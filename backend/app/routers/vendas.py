from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.schemas.venda import VendaCreate, VendaResponse
from app.services import venda_service

router = APIRouter(prefix="/vendas", tags=["Vendas"])

@router.get("", response_model=List[VendaResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    return venda_service.listar(db, store_id, skip, limit)

@router.get("/{id}", response_model=VendaResponse)
def buscar(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    return venda_service.buscar_por_id(db, id, store_id)

@router.post("", response_model=VendaResponse, status_code=201)
def nova_venda(
    venda_data: VendaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    return venda_service.realizar_venda(db, venda_data, store_id, current_user.id)
