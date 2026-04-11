from datetime import date
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.schemas.agendamento import AgendamentoCreate, AgendamentoUpdate, AgendamentoResponse
from app.services import agendamento_service
from app.services.whatsapp_service import whatsapp_service

router = APIRouter(prefix="/agendamentos", tags=["Agendamentos"])


@router.get("", response_model=List[AgendamentoResponse])
def listar(
    data: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    return agendamento_service.listar(db, store_id, data, skip, limit)


@router.post("", response_model=AgendamentoResponse, status_code=201)
def criar(
    dados: AgendamentoCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_any_role), 
    store_id: UUID = Depends(get_current_store_id)
):
    ag = agendamento_service.criar(db, dados, store_id, current_user.id)
    
    # Notificação em 2º plano
    if ag.pet and ag.pet.client:
        background_tasks.add_task(
            whatsapp_service.notify_appointment_created,
            db, store_id, ag.pet.client.name, ag.pet.name, 
            ag.service_legacy or "Serviço", str(ag.date), ag.time, ag.pet.client.phone
        )
    return ag


@router.patch("/{id}", response_model=AgendamentoResponse)
def atualizar(
    id: UUID, 
    dados: AgendamentoUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_any_role), 
    store_id: UUID = Depends(get_current_store_id)
):
    ag = agendamento_service.atualizar_status(db, id, dados, store_id)
    
    # Notificação de mudança de status (ex: confirmado)
    if dados.status in ["confirmed", "cancelled"] and ag.pet and ag.pet.client:
        background_tasks.add_task(
            whatsapp_service.notify_status_change,
            db, store_id, ag.pet.client.name, ag.pet.name, dados.status, ag.pet.client.phone
        )
    return ag


@router.get("/hoje/count")
def contar_hoje(db: Session = Depends(get_db), current_user: User = Depends(get_any_role), store_id: UUID = Depends(get_current_store_id)):
    return {"count": agendamento_service.contar_hoje(db, store_id)}
