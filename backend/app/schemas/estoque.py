from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, date
from typing import Optional
from decimal import Decimal

class EstoqueMovimentacaoBase(BaseModel):
    product_id: UUID
    type: str
    quantity: Optional[int] = None
    weight: Optional[Decimal] = None
    reason: Optional[str] = None
    cost_price: Optional[Decimal] = None
    supplier: Optional[str] = None

class EstoqueMovimentacaoCreate(EstoqueMovimentacaoBase):
    pass

class EstoqueMovimentacaoResponse(EstoqueMovimentacaoBase):
    id: UUID
    store_id: UUID
    sale_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AlertaEstoqueResponse(BaseModel):
    product_id: UUID
    name: str
    quantity: Optional[int] = None
    weight_in_stock: Optional[Decimal] = None
    min_qty: Optional[int] = None
    min_weight: Optional[Decimal] = None
    status: str
    
    model_config = ConfigDict(from_attributes=True)


class ProdutoVencimentoResponse(BaseModel):
    id: UUID
    name: str
    expires_at: date
    status: str
    
    model_config = ConfigDict(from_attributes=True)
