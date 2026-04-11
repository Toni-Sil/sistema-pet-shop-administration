from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DespesaBase(BaseModel):
    description: str
    amount: Decimal
    category: str
    due_date: date
    notes: Optional[str] = None


class DespesaCreate(DespesaBase):
    pass


class DespesaUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    category: Optional[str] = None
    due_date: Optional[date] = None
    paid_at: Optional[date] = None
    is_paid: Optional[bool] = None
    notes: Optional[str] = None


class DespesaResponse(DespesaBase):
    id: UUID
    store_id: UUID
    is_paid: bool
    paid_at: Optional[date] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
