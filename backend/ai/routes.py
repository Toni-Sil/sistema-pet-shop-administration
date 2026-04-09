from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from .agents import AgentContext, build_llm_client, get_agent

router = APIRouter()


async def get_llm_client():
    # Em produção, você pode reaproveitar o cliente (singleton) em vez de criar sempre
    return build_llm_client()


@router.post("/orchestrator")
async def orchestrate(payload: Dict[str, Any], llm_client=Depends(get_llm_client)):
    """Endpoint para o Agente Orquestrador.

    Exemplo de payload:
    {
      "message": "quero ver os produtos com estoque baixo"
    }
    """

    agent = get_agent("orchestrator", llm_client)
    ctx = AgentContext()
    result = await agent.run(ctx, payload)
    return result


@router.post("/estoque")
async def estoque_agent(payload: Dict[str, Any], llm_client=Depends(get_llm_client)):
    """Endpoint do agente de Estoque.

    Espera um payload com:
    - question: pergunta do usuário
    - context: (opcional) dados de estoque já agregados pelo backend
    """

    agent = get_agent("estoque", llm_client)
    ctx = AgentContext()
    result = await agent.run(ctx, payload)
    return result


@router.post("/financeiro")
async def financeiro_agent(payload: Dict[str, Any], llm_client=Depends(get_llm_client)):
    """Endpoint do agente Financeiro.

    Similar ao estoque, mas focalizado em contexto financeiro.
    """

    agent = get_agent("financeiro", llm_client)
    ctx = AgentContext()
    result = await agent.run(ctx, payload)
    return result
