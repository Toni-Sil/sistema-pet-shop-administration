from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime, timedelta
import hashlib
import json

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.models.venda import Venda

router = APIRouter(prefix="/idempotency", tags=["Idempotency"])

class IdempotencyRequest(BaseModel):
    key: str
    payload: dict


class IdempotencyResponse(BaseModel):
    found: bool
    existing_result: dict = None


def hash_payload(payload: dict) -> str:
    json_str = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()


@router.post("/check", response_model=IdempotencyResponse)
async def check_idempotency(
    dados: IdempotencyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    """Verifica se uma requisição já foi processada"""
    key_hash = hash_payload({"key": dados.key, "store_id": str(store_id)})
    
    existing = db.query(Venda).filter(
        Venda.store_id == store_id,
        Venda.asaas_charge_id == key_hash
    ).first()
    
    if existing:
        return IdempotencyResponse(
            found=True,
            existing_result={
                "id": str(existing.id),
                "total": float(existing.total),
                "created_at": existing.created_at.isoformat()
            }
        )
    
    return IdempotencyResponse(found=False)