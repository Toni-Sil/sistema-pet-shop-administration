import logging
from datetime import date
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.models.store import Store
from app.schemas.agendamento import AgendamentoCreate, AgendamentoUpdate, AgendamentoResponse
from app.services import agendamento_service
from app.services.whatsapp_service import whatsapp_service
from app.services import fiscal_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agendamentos", tags=["Agendamentos"])


async def _auto_emitir_nfse(db: Session, appointment_id: UUID, store_id: UUID):
    """
    Emite NFS-e automaticamente ao marcar um serviço como 'done'.
    Silencioso quando chave PlugNotas não está configurada.
    """
    try:
        store = db.query(Store).filter(Store.id == store_id).first()
        api_key = fiscal_service._get_plugnotas_key(store) if store else None
        if not api_key:
            return
        await fiscal_service.emitir_nfse(db, appointment_id, store_id)
    except Exception as exc:
        logger.warning(f"[Auto NFS-e] Falha para agendamento {appointment_id}: {exc}")


@router.get("/unified")
def listar_unificado(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    """Retorna visão unificada de agendamentos e hospedagens"""
    return agendamento_service.listar_unificado(db, store_id, start_date, end_date)


@router.get("/estimate-duration")
def estimate_duration(
    service_type: str,
    pet_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
    current_user: User = Depends(get_any_role)
):
    """Retorna o tempo estimado em minutos para o serviço"""
    from app.models.cliente import Pet
    breed, weight = None, None
    if pet_id:
        pet = db.query(Pet).filter(Pet.id == pet_id, Pet.store_id == store_id).first()
        if pet:
            breed, weight = pet.breed, pet.weight
            
    minutes = agendamento_service.estimar_duracao_servico(service_type, breed, weight)
    return {"minutes": minutes}


@router.get("", response_model=List[AgendamentoResponse])
def listar(
    data: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    return agendamento_service.listar(db, store_id, data, start_date, end_date, skip, limit)


@router.post("", response_model=AgendamentoResponse, status_code=201)
def criar(
    dados: AgendamentoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    ag = agendamento_service.criar(db, dados, store_id, current_user.id)

    # Notificação WhatsApp em 2º plano
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

    # Notificação de mudança de status
    if dados.status in ["confirmed", "cancelled"] and ag.pet and ag.pet.client:
        background_tasks.add_task(
            whatsapp_service.notify_status_change,
            db, store_id, ag.pet.client.name, ag.pet.name, dados.status, ag.pet.client.phone
        )

    # Emissão automática de NFS-e quando serviço concluído
    if dados.status == "done":
        background_tasks.add_task(_auto_emitir_nfse, db, id, store_id)

    return ag


@router.get("/hoje/count")
def contar_hoje(db: Session = Depends(get_db), current_user: User = Depends(get_any_role), store_id: UUID = Depends(get_current_store_id)):
    return {"count": agendamento_service.contar_hoje(db, store_id)}

