from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.core.deps import get_current_user, get_current_store_id
from app.models.user import User
from app.models.store import Store
from app.schemas.store import StoreUpdate, StoreResponse
from app.schemas.auth import UserResponse
from app.services import asaas_service

router = APIRouter(prefix="/settings", tags=["Settings"])


class AsaasConfigRequest(BaseModel):
    customer_id: Optional[str] = None
    enable_pix: bool = False


class AsaasConfigResponse(BaseModel):
    customer_id: Optional[str]
    pix_enabled: bool


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/loja", response_model=StoreResponse)
def get_store(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    return store


@router.patch("/loja", response_model=StoreResponse)
def update_store(
    dados: StoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    for k, v in dados.model_dump(exclude_unset=True).items():
        setattr(store, k, v)
    db.commit()
    db.refresh(store)
    return store


@router.post("/asaas/configure", response_model=AsaasConfigResponse)
async def configure_asaas(
    dados: AsaasConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Configura integração com Asaas para Pix"""
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    
    if dados.customer_id:
        store.asaas_customer_id = dados.customer_id
    
    db.commit()
    db.refresh(store)
    
    return AsaasConfigResponse(
        customer_id=store.asaas_customer_id,
        pix_enabled=bool(store.asaas_customer_id)
    )


@router.post("/asaas/create-customer", response_model=AsaasConfigResponse)
async def create_asaas_customer(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria cliente no Asaas automaticamente"""
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    
    if store.asaas_customer_id:
        return AsaasConfigResponse(
            customer_id=store.asaas_customer_id,
            pix_enabled=True
        )
    
    try:
        result = await asaas_service.criar_customer(
            name=store.name,
            email=current_user.email,
            phone=store.phone
        )
        
        store.asaas_customer_id = result["id"]
        db.commit()
        
        return AsaasConfigResponse(
            customer_id=store.asaas_customer_id,
            pix_enabled=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar cliente: {str(e)}")
