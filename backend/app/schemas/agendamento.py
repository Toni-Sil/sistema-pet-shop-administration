from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, date
from typing import Optional


class AgendamentoBase(BaseModel):
    pet_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    service: Optional[str] = None # Para compatibilidade legada
    professional: Optional[str] = None
    date: date
    time: str
    price: Optional[str] = None
    notes: Optional[str] = None


class AgendamentoCreate(AgendamentoBase):
    pass


class AgendamentoUpdate(BaseModel):
    status: Optional[str] = None
    professional: Optional[str] = None
    date: Optional[date] = None
    time: Optional[str] = None
    notes: Optional[str] = None


class AgendamentoResponse(AgendamentoBase):
    id: UUID
    store_id: UUID
    user_id: Optional[UUID] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
