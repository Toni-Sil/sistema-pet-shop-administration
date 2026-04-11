from pydantic import BaseModel, ConfigDict, EmailStr, Field
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List


class PetBase(BaseModel):
    name: str
    species: str = "dog"
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    weight: Optional[str] = None
    color: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class PetCreate(PetBase):
    pass


class PetUpdate(BaseModel):
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    weight: Optional[str] = None
    color: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None


class PetResponse(PetBase):
    id: UUID
    store_id: UUID
    client_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClienteBase(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ClienteResponse(ClienteBase):
    id: UUID
    store_id: UUID
    is_active: bool
    created_at: datetime
    pets: List[PetResponse] = []
    total_spent: Optional[float] = 0
    last_visit: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClienteInativoResponse(BaseModel):
    id: UUID
    name: str
    phone: str
    last_visit: datetime
    days_without_visit: int
    total_spent: float

    model_config = ConfigDict(from_attributes=True)
