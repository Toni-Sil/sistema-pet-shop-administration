from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from .agents import AgentContext, build_llm_client, get_agent, get_openai_api_key_from_settings
from app.database import get_db
from app.core.deps import get_current_store_id
from app.models.store import Store

router = APIRouter()


async def get_store_settings(
    db: Session = Depends(get_db),
    store_id: UUID = Depends(get_current_store_id)
) -> Dict[str, Any]:
    store = db.query(Store).filter(Store.id == store_id).first()
    return store.settings if store else {}


async def get_llm_client(
    store_settings=Depends(get_store_settings)
):
    key = get_openai_api_key_from_settings(store_settings)
    return build_llm_client(key)


@router.post("/orchestrator")
async def orchestrate(
    payload: Dict[str, Any], 
    llm_client=Depends(get_llm_client),
    store_settings=Depends(get_store_settings)
):
    agent = get_agent("orchestrator", llm_client, store_settings)
    ctx = AgentContext()
    result = await agent.run(ctx, payload)
    return result


@router.post("/estoque")
async def estoque_agent(
    payload: Dict[str, Any], 
    llm_client=Depends(get_llm_client),
    store_settings=Depends(get_store_settings)
):
    agent = get_agent("estoque", llm_client, store_settings)
    ctx = AgentContext()
    result = await agent.run(ctx, payload)
    return result


@router.post("/financeiro")
async def financeiro_agent(
    payload: Dict[str, Any], 
    llm_client=Depends(get_llm_client),
    store_settings=Depends(get_store_settings)
):
    agent = get_agent("financeiro", llm_client, store_settings)
    ctx = AgentContext()
    result = await agent.run(ctx, payload)
    return result
