from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.models.financeiro import CaixaSession
from app.models.venda import Venda
from app.schemas.caixa import CaixaSessionCreate, CaixaSessionResponse, CaixaSessionClose

router = APIRouter(prefix="/caixa", tags=["Caixa"])

@router.get("/status", response_model=CaixaSessionResponse)
def get_status(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    # Busca caixa aberto para esta loja
    session = db.query(CaixaSession).filter(
        CaixaSession.store_id == store_id,
        CaixaSession.closed_at == None
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Nenhum caixa aberto")
    
    # Calcula total de vendas para o caixa atual
    total_sales = db.query(Venda).filter(
        Venda.cashier_id == session.id
    ).with_entities(Venda.total).all()
    
    session.total_sales = sum([v[0] for v in total_sales]) if total_sales else 0
    return session

@router.post("/abrir", response_model=CaixaSessionResponse)
def abrir_caixa(
    dados: CaixaSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    # Verifica se já tem caixa aberto
    session_aberta = db.query(CaixaSession).filter(
        CaixaSession.store_id == store_id,
        CaixaSession.closed_at == None
    ).first()
    
    if session_aberta:
        raise HTTPException(status_code=400, detail="Já existe um caixa aberto para esta loja.")
    
    nova_sessao = CaixaSession(
        store_id=store_id,
        user_id=current_user.id,
        opening_balance=dados.opening_balance,
        notes=dados.notes
    )
    db.add(nova_sessao)
    db.commit()
    db.refresh(nova_sessao)
    return nova_sessao

@router.post("/fechar", response_model=CaixaSessionResponse)
def fechar_caixa(
    dados: CaixaSessionClose,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    session = db.query(CaixaSession).filter(
        CaixaSession.store_id == store_id,
        CaixaSession.closed_at == None
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Nenhum caixa aberto para fechar.")
    
    # Total de vendas
    total_sales = db.query(Venda).filter(Venda.cashier_id == session.id).with_entities(Venda.total).all()
    session.total_sales = sum([v[0] for v in total_sales]) if total_sales else 0
    
    session.closing_balance = dados.closing_balance
    session.notes = dados.notes
    session.closed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    return session

@router.get("/historico", response_model=List[CaixaSessionResponse])
def listar_historico(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
    limit: int = 20
):
    return db.query(CaixaSession).filter(
        CaixaSession.store_id == store_id
    ).order_by(CaixaSession.opened_at.desc()).limit(limit).all()
