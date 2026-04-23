from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.core.deps import get_current_user, get_any_role
from app.models.user import User

router = APIRouter(prefix="/services", tags=["Serviços"])

@router.post("", response_model=ServiceResponse)
def create_service(
    service_in: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role)
):
    db_service = Service(
        **service_in.model_dump(),
        store_id=current_user.store_id
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@router.get("", response_model=List[ServiceResponse])
def list_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role)
):
    return db.query(Service).filter(Service.store_id == current_user.store_id).all()

@router.get("/{id}", response_model=ServiceResponse)
def get_service(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role)
):
    db_service = db.query(Service).filter(
        Service.id == id, Service.store_id == current_user.store_id
    ).first()
    if not db_service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return db_service

@router.put("/{id}", response_model=ServiceResponse)
def update_service(
    id: UUID,
    service_in: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role)
):
    db_service = db.query(Service).filter(
        Service.id == id, Service.store_id == current_user.store_id
    ).first()
    if not db_service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    update_data = service_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_service, key, value)
    
    db.commit()
    db.refresh(db_service)
    return db_service
