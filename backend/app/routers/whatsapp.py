from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.models.whatsapp_log import WhatsAppLog
from app.models.cliente import Pet
from app.services.whatsapp_service import whatsapp_service

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Simulação"])

@router.get("/logs")
def list_logs(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
    current_user: User = Depends(get_any_role)
):
    return db.query(WhatsAppLog).filter(
        WhatsAppLog.store_id == store_id
    ).order_by(WhatsAppLog.created_at.desc()).limit(50).all()

@router.post("/status-update")
async def send_live_status(
    pet_id: UUID,
    status_type: str,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
    current_user: User = Depends(get_any_role)
):
    """Envia um status em tempo real para o tutor"""
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.store_id == store_id).first()
    if not pet or not pet.client or not pet.client.phone:
        return {"error": "Pet ou Telefone não encontrado"}
        
    return await whatsapp_service.send_status_update(db, store_id, pet.client.phone, pet.name, status_type)
