from typing import Any, Dict, List, Union, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.core.deps import get_current_store_id
from app.services.agent_system_service import agent_system_service


router = APIRouter(prefix="/ai/v2", tags=["ai-v2"])


class ChatRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}
    user_id: str | None = None


class AgentExecuteRequest(BaseModel):
    agent: str
    action: str
    payload: Dict[str, Any] = {}


class ApprovalActionRequest(BaseModel):
    approval_id: str
    action: Union[str, Literal["approve", "reject"]]
    approver: str
    reason: Union[str, None] = None


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    result = await agent_system_service.process_message(
        db=db,
        store_id=store_id,
        message=request.message,
        context=request.context,
        user_id=request.user_id,
    )
    return result


@router.post("/execute")
async def execute_agent(
    request: AgentExecuteRequest,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    result = await agent_system_service.execute_agent(
        db=db,
        store_id=store_id,
        agent_name=request.agent,
        action=request.action,
        payload=request.payload,
    )
    return result


@router.get("/status")
async def get_status(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    result = await agent_system_service.get_agent_status(db=db, store_id=store_id)
    return result


@router.get("/executions")
async def get_executions(
    agent: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    result = await agent_system_service.get_execution_history(
        db=db, store_id=store_id, agent_name=agent, limit=limit
    )
    return result


@router.get("/approvals")
async def get_approvals(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    result = await agent_system_service.get_pending_approvals(db=db, store_id=store_id)
    return result


@router.post("/approvals/{approval_id}")
async def handle_approval(
    approval_id: str,
    request: ApprovalActionRequest,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    if request.action == "approve":
        result = await agent_system_service.approve_action(
            db=db,
            approval_id=UUID(approval_id),
            approver=request.approver,
        )
    else:
        result = await agent_system_service.reject_action(
            db=db,
            approval_id=UUID(approval_id),
            approver=request.approver,
            reason=request.reason or "",
        )
    return result


@router.get("/events")
async def get_events(
    event_type: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    result = await agent_system_service.get_event_history(
        db=db, store_id=store_id, event_type=event_type, limit=limit
    )
    return result


@router.post("/events")
async def trigger_event(
    event_type: str,
    payload: Dict[str, Any],
    source_agent: str = "system",
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    result = await agent_system_service.trigger_event(
        db=db,
        store_id=store_id,
        event_type=event_type,
        payload=payload,
        source_agent=source_agent,
    )
    return result


@router.get("/memory/{agent}")
async def get_agent_memory(
    agent: str,
    memory_type: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    result = await agent_system_service.get_agent_memory(
        db=db, store_id=store_id, agent_name=agent, memory_type=memory_type, limit=limit
    )
    return result