from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal

class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    duration: int
    price: Decimal
    is_active: Optional[bool] = True

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[Decimal] = None
    is_active: Optional[bool] = None

class ServiceResponse(ServiceBase):
    id: UUID
    store_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
