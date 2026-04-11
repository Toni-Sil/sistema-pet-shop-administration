from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException
from typing import List, Dict

from app.models.agendamento import Agendamento
from app.models.schedule_block import ScheduleBlock
from app.models.service import Service
from app.schemas.agendamento import AgendamentoCreate, AgendamentoUpdate


def listar(db: Session, store_id: UUID, data: date = None, skip: int = 0, limit: int = 50):
    q = db.query(Agendamento).filter(Agendamento.store_id == store_id)
    if data:
        q = q.filter(Agendamento.date == data)
    return q.order_by(Agendamento.date, Agendamento.time).offset(skip).limit(limit).all()


def verificar_conflito(
    db: Session,
    store_id: UUID,
    service_id: UUID,
    date: date,
    time: str,
    exclude_id: UUID = None
) -> Dict:
    """Verifica se há conflito de horário para um agendamento"""
    service = db.query(Service).filter(Service.id == service_id, Service.store_id == store_id).first()
    if not service:
        raise HTTPException(404, "Serviço não encontrado")
    
    scheduled_at = datetime.combine(date, datetime.strptime(time, "%H:%M").time())
    ends_at = scheduled_at + timedelta(minutes=service.duration)
    
    existe_agendamento = db.query(Agendamento).filter(
        Agendamento.store_id == store_id,
        Agendamento.date == date,
        Agendamento.status.in_(['scheduled', 'in_progress']),
        Agendamento.id != exclude_id if exclude_id else True
    ).all()
    
    for ag in existe_agendamento:
        ag_start = datetime.strptime(ag.time, "%H:%M").time()
        ag_service = db.query(Service).filter(Service.id == ag.service_id).first()
        ag_end = ag_start + timedelta(minutes=ag_service.duration if ag_service else 0)
        
        if not (ends_at.time() <= ag_start or scheduled_at.time() >= ag_end.time()):
            return {
                "has_conflict": True,
                "existing_appointment": {
                    "id": str(ag.id),
                    "time": ag.time,
                    "service": ag_service.name if ag_service else ag.service_legacy
                }
            }
    
    bloqueado = db.query(ScheduleBlock).filter(
        ScheduleBlock.store_id == store_id,
        ScheduleBlock.starts_at <= scheduled_at,
        ScheduleBlock.ends_at >= ends_at
    ).first()
    
    if bloqueado:
        return {
            "has_conflict": True,
            "blocked": True,
            "reason": bloqueado.reason
        }
    
    return {"has_conflict": False}


def checar_horarios_disponiveis(
    db: Session,
    store_id: UUID,
    service_id: UUID,
    date: date
) -> List[str]:
    """Retorna lista de horários disponíveis para uma data"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        return []
    
    inicio_hora = 8
    fim_hora = 19
    
    horarios = []
    for hora in range(inicio_hora, fim_hora + 1):
        for minuto in [0, 30]:
            time_str = f"{hora:02d}:{minuto:02d}"
            resultado = verificar_conflito(db, store_id, service_id, date, time_str)
            if not resultado.get("has_conflict"):
                horarios.append(time_str)
    
    return horarios


def criar(db: Session, dados: AgendamentoCreate, store_id: UUID, user_id: UUID):
    dados_dict = dados.model_dump()
    date = dados_dict.get('date')
    time = dados_dict.get('time')
    service_id = dados_dict.get('service_id')
    
    if date and time and service_id:
        conflito = verificar_conflito(db, store_id, service_id, date, time)
        if conflito.get("has_conflict"):
            raise HTTPException(400, f"Horário conflitante: {conflito.get('existing_appointment', {}).get('service', 'bloqueado')}")
    
    ag = Agendamento(**dados_dict, store_id=store_id, user_id=user_id)
    db.add(ag)
    db.commit()
    db.refresh(ag)
    return ag


def atualizar_status(db: Session, id: UUID, dados: AgendamentoUpdate, store_id: UUID):
    ag = db.query(Agendamento).filter(Agendamento.id == id, Agendamento.store_id == store_id).first()
    if not ag:
        raise HTTPException(404, "Agendamento não encontrado")
    for k, v in dados.model_dump(exclude_unset=True).items():
        setattr(ag, k, v)
    db.commit()
    db.refresh(ag)
    return ag


def contar_hoje(db: Session, store_id: UUID) -> int:
    return db.query(Agendamento).filter(
        Agendamento.store_id == store_id,
        Agendamento.date == date.today()
    ).count()
