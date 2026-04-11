from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.core.deps import get_any_role, get_gerente_ou_admin, get_current_store_id
from app.models.user import User
from app.models.schedule_block import ScheduleBlock

router = APIRouter(prefix="/schedule/blocks", tags=["Schedule Blocks"])

class ScheduleBlockCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str] = None

class ScheduleBlockResponse(BaseModel):
    id: UUID
    store_id: UUID
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str]
    created_at: datetime
    
    model_config = {"from_attributes": True}

@router.get("", response_model=List[ScheduleBlockResponse])
def listar_bloqueios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    return db.query(ScheduleBlock).filter(
        ScheduleBlock.store_id == store_id
    ).offset(skip).limit(limit).all()

@router.post("", response_model=ScheduleBlockResponse, status_code=201)
def criar_bloqueio(
    block: ScheduleBlockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_gerente_ou_admin),
    store_id: UUID = Depends(get_current_store_id)
):
    if block.ends_at <= block.starts_at:
        raise HTTPException(status_code=400, detail="ends_at deve ser depois de starts_at")
    
    bloqueio = ScheduleBlock(
        store_id=store_id,
        starts_at=block.starts_at,
        ends_at=block.ends_at,
        reason=block.reason
    )
    db.add(bloqueio)
    db.commit()
    db.refresh(bloqueio)
    return bloqueio

@router.delete("/{id}")
def deletar_bloqueio(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_gerente_ou_admin),
    store_id: UUID = Depends(get_current_store_id)
):
    bloqueio = db.query(ScheduleBlock).filter(
        ScheduleBlock.id == id,
        ScheduleBlock.store_id == store_id
    ).first()
    if not bloqueio:
        raise HTTPException(status_code=404, detail="Bloqueio não encontrado")
    
    db.delete(bloqueio)
    db.commit()
    return {"message": "Bloqueio removido com sucesso"}