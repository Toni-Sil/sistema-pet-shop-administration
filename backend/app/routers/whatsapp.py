from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.models.whatsapp_log import WhatsAppLog

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
