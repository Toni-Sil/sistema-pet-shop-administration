from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

class CaixaSessionBase(BaseModel):
    opening_balance: Decimal
    notes: Optional[str] = None

class CaixaSessionCreate(CaixaSessionBase):
    pass

class CaixaSessionClose(BaseModel):
    closing_balance: Decimal
    notes: Optional[str] = None

class CaixaSessionResponse(CaixaSessionBase):
    id: UUID
    store_id: UUID
    user_id: UUID
    closing_balance: Optional[Decimal] = None
    total_sales: Optional[Decimal] = 0
    opened_at: datetime
    closed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
