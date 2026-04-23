import logging
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.models.store import Store
from app.schemas.venda import VendaCreate, VendaResponse
from app.services import venda_service
from app.services import fiscal_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vendas", tags=["Vendas"])


async def _auto_emitir_nfe(db: Session, sale_id: UUID, store_id: UUID):
    """Dispara emissão automática de NF-e em segundo plano após a venda."""
    try:
        store = db.query(Store).filter(Store.id == store_id).first()
        api_key = fiscal_service._get_plugnotas_key(store) if store else None
        if not api_key:
            return  # Fiscal não configurado – silenciosamente ignora
        await fiscal_service.emitir_nfe(db, sale_id, store_id)
    except Exception as exc:
        logger.warning(f"[Auto NF-e] Falha para venda {sale_id}: {exc}")


@router.get("", response_model=List[VendaResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=500),
    cashier_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    return venda_service.listar(db, store_id, skip, limit, cashier_id)


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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    """Registra a venda e automaticamente tenta emitir NF-e em segundo plano."""
    venda = venda_service.realizar_venda(db, venda_data, store_id, current_user.id)
    background_tasks.add_task(_auto_emitir_nfe, db, venda.id, store_id)
    return venda
