from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.schemas.estoque import (
    EstoqueMovimentacaoCreate, EstoqueMovimentacaoResponse,
    AlertaEstoqueResponse, ProdutoVencimentoResponse
)
from app.services import estoque_service

router = APIRouter(prefix="/estoque", tags=["Estoque"])

@router.get("/movimentacoes", response_model=List[EstoqueMovimentacaoResponse])
def listar(
    product_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    return estoque_service.listar_movimentacoes(db, store_id, product_id, skip, limit)

@router.post("/movimentacoes", response_model=EstoqueMovimentacaoResponse, status_code=201)
def criar(
    dados: EstoqueMovimentacaoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    return estoque_service.registrar_movimentacao(db, dados, store_id, current_user.id)

@router.get("/alerts", response_model=List[AlertaEstoqueResponse])
def alertas_estoque(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    return estoque_service.listar_alertas(db, store_id)

@router.get("/expiring", response_model=List[ProdutoVencimentoResponse])
def produtos_vencendo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    return estoque_service.listar_vencendo(db, store_id)
