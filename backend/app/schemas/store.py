from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class StoreResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    phone: Optional[str] = None
    address: Optional[str] = None
    plan: str

    model_config = ConfigDict(from_attributes=True)
