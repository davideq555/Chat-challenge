from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.schemas.attachment import AttachmentCreate, AttachmentUpdate, AttachmentResponse
from app.models.attachment import Attachment
from app.database import get_db

router = APIRouter(
    prefix="/attachments",
    tags=["attachments"]
)

@router.post("/", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def create_attachment(attachment_data: AttachmentCreate, db: Session = Depends(get_db)):
    """Crear un nuevo adjunto"""
    # TODO: Validar que message_id exista

    attachment = Attachment(
        message_id=attachment_data.message_id,
        file_url=attachment_data.file_url,
        file_type=attachment_data.file_type
    )

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment

@router.get("/", response_model=List[AttachmentResponse])
async def get_attachments(
    message_id: int = Query(None, description="Filtrar por mensaje"),
    file_type: str = Query(None, description="Filtrar por tipo de archivo"),
    db: Session = Depends(get_db)
):
    """
    Obtener adjuntos con filtros opcionales

    - **message_id**: Filtrar por mensaje específico
    - **file_type**: Filtrar por tipo de archivo
    """
    query = db.query(Attachment)

    # Aplicar filtros
    if message_id is not None:
        query = query.filter(Attachment.message_id == message_id)

    if file_type is not None:
        query = query.filter(func.lower(Attachment.file_type) == file_type.lower())

    # Ordenar por fecha de subida (más recientes primero)
    query = query.order_by(Attachment.uploaded_at.desc())

    return query.all()

@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(attachment_id: int, db: Session = Depends(get_db)):
    """Obtener un adjunto por ID"""
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    return attachment

@router.put("/{attachment_id}", response_model=AttachmentResponse)
async def update_attachment(attachment_id: int, attachment_data: AttachmentUpdate, db: Session = Depends(get_db)):
    """Actualizar información de un adjunto"""
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
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

    db.commit()
    db.refresh(attachment)

    return attachment

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(attachment_id: int, db: Session = Depends(get_db)):
    """Eliminar un adjunto"""
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    db.delete(attachment)
    db.commit()

@router.get("/message/{message_id}/all", response_model=List[AttachmentResponse])
async def get_message_attachments(message_id: int, db: Session = Depends(get_db)):
    """Obtener todos los adjuntos de un mensaje específico"""
    attachments = db.query(Attachment).filter(
        Attachment.message_id == message_id
    ).order_by(Attachment.uploaded_at).all()

    return attachments

@router.get("/message/{message_id}/count", response_model=dict)
async def count_message_attachments(message_id: int, db: Session = Depends(get_db)):
    """Contar los adjuntos de un mensaje"""
    count = db.query(Attachment).filter(Attachment.message_id == message_id).count()
    return {"message_id": message_id, "attachment_count": count}

@router.get("/stats/by-type", response_model=dict)
async def get_attachments_stats_by_type(db: Session = Depends(get_db)):
    """Obtener estadísticas de adjuntos por tipo"""
    # Obtener total de attachments
    total = db.query(Attachment).count()

    # Agrupar por tipo y contar
    stats_query = db.query(
        func.lower(Attachment.file_type).label('file_type'),
        func.count(Attachment.id).label('count')
    ).group_by(func.lower(Attachment.file_type)).all()

    stats = {row.file_type: row.count for row in stats_query}

    return {"total_attachments": total, "by_type": stats}
