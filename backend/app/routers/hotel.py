from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from datetime import datetime

from app.database import get_db
from app.core.deps import get_current_store_id
from app.models.hotel import Quarto, Hospedagem, QuartoStatus, HospedagemStatus
from app.schemas.hotel import QuartoCreate, QuartoResponse, HospedagemCreate, HospedagemResponse

router = APIRouter(prefix="/hotel", tags=["Hotel e Creche"])

# --- Quartos ---

@router.get("/quartos", response_model=List[QuartoResponse])
def list_quartos(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    return db.query(Quarto).filter(Quarto.store_id == store_id).all()

@router.post("/quartos", response_model=QuartoResponse)
def create_quarto(
    quarto_in: QuartoCreate,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    db_quarto = Quarto(**quarto_in.model_dump(), store_id=store_id)
    db.add(db_quarto)
    db.commit()
    db.refresh(db_quarto)
    return db_quarto

# --- Hospedagens ---

@router.get("/hospedagens", response_model=List[HospedagemResponse])
def list_hospedagens(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    return db.query(Hospedagem).filter(Hospedagem.store_id == store_id).all()

@router.post("/hospedagens", response_model=HospedagemResponse)
def create_hospedagem(
    hospedagem_in: HospedagemCreate,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    # Verifica se o quarto existe
    quarto = db.query(Quarto).filter(Quarto.id == hospedagem_in.quarto_id, Quarto.store_id == store_id).first()
    if not quarto:
        raise HTTPException(404, "Quarto não encontrado")
    
    # Calcula valor total preliminar
    days = (hospedagem_in.check_out_previsto - hospedagem_in.check_in_previsto).days
    if days < 1: days = 1
    total = float(quarto.preco_diaria) * days

    db_hospedagem = Hospedagem(
        **hospedagem_in.model_dump(),
        store_id=store_id,
        valor_diaria=quarto.preco_diaria,
        valor_total=total,
        status=HospedagemStatus.PLANNED
    )
    db.add(db_hospedagem)
    db.commit()
    db.refresh(db_hospedagem)
    return db_hospedagem

from app.schemas.hotel import HospedagemUpdate

@router.patch("/hospedagens/{id}", response_model=HospedagemResponse)
def update_hospedagem(
    id: UUID,
    hospedagem_in: HospedagemUpdate,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    hosp = db.query(Hospedagem).filter(Hospedagem.id == id, Hospedagem.store_id == store_id).first()
    if not hosp:
        raise HTTPException(404, "Hospedagem não encontrada")
        
    update_data = hospedagem_in.model_dump(exclude_unset=True)
    
    if "quarto_id" in update_data:
        quarto = db.query(Quarto).filter(Quarto.id == update_data["quarto_id"], Quarto.store_id == store_id).first()
        if not quarto:
            raise HTTPException(404, "Quarto não encontrado")
            
    for field, value in update_data.items():
        setattr(hosp, field, value)
        
    # Recalcula valor total se as datas mudaram
    if "check_in_previsto" in update_data or "check_out_previsto" in update_data:
        days = (hosp.check_out_previsto - hosp.check_in_previsto).days
        if days < 1: days = 1
        hosp.valor_total = float(hosp.valor_diaria) * days
        
    db.commit()
    db.refresh(hosp)
    return hosp

@router.post("/hospedagens/{id}/check-in", response_model=HospedagemResponse)
def check_in(
    id: UUID,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    hosp = db.query(Hospedagem).filter(Hospedagem.id == id, Hospedagem.store_id == store_id).first()
    if not hosp:
        raise HTTPException(404, "Hospedagem não encontrada")
    
    hosp.status = HospedagemStatus.CHECKED_IN
    hosp.check_in_real = datetime.utcnow()
    
    # Atualiza status do quarto
    quarto = db.query(Quarto).filter(Quarto.id == hosp.quarto_id).first()
    if quarto:
        quarto.status = QuartoStatus.OCCUPIED
        
    db.commit()
    db.refresh(hosp)
    return hosp

@router.post("/hospedagens/{id}/check-out", response_model=HospedagemResponse)
def check_out(
    id: UUID,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    hosp = db.query(Hospedagem).filter(Hospedagem.id == id, Hospedagem.store_id == store_id).first()
    if not hosp:
        raise HTTPException(404, "Hospedagem não encontrada")
    
    hosp.status = HospedagemStatus.CHECKED_OUT
    hosp.check_out_real = datetime.utcnow()
    
    # Atualiza status do quarto para limpeza
    quarto = db.query(Quarto).filter(Quarto.id == hosp.quarto_id).first()
    if quarto:
        quarto.status = QuartoStatus.CLEANING
        
    db.commit()
    db.refresh(hosp)
    return hosp
