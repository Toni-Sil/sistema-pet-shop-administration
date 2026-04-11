from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.models.cliente import Pet
from app.models.pet_vaccine import PetVaccine
from app.models.pet_note import PetNote
from app.models.agendamento import Agendamento
from app.schemas.crm import PetVaccineResponse, PetVaccineCreate, PetNoteResponse, PetNoteCreate
from app.schemas.cliente import PetResponse

router = APIRouter(prefix="/pets", tags=["CRM de Pets"])

@router.get("/{id}", response_model=PetResponse)
def get_pet_details(
    id: UUID,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    pet = db.query(Pet).filter(Pet.id == id, Pet.store_id == store_id).first()
    if not pet:
        raise HTTPException(404, "Pet não encontrado")
    return pet

@router.get("/{id}/vaccines", response_model=List[PetVaccineResponse])
def list_pet_vaccines(
    id: UUID,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    # Verifica se pet existe e pertence à loja
    pet = db.query(Pet).filter(Pet.id == id, Pet.store_id == store_id).first()
    if not pet:
        raise HTTPException(404, "Pet não encontrado")
    
    return db.query(PetVaccine).filter(PetVaccine.pet_id == id).all()

@router.post("/{id}/vaccines", response_model=PetVaccineResponse)
def register_vaccine(
    id: UUID,
    vaccine_in: PetVaccineCreate,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    pet = db.query(Pet).filter(Pet.id == id, Pet.store_id == store_id).first()
    if not pet:
        raise HTTPException(404, "Pet não encontrado")
    
    db_vaccine = PetVaccine(**vaccine_in.model_dump())
    db_vaccine.pet_id = id
    db.add(db_vaccine)
    db.commit()
    db.refresh(db_vaccine)
    return db_vaccine

@router.get("/{id}/history")
def get_pet_history(
    id: UUID,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    # Retorna agendamentos concluídos e notas
    pet = db.query(Pet).filter(Pet.id == id, Pet.store_id == store_id).first()
    if not pet:
        raise HTTPException(404, "Pet não encontrado")
    
    agendamentos = db.query(Agendamento).filter(
        Agendamento.pet_id == id, 
        Agendamento.status == "done"
    ).order_by(Agendamento.date.desc()).all()
    
    notes = db.query(PetNote).filter(PetNote.pet_id == id).order_by(PetNote.created_at.desc()).all()
    
    return {
        "agendamentos": agendamentos,
        "notes": notes
    }

@router.post("/{id}/notes", response_model=PetNoteResponse)
def add_pet_note(
    id: UUID,
    note_in: PetNoteCreate,
    current_user: User = Depends(get_any_role),
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
):
    pet = db.query(Pet).filter(Pet.id == id, Pet.store_id == store_id).first()
    if not pet:
        raise HTTPException(404, "Pet não encontrado")
    
    db_note = PetNote(
        pet_id=id,
        user_id=current_user.id,
        note=note_in.note
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note
