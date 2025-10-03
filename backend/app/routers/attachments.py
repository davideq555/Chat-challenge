from fastapi import APIRouter, HTTPException, status, Query
from typing import List
from datetime import datetime

from app.schemas.attachment import AttachmentCreate, AttachmentUpdate, AttachmentResponse
from app.models.attachment import Attachment

router = APIRouter(
    prefix="/attachments",
    tags=["attachments"]
)

# Almacenamiento temporal en memoria (luego se reemplazará con base de datos)
attachments_db = {}
attachment_id_counter = 1

@router.post("/", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def create_attachment(attachment_data: AttachmentCreate):
    """Crear un nuevo adjunto"""
    global attachment_id_counter

    # TODO: Validar que message_id exista (cuando tengamos BD)

    # Crear adjunto
    attachment = Attachment(
        id=attachment_id_counter,
        message_id=attachment_data.message_id,
        file_url=attachment_data.file_url,
        file_type=attachment_data.file_type,
        uploaded_at=datetime.now()
    )

    attachments_db[attachment_id_counter] = attachment
    attachment_id_counter += 1

    return attachment.to_dict()

@router.get("/", response_model=List[AttachmentResponse])
async def get_attachments(
    message_id: int = Query(None, description="Filtrar por mensaje"),
    file_type: str = Query(None, description="Filtrar por tipo de archivo")
):
    """
    Obtener adjuntos con filtros opcionales

    - **message_id**: Filtrar por mensaje específico
    - **file_type**: Filtrar por tipo de archivo
    """
    attachments = list(attachments_db.values())

    # Aplicar filtros
    if message_id is not None:
        attachments = [att for att in attachments if att.message_id == message_id]

    if file_type is not None:
        attachments = [att for att in attachments if att.file_type.lower() == file_type.lower()]

    # Ordenar por fecha de subida (más recientes primero)
    attachments.sort(key=lambda x: x.uploaded_at, reverse=True)

    return [att.to_dict() for att in attachments]

@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(attachment_id: int):
    """Obtener un adjunto por ID"""
    attachment = attachments_db.get(attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    return attachment.to_dict()

@router.put("/{attachment_id}", response_model=AttachmentResponse)
async def update_attachment(attachment_id: int, attachment_data: AttachmentUpdate):
    """Actualizar información de un adjunto"""
    attachment = attachments_db.get(attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )

    # Actualizar campos si se proporcionan
    if attachment_data.file_url is not None:
        attachment.file_url = attachment_data.file_url

    if attachment_data.file_type is not None:
        attachment.file_type = attachment_data.file_type

    return attachment.to_dict()

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(attachment_id: int):
    """Eliminar un adjunto"""
    if attachment_id not in attachments_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    del attachments_db[attachment_id]

@router.get("/message/{message_id}/all", response_model=List[AttachmentResponse])
async def get_message_attachments(message_id: int):
    """Obtener todos los adjuntos de un mensaje específico"""
    attachments = [
        att for att in attachments_db.values()
        if att.message_id == message_id
    ]

    # Ordenar por fecha de subida
    attachments.sort(key=lambda x: x.uploaded_at)

    return [att.to_dict() for att in attachments]

@router.get("/message/{message_id}/count", response_model=dict)
async def count_message_attachments(message_id: int):
    """Contar los adjuntos de un mensaje"""
    count = sum(1 for att in attachments_db.values() if att.message_id == message_id)
    return {"message_id": message_id, "attachment_count": count}

@router.get("/stats/by-type", response_model=dict)
async def get_attachments_stats_by_type():
    """Obtener estadísticas de adjuntos por tipo"""
    stats = {}
    for att in attachments_db.values():
        file_type = att.file_type.lower()
        stats[file_type] = stats.get(file_type, 0) + 1

    return {"total_attachments": len(attachments_db), "by_type": stats}
