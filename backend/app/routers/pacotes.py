from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.pacote import Pacote, PacoteItem, ClientePacote
from app.models.user import User

router = APIRouter(prefix="/pacotes", tags=["Pacotes"])

class PacoteItemSchema(BaseModel):
    service_id: UUID
    quantity: int

class PacoteCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    price: Decimal
    items: List[PacoteItemSchema]

@router.get("/")
def list_pacotes(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
    current_user: User = Depends(get_any_role)
):
    return db.query(Pacote).filter(Pacote.store_id == store_id).all()

@router.post("/")
def create_pacote(
    dados: PacoteCreate,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
    current_user: User = Depends(get_any_role)
):
    pacote = Pacote(
        store_id=store_id,
        name=dados.name,
        description=dados.description,
        price=dados.price
    )
    db.add(pacote)
    db.flush()
    
    for item in dados.items:
        db.add(PacoteItem(
            pacote_id=pacote.id,
            service_id=item.service_id,
            quantity=item.quantity
        ))
    
    db.commit()
    db.refresh(pacote)
    return pacote

@router.get("/cliente/{client_id}/saldo")
def get_cliente_saldo(
    client_id: UUID,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
    current_user: User = Depends(get_any_role)
):
    """Retorna o saldo de serviços do cliente (pacotes comprados)"""
    return db.query(ClientePacote).filter(
        ClientePacote.client_id == client_id,
        ClientePacote.store_id == store_id
    ).all()
