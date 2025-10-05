from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse, ContactWithUser
from app.schemas.user import UserResponse
from app.models.contact import Contact
from app.models.user import User
from app.database import get_db
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/contacts",
    tags=["contacts"]
)

@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def send_contact_request(
    contact_data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enviar solicitud de contacto (requiere JWT)

    - Si el usuario es público, se acepta automáticamente (status='accepted')
    - Si el usuario es privado, queda pendiente (status='pending')
    - No se puede agregar a uno mismo como contacto
    """
    # Validar que no se agregue a sí mismo
    if contact_data.contact_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add yourself as a contact"
        )

    # Verificar que el usuario contacto existe
    contact_user = db.query(User).filter(User.id == contact_data.contact_id).first()
    if not contact_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verificar si ya existe una relación de contacto
    existing_contact = db.query(Contact).filter(
        or_(
            and_(Contact.user_id == current_user.id, Contact.contact_id == contact_data.contact_id),
            and_(Contact.user_id == contact_data.contact_id, Contact.contact_id == current_user.id)
        )
    ).first()

    if existing_contact:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact relationship already exists"
        )

    # Determinar el estado según si el usuario es público
    initial_status = "accepted" if contact_user.is_public else "pending"

    # Crear el contacto
    new_contact = Contact(
        user_id=current_user.id,
        contact_id=contact_data.contact_id,
        status=initial_status
    )

    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)

    # Si se acepta automáticamente, crear la relación inversa
    if initial_status == "accepted":
        reverse_contact = Contact(
            user_id=contact_data.contact_id,
            contact_id=current_user.id,
            status="accepted"
        )
        db.add(reverse_contact)
        db.commit()

    return new_contact

@router.get("/my-contacts", response_model=List[ContactWithUser])
async def get_my_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener todos mis contactos aceptados (requiere JWT)

    Retorna solo contactos con status='accepted'
    """
    contacts = db.query(Contact).filter(
        Contact.user_id == current_user.id,
        Contact.status == "accepted"
    ).all()

    # Enriquecer con información del usuario
    result = []
    for contact in contacts:
        contact_user = db.query(User).filter(User.id == contact.contact_id).first()
        if contact_user:
            contact_dict = contact.to_dict()
            contact_dict['contact'] = contact_user
            result.append(contact_dict)

    return result

@router.get("/pending", response_model=List[ContactWithUser])
async def get_pending_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener solicitudes de contacto pendientes (requiere JWT)

    Retorna solicitudes recibidas con status='pending'
    """
    # Solicitudes donde YO soy el contacto (contact_id) y están pendientes
    pending_requests = db.query(Contact).filter(
        Contact.contact_id == current_user.id,
        Contact.status == "pending"
    ).all()

    # Enriquecer con información del usuario que envió la solicitud
    result = []
    for contact in pending_requests:
        requester_user = db.query(User).filter(User.id == contact.user_id).first()
        if requester_user:
            contact_dict = contact.to_dict()
            contact_dict['contact'] = requester_user
            result.append(contact_dict)

    return result

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact_status(
    contact_id: int,
    contact_update: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar estado de contacto: aceptar, rechazar o bloquear (requiere JWT)

    - **accepted**: Acepta la solicitud y crea la relación bidireccional
    - **blocked**: Bloquea al usuario
    - Solo el receptor de la solicitud puede aceptar/rechazar
    """
    # Buscar el contacto
    contact = db.query(Contact).filter(Contact.id == contact_id).first()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    # Verificar que el usuario actual es el receptor de la solicitud
    if contact.contact_id != current_user.id and contact.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this contact"
        )

    # Actualizar el estado
    contact.status = contact_update.status

    # Si se acepta, crear la relación inversa
    if contact_update.status == "accepted":
        # Verificar si ya existe la relación inversa
        reverse_contact = db.query(Contact).filter(
            Contact.user_id == contact.contact_id,
            Contact.contact_id == contact.user_id
        ).first()

        if not reverse_contact:
            reverse_contact = Contact(
                user_id=contact.contact_id,
                contact_id=contact.user_id,
                status="accepted"
            )
            db.add(reverse_contact)
        else:
            reverse_contact.status = "accepted"

    db.commit()
    db.refresh(contact)

    return contact

@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar un contacto (requiere JWT)

    Elimina la relación de contacto bidireccional
    """
    # Buscar el contacto
    contact = db.query(Contact).filter(Contact.id == contact_id).first()

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )

    # Verificar que el usuario actual es parte de la relación
    if contact.user_id != current_user.id and contact.contact_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this contact"
        )

    # Eliminar la relación inversa también
    reverse_contact = db.query(Contact).filter(
        Contact.user_id == contact.contact_id,
        Contact.contact_id == contact.user_id
    ).first()

    if reverse_contact:
        db.delete(reverse_contact)

    db.delete(contact)
    db.commit()

@router.get("/search-public-users", response_model=List[UserResponse])
async def search_public_users(
    query: str = Query(..., min_length=1, description="Search query (username or email)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Buscar usuarios públicos para agregar como contactos (requiere JWT)

    - Solo retorna usuarios con is_public=True
    - No incluye al usuario actual
    - No incluye usuarios que ya son contactos
    """
    # Buscar usuarios públicos que coincidan con la búsqueda
    public_users = db.query(User).filter(
        User.is_public == True,
        User.id != current_user.id,
        or_(
            User.username.ilike(f"%{query}%"),
            User.email.ilike(f"%{query}%")
        )
    ).limit(20).all()

    # Filtrar usuarios que ya son contactos
    my_contact_ids = [c.contact_id for c in db.query(Contact).filter(
        Contact.user_id == current_user.id
    ).all()]

    filtered_users = [user for user in public_users if user.id not in my_contact_ids]

    return filtered_users
