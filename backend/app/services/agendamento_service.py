from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.models.hotel import Hospedagem
from app.models.cliente import Pet
from sqlalchemy import func
from uuid import UUID
from fastapi import HTTPException
from typing import List, Dict

from app.models.agendamento import Agendamento
from app.models.schedule_block import ScheduleBlock
from app.models.service import Service
from app.models.hotel import Hospedagem
from app.schemas.agendamento import AgendamentoCreate, AgendamentoUpdate


def listar(
    db: Session,
    store_id: UUID,
    data: date = None,
    start_date: date = None,
    end_date: date = None,
    skip: int = 0,
    limit: int = 50
):
    from sqlalchemy.orm import joinedload
    
    q = db.query(Agendamento).options(joinedload(Agendamento.pet)).filter(Agendamento.store_id == store_id)
    if data:
        q = q.filter(Agendamento.date == data)
    if start_date:
        q = q.filter(Agendamento.date >= start_date)
    if end_date:
        q = q.filter(Agendamento.date <= end_date)
    return q.order_by(Agendamento.date, Agendamento.time).offset(skip).limit(limit).all()


def listar_unificado(
    db: Session,
    store_id: UUID,
    start_date: date,
    end_date: date
):
    """Retorna agendamentos e hospedagens unificados para a agenda"""
    from sqlalchemy.orm import joinedload
    
    # 1. Agendamentos Padrão (Agora com Eager Loading para evitar N+1 queries)
    agendamentos = db.query(Agendamento).options(joinedload(Agendamento.pet)).filter(
        Agendamento.store_id == store_id,
        Agendamento.date >= start_date,
        Agendamento.date <= end_date
    ).all()
    
    # 2. Hospedagens (Hotel/Creche) (Também com Eager Loading)
    # Mostramos a entrada (check-in) e a saída (check-out) como eventos na agenda
    hospedagens = db.query(Hospedagem).options(joinedload(Hospedagem.pet)).filter(
        Hospedagem.store_id == store_id,
        ((func.date(Hospedagem.check_in_previsto) >= start_date) & (func.date(Hospedagem.check_in_previsto) <= end_date)) |
        ((func.date(Hospedagem.check_out_previsto) >= start_date) & (func.date(Hospedagem.check_out_previsto) <= end_date))
    ).all()
    
    resultado = []
    
    for ag in agendamentos:
        resultado.append({
            "id": str(ag.id),
            "pet_id": str(ag.pet_id) if ag.pet_id else None,
            "pet_name": ag.pet.name if ag.pet else ("Objeto" if ag.pet_id is None else "N/A"),
            "service": ag.service_legacy or "Serviço",
            "date": ag.date.isoformat(),
            "time": ag.time,
            "status": ag.status,
            "price": str(ag.price or 0),
            "type": "service"
        })
        
    for h in hospedagens:
        # Evento de Check-in
        if start_date <= h.check_in_previsto.date() <= end_date:
            resultado.append({
                "id": f"hotel-in-{h.id}",
                "pet_id": str(h.pet_id),
                "pet_name": h.pet.name if h.pet else "Hóspede",
                "service": "Check-in Hotel",
                "date": h.check_in_previsto.date().isoformat(),
                "time": h.check_in_previsto.strftime("%H:%M"),
                "status": "scheduled" if h.status == 'planned' else "done",
                "price": str(h.valor_total),
                "type": "hotel"
            })
        
        # Evento de Check-out
        if start_date <= h.check_out_previsto.date() <= end_date:
            resultado.append({
                "id": f"hotel-out-{h.id}",
                "pet_id": str(h.pet_id),
                "pet_name": h.pet.name if h.pet else "Hóspede",
                "service": "Check-out Hotel",
                "date": h.check_out_previsto.date().isoformat(),
                "time": h.check_out_previsto.strftime("%H:%M"),
                "status": "scheduled",
                "price": "0",
                "type": "hotel"
            })
            
    return resultado


def estimar_duracao_servico(
    service_type: str,
    breed: str = None,
    weight: str = None
) -> int:
    """
    Estima o tempo em minutos para um serviço baseado na realidade brasileira.
    Considera porte (peso) e raça (tipo de pelo).
    """
    # Tempo base por serviço
    base_times = {
        "banho": 40,
        "tosa": 60,
        "banho_tosa": 90,
        "consulta": 30,
        "vacina": 15
    }
    
    tempo = base_times.get(service_type.lower(), 45)
    
    # Ajuste por porte (Peso)
    if weight:
        w = float(weight.replace("kg", "").replace(",", ".").strip())
        if w > 25: # Grande
            tempo += 40
        elif w > 12: # Médio
            tempo += 20
        elif w > 7: # Pequeno (padrão)
            tempo += 0
        else: # Mini
            tempo -= 10
            
    # Ajuste por Raça (Complexidade de Pelo)
    heavy_coats = ["golden", "chow", "husky", "akita", "bernese", "border"]
    medium_coats = ["poodle", "shih", "lhasa", "maltes", "yorkshire"]
    
    breed_lower = (breed or "").lower()
    
    if any(r in breed_lower for r in heavy_coats):
        tempo += 30 # Muito pelo / Subpelo
    elif any(r in breed_lower for r in medium_coats):
        tempo += 15 # Pelo longo
        
    return max(tempo, 15) # Mínimo de 15 min


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
        ag_start_dt = datetime.combine(date, datetime.strptime(ag.time, "%H:%M").time())
        ag_service = db.query(Service).filter(Service.id == ag.service_id).first()
        ag_end_dt = ag_start_dt + timedelta(minutes=ag_service.duration if ag_service else 0)
        
        if not (ends_at <= ag_start_dt or scheduled_at >= ag_end_dt):
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
