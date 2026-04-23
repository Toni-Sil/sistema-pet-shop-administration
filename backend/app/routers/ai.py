from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.schemas.ai import ChatRequest, ChatResponse
from app.services.ai_service import ai_service

router = APIRouter(prefix="/ai", tags=["Inteligência Artificial"])

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
    current_user: User = Depends(get_any_role)
):
    return await ai_service.process_chat(db, store_id, request)


@router.get("/inventory-predictions")
async def get_inventory_predictions(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
    current_user: User = Depends(get_any_role)
):
    """Retorna previsões de estoque baseadas em IA"""
    from app.services.ai_tools import ai_tools
    return ai_tools.get_inventory_predictions(db, store_id)


@router.post("/scribe")
async def vet_scribe(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
    current_user: User = Depends(get_any_role)
):
    """Transforma áudio de consulta em prontuário estruturado"""
    audio_content = await file.read()
    return await ai_service.process_audio_scribe(audio_content)
