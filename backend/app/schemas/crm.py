from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime, date
from typing import Optional

# Vacinas
class PetVaccineBase(BaseModel):
    vaccine: str
    applied_at: date
    next_dose: Optional[date] = None
    notes: Optional[str] = None

class PetVaccineCreate(PetVaccineBase):
    pass

class PetVaccineResponse(PetVaccineBase):
    id: UUID
    pet_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Notas
class PetNoteBase(BaseModel):
    note: str

class PetNoteCreate(PetNoteBase):
    pass

class PetNoteResponse(PetNoteBase):
    id: UUID
    pet_id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
