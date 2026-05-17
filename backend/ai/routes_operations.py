from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID
from openai import AsyncOpenAI
from app.models.store import Store

from app.database import get_db
from app.core.deps import get_current_store_id
from ai.operations import operational_service, OperationalFlow, MessageSource
from ai.hierarchy import hierarchy_registry
from ai.event_bus import event_bus, EventType
from ai.memory import memory_store


router = APIRouter(prefix="/ai/operations", tags=["Operations Center"])


class ProcessMessageRequest(BaseModel):
    phone: str
    message: str
    source: str = "whatsapp"


class ApprovalRequest(BaseModel):
    conversation_id: str
    approved: bool
    approver: str
    modified_response: str | None = None


@router.post("/message")
async def process_message(
    request: ProcessMessageRequest,
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    from ai.agents import get_openai_api_key_from_settings, build_llm_client
    import os

    store = db.query(Store).filter(Store.id == store_id).first()
    settings = store.settings if store else {}
    openai_key = get_openai_api_key_from_settings(settings) or os.environ.get("OPENAI_API_KEY")

    flow = operational_service.get_flow(str(store_id))
    
    if openai_key and (flow._llm is None or getattr(flow, "_openai_key", None) != openai_key):
        flow.set_llm(build_llm_client(openai_key))
        flow._openai_key = openai_key

    if not openai_key:
        raise HTTPException(
            status_code=400,
            detail="Nenhuma chave API da OpenAI configurada. Configure em Configurações > IA Agentes."
        )

    result = await operational_service.process_message(
        store_id=str(store_id),
        phone=request.phone,
        message=request.message,
        source=MessageSource(request.source),
    )
    return result


@router.get("/dashboard")
async def get_dashboard(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    from ai.agents import get_openai_api_key_from_settings, build_llm_client
    import os

    store = db.query(Store).filter(Store.id == store_id).first()
    settings = store.settings if store else {}
    openai_key = get_openai_api_key_from_settings(settings) or os.environ.get("OPENAI_API_KEY")

    flow = operational_service.get_flow(str(store_id))
    
    if openai_key and (flow._llm is None or getattr(flow, "_openai_key", None) != openai_key):
        flow.set_llm(build_llm_client(openai_key))
        flow._openai_key = openai_key

    dashboard = operational_service.get_dashboard(str(store_id))
    if isinstance(dashboard, dict):
        if "summary" in dashboard:
            dashboard["summary"]["health"] = "operational" if openai_key else "configuration_pending"
        dashboard["openai_key_configured"] = bool(openai_key)
        if not openai_key and "agents" in dashboard:
            for agent in dashboard["agents"]:
                agent["state"] = "offline"
        
    return dashboard


@router.get("/conversations")
async def get_active_conversations(
    store_id: UUID = Depends(get_current_store_id),
):
    flow = operational_service.get_flow(str(store_id))
    return {
        "active": len(flow._active_conversations),
        "conversations": [
            {
                "id": k,
                "client_phone": v.client_phone,
                "intent": v.intent,
                "current_agent": v.current_agent,
                "step": v.step,
                "requires_approval": v.requires_approval,
            }
            for k, v in flow._active_conversations.items()
        ]
    }


@router.get("/agents/status")
async def get_agents_status(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    from ai.agents import get_openai_api_key_from_settings
    import os

    store = db.query(Store).filter(Store.id == store_id).first()
    settings = store.settings if store else {}
    openai_key = get_openai_api_key_from_settings(settings) or os.environ.get("OPENAI_API_KEY")

    hierarchy = hierarchy_registry.get_or_create(str(store_id))
    status = hierarchy.get_hierarchy_status()
    
    if not openai_key:
        if "supervisor" in status:
            status["supervisor"]["state"] = "offline"
        if "sub_agents" in status:
            for k in status["sub_agents"]:
                status["sub_agents"][k]["state"] = "offline"
        else:
            for k in status:
                if isinstance(status[k], dict) and "state" in status[k]:
                    status[k]["state"] = "offline"
                    
    return status


@router.get("/events/recent")
async def get_recent_events(
    limit: int = 50,
    event_type: str | None = None,
):
    events = event_bus.get_history(
        event_type=EventType(event_type) if event_type else None,
        limit=limit,
    )
    return {
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }


@router.get("/memory/client/{client_id}")
async def get_client_memory(
    client_id: str,
    store_id: UUID = Depends(get_current_store_id),
):
    from ai.layers.memory import get_client_context_memory
    return get_client_context_memory(str(store_id), client_id)


@router.post("/approval")
async def handle_approval(
    request: ApprovalRequest,
    store_id: UUID = Depends(get_current_store_id),
):
    flow = operational_service.get_flow(str(store_id))
    ctx = flow._active_conversations.get(request.conversation_id)

    if not ctx:
        return {"error": "Conversation not found"}

    if request.approved:
        return {
            "status": "approved",
            "response": request.modified_response or "Aprovado",
        }
    else:
        ctx.requires_approval = False
        return {
            "status": "rejected",
            "response": "Rejeitado. Nova resposta necessária.",
        }


@router.get("/health")
async def health_check(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id),
):
    from ai.agents import get_openai_api_key_from_settings, build_llm_client
    import os

    store = db.query(Store).filter(Store.id == store_id).first()
    settings = store.settings if store else {}
    openai_key = get_openai_api_key_from_settings(settings) or os.environ.get("OPENAI_API_KEY")

    flow = operational_service.get_flow(str(store_id))
    
    if openai_key and (flow._llm is None or getattr(flow, "_openai_key", None) != openai_key):
        flow.set_llm(build_llm_client(openai_key))
        flow._openai_key = openai_key

    return {
        "status": "operational" if openai_key else "configuration_pending",
        "active_conversations": len(flow._active_conversations),
        "llm_connected": flow._llm is not None and bool(openai_key),
        "openai_key_configured": bool(openai_key),
    }


@router.get("/suggestions")
async def get_suggestions(
    store_id: UUID = Depends(get_current_store_id),
):
    from ai.layers.business import business_rules_engine

    suggestions = []

    suggestions.append({
        "type": "operational",
        "title": "Revisar aprovações pendentes",
        "count": len([c for c in operational_service.get_flow(str(store_id))._active_conversations.values() if c.requires_approval]),
    })

    recent_events = event_bus.get_history(limit=20)
    errors = [e for e in recent_events if e.metadata.get("error")]
    if errors:
        suggestions.append({
            "type": "errors",
            "title": "Erros detectados",
            "count": len(errors),
        })

    return {"suggestions": suggestions}