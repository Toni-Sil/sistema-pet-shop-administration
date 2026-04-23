from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

class ItemVendaBase(BaseModel):
    product_id: Optional[UUID] = None
    pacote_id: Optional[UUID] = None
    quantity: Optional[int] = None
    weight: Optional[Decimal] = None
    unit_price: Decimal
    total: Decimal

class VendaPagamentoBase(BaseModel):
    method: str
    amount: Decimal

class VendaCreate(BaseModel):
    client_id: Optional[UUID] = None
    items: List[ItemVendaBase]
    discount: Optional[Decimal] = Decimal('0.00')
    payment_method: Optional[str] = None # Mantido para compatibilidade temporária
    payments: Optional[List[VendaPagamentoBase]] = None
    notes: Optional[str] = None

class ItemVendaResponse(ItemVendaBase):
    id: UUID
    sale_id: UUID

    model_config = ConfigDict(from_attributes=True)

class VendaResponse(BaseModel):
    id: UUID
    store_id: UUID
    client_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    cashier_id: Optional[UUID] = None
    total: Decimal
    discount: Decimal
    payment_method: str
    payment_status: str
    asaas_charge_id: Optional[str] = None
    pix_qr_code: Optional[str] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    items: List[ItemVendaResponse]

    model_config = ConfigDict(from_attributes=True)
