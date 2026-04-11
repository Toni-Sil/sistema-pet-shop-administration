from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from typing import List

from app.database import get_db
from app.models.store import Store
from app.models.service import Service
from app.models.agendamento import Agendamento
from app.schemas.agendamento import AgendamentoCreate, AgendamentoResponse
from app.services.whatsapp_service import whatsapp_service

router = APIRouter(prefix="/public", tags=["Agendamento Público"])

@router.get("/{slug}/services")
def get_public_services(slug: str, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.slug == slug, Store.is_active == True).first()
    if not store:
        raise HTTPException(404, "Loja não encontrada")
    
    return db.query(Service).filter(Service.store_id == store.id, Service.is_active == True).all()

@router.post("/{slug}/book")
def public_book(
    slug: str, 
    appointment: AgendamentoCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    store = db.query(Store).filter(Store.slug == slug, Store.is_active == True).first()
    if not store:
        raise HTTPException(404, "Loja não encontrada")
    
    db_obj = Agendamento(
        **appointment.model_dump(),
        store_id=store.id,
        status="pending"
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # Extrair telefone do notes (mocked format "Pet: X | Tel: Y")
    phone = "5500000000000"
    if appointment.notes and "Tel: " in appointment.notes:
        phone = appointment.notes.split("Tel: ")[-1].strip()
    
    background_tasks.add_task(
        whatsapp_service.notify_appointment_created,
        db, store.id, "Cliente", "Pet", 
        appointment.service or "Serviço", str(appointment.date), appointment.time, phone
    )
    
    return {"message": "Agendamento solicitado com sucesso! Aguarde confirmação.", "id": db_obj.id}
