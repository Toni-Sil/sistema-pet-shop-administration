from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.core.deps import get_any_role, get_gerente_ou_admin, get_current_store_id
from app.models.user import User
from app.schemas.despesa import DespesaCreate, DespesaUpdate, DespesaResponse
from app.services import despesa_service

router = APIRouter(prefix="/despesas", tags=["Despesas"])


@router.get("", response_model=List[DespesaResponse])
def listar(
    pendentes: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    return despesa_service.listar(db, store_id, pendentes, skip, limit)


@router.post("", response_model=DespesaResponse, status_code=201)
def criar(
    dados: DespesaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_gerente_ou_admin),
    store_id: UUID = Depends(get_current_store_id),
):
    return despesa_service.criar(db, dados, store_id)


@router.patch("/{id}", response_model=DespesaResponse)
def atualizar(
    id: UUID,
    dados: DespesaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_gerente_ou_admin),
    store_id: UUID = Depends(get_current_store_id),
):
    return despesa_service.atualizar(db, id, dados, store_id)


@router.post("/{id}/pagar", response_model=DespesaResponse)
def marcar_paga(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_gerente_ou_admin),
    store_id: UUID = Depends(get_current_store_id),
):
    return despesa_service.marcar_paga(db, id, store_id)


@router.delete("/{id}")
def deletar(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_gerente_ou_admin),
    store_id: UUID = Depends(get_current_store_id),
):
    return despesa_service.deletar(db, id, store_id)
