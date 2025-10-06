from fastapi import APIRouter, HTTPException, status, Query, Depends, UploadFile, File
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import hashlib
import uuid
from pathlib import Path

from app.schemas.attachment import AttachmentCreate, AttachmentUpdate, AttachmentResponse
from app.models.attachment import Attachment
from app.models.message import Message
from app.models.room_participant import RoomParticipant
from app.models.user import User
from app.database import get_db
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/attachments",
    tags=["attachments"]
)

# Configuración de archivos
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Tipos de archivo permitidos
ALLOWED_MIME_TYPES = {
    # Imágenes
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    # Documentos
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


def get_file_type_category(content_type: str) -> str:
    """Determinar categoría del archivo (image o document)"""
    if content_type.startswith("image/"):
        return "image"
    return "document"


def generate_hashed_filename(original_filename: str, content: bytes) -> str:
    """Generar nombre único usando hash del contenido + UUID"""
    extension = Path(original_filename).suffix.lower()
    file_hash = hashlib.sha256(content).hexdigest()[:16]
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"{timestamp}_{file_hash}_{unique_id}{extension}"


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Subir un archivo al servidor (requiere JWT)

    - **file**: Archivo a subir (imágenes: jpg, png, gif, webp | documentos: pdf, doc, docx)
    - Tamaño máximo: 10MB

    Retorna información del archivo incluyendo file_url para usar en mensajes
    """
    # Validar tipo MIME
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: images (jpg, png, gif, webp) and documents (pdf, doc, docx)"
        )

    # Leer contenido del archivo
    contents = await file.read()

    # Validar tamaño
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    # Generar nombre hasheado único
    hashed_filename = generate_hashed_filename(file.filename or "file", contents)
    file_path = UPLOAD_DIR / hashed_filename

    # Guardar archivo en el servidor
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )

    # Determinar categoría del archivo
    file_type = get_file_type_category(file.content_type)

    # Construir URL del archivo (será servida por FastAPI static files)
    file_url = f"/uploads/{hashed_filename}"

    return {
        "file_url": file_url,
        "file_name": file.filename,
        "file_type": file_type,
        "file_size": len(contents)
    }


@router.post("/", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def create_attachment(
    attachment_data: AttachmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo adjunto (requiere JWT)

    Solo el autor del mensaje puede agregar adjuntos
    """
    # Validar que el mensaje existe
    message = db.query(Message).filter(Message.id == attachment_data.message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Validar que el usuario es el autor del mensaje
    if message.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add attachments to your own messages"
        )

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener adjuntos con filtros opcionales (requiere JWT)

    - **message_id**: Filtrar por mensaje específico
    - **file_type**: Filtrar por tipo de archivo

    Si se filtra por message_id, se valida que el usuario sea participante de la sala
    """
    # Si se filtra por message_id, validar acceso
    if message_id is not None:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        # Validar que el usuario es participante de la sala del mensaje
        is_participant = db.query(RoomParticipant).filter(
            RoomParticipant.room_id == message.room_id,
            RoomParticipant.user_id == current_user.id
        ).first()

        if not is_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant of this chat room"
            )

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
async def get_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener un adjunto por ID (requiere JWT)

    Se valida que el usuario sea participante de la sala del mensaje
    """
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )

    # Obtener el mensaje asociado
    message = db.query(Message).filter(Message.id == attachment.message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Validar que el usuario es participante de la sala del mensaje
    is_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == message.room_id,
        RoomParticipant.user_id == current_user.id
    ).first()

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room"
        )

    return attachment

@router.put("/{attachment_id}", response_model=AttachmentResponse)
async def update_attachment(
    attachment_id: int,
    attachment_data: AttachmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar información de un adjunto (requiere JWT)

    Solo el autor del mensaje puede actualizar sus adjuntos
    """
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )

    # Obtener el mensaje asociado
    message = db.query(Message).filter(Message.id == attachment.message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Validar que el usuario es el autor del mensaje
    if message.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update attachments of your own messages"
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
async def delete_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar un adjunto (requiere JWT)

    Solo el autor del mensaje puede eliminar sus adjuntos
    """
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )

    # Obtener el mensaje asociado
    message = db.query(Message).filter(Message.id == attachment.message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Validar que el usuario es el autor del mensaje
    if message.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete attachments of your own messages"
        )

    db.delete(attachment)
    db.commit()

@router.get("/message/{message_id}/all", response_model=List[AttachmentResponse])
async def get_message_attachments(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los adjuntos de un mensaje específico (requiere JWT)

    Se valida que el usuario sea participante de la sala del mensaje
    """
    # Obtener el mensaje
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Validar que el usuario es participante de la sala del mensaje
    is_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == message.room_id,
        RoomParticipant.user_id == current_user.id
    ).first()

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room"
        )

    attachments = db.query(Attachment).filter(
        Attachment.message_id == message_id
    ).order_by(Attachment.uploaded_at).all()

    return attachments

@router.get("/message/{message_id}/count", response_model=dict)
async def count_message_attachments(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Contar los adjuntos de un mensaje (requiere JWT)

    Se valida que el usuario sea participante de la sala del mensaje
    """
    # Obtener el mensaje
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    # Validar que el usuario es participante de la sala del mensaje
    is_participant = db.query(RoomParticipant).filter(
        RoomParticipant.room_id == message.room_id,
        RoomParticipant.user_id == current_user.id
    ).first()

    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room"
        )

    count = db.query(Attachment).filter(Attachment.message_id == message_id).count()
    return {"message_id": message_id, "attachment_count": count}

@router.get("/stats/by-type", response_model=dict)
async def get_attachments_stats_by_type(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas de adjuntos por tipo (requiere JWT)

    Muestra estadísticas globales del sistema
    """
    # Obtener total de attachments
    total = db.query(Attachment).count()

    # Agrupar por tipo y contar
    stats_query = db.query(
        func.lower(Attachment.file_type).label('file_type'),
        func.count(Attachment.id).label('count')
    ).group_by(func.lower(Attachment.file_type)).all()

    stats = {row.file_type: row.count for row in stats_query}

    return {"total_attachments": total, "by_type": stats}
