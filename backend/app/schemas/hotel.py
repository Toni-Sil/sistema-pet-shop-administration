from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class QuartoBase(BaseModel):
    name: str
    tipo: Optional[str] = None
    preco_diaria: float
    capacidade: int = 1

class QuartoCreate(QuartoBase):
    pass

class QuartoResponse(QuartoBase):
    id: UUID
    status: str
    class Config:
        from_attributes = True

class HospedagemBase(BaseModel):
    pet_id: UUID
    quarto_id: UUID
    check_in_previsto: datetime
    check_out_previsto: datetime
    alimentacao: Optional[str] = None
    medicamentos: Optional[str] = None
    observacoes: Optional[str] = None

class HospedagemCreate(HospedagemBase):
    pass

class HospedagemUpdate(BaseModel):
    check_in_previsto: Optional[datetime] = None
    check_out_previsto: Optional[datetime] = None
    quarto_id: Optional[UUID] = None
    alimentacao: Optional[str] = None
    medicamentos: Optional[str] = None
    observacoes: Optional[str] = None

from app.schemas.cliente import PetResponse

class HospedagemResponse(HospedagemBase):
    id: UUID
    status: str
    valor_diaria: float
    valor_total: float
    check_in_real: Optional[datetime] = None
    check_out_real: Optional[datetime] = None
    pet: Optional[PetResponse] = None
    class Config:
        from_attributes = True
