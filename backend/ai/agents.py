from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import httpx
from openai import AsyncOpenAI

from .config import AgentConfig, get_agent_config


@dataclass
class AgentContext:
    """Contexto passado para os agentes.

    Aqui no futuro você pode incluir:
    - store_id (instância do pet shop)
    - user_id (quem está chamando)
    - idioma
    - etc.
    """

    store_id: str | None = None
    user_id: str | None = None


class BaseAgent:
    def __init__(self, cfg: AgentConfig, llm_client: AsyncOpenAI) -> None:
        self.cfg = cfg
        self.llm = llm_client

    async def call_llm(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """Chama o modelo configurado para o agente.

        Inicialmente usa OpenAI; no futuro, pode ser trocado por outro provedor
        (Claude, Gemini, Sabiá, etc.) via camada de abstração.
        """

        response = await self.llm.chat.completions.create(
            model=self.cfg.model,
            max_tokens=self.cfg.max_tokens,
            temperature=self.cfg.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
        )
        return response.choices[0].message.content or ""

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - interface
        raise NotImplementedError


class OrchestratorAgent(BaseAgent):
    """Decide para qual agente rotear a requisição.

    Retorna um dicionário com:
    - target_agent: nome do agente
    - reasoning: breve explicação
    """

    SYSTEM_PROMPT = (
        "Você é o orquestrador de um sistema de gestão de pet shop. "
        "Sua função é APENAS decidir qual módulo deve tratar a solicitação: "
        "'estoque', 'financeiro', 'agendamento', 'crm', 'relatorios' ou 'whatsapp'. "
        "Responda em JSON com as chaves 'target_agent' e 'reasoning'."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        user_message = payload.get("message", "")
        messages = [
            {"role": "user", "content": user_message},
        ]
        raw = await self.call_llm(self.SYSTEM_PROMPT, messages)
        # Para manter simples, tentamos interpretar como JSON;
        # se falhar, caímos em um default.
        try:
            import json

            data = json.loads(raw)
            target = data.get("target_agent", "estoque")
            reasoning = data.get("reasoning", "")
        except Exception:
            target = "estoque"
            reasoning = "Não consegui interpretar corretamente, roteando para estoque por padrão."

        return {"target_agent": target, "reasoning": reasoning, "raw": raw}


class EstoqueAgent(BaseAgent):
    """Agente especializado em estoque.

    Versão inicial: apenas responde perguntas em linguagem natural
    usando os dados que forem passados no payload.
    Em versões futuras, pode chamar o banco para buscar produtos, alertas, etc.
    """

    SYSTEM_PROMPT = (
        "Você é um assistente especializado em ESTOQUE de um pet shop. "
        "Responda de forma objetiva em português do Brasil. "
        "Use apenas as informações fornecidas no contexto e no payload."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        question = payload.get("question", "")
        context = payload.get("context", "")
        messages = [
            {"role": "system", "content": f"Contexto:
{context}"},
            {"role": "user", "content": question},
        ]
        answer = await self.call_llm(self.SYSTEM_PROMPT, messages)
        return {"answer": answer}


class FinanceiroAgent(BaseAgent):
    SYSTEM_PROMPT = (
        "Você é um assistente financeiro para um pet shop. "
        "Explique resultados de vendas, despesas e lucro de forma clara, em linguagem simples."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        question = payload.get("question", "")
        context = payload.get("context", "")
        messages = [
            {"role": "system", "content": f"Contexto financeiro:
{context}"},
            {"role": "user", "content": question},
        ]
        answer = await self.call_llm(self.SYSTEM_PROMPT, messages)
        return {"answer": answer}


# Outros agentes (agendamento, CRM, relatórios, WhatsApp) podem seguir
# o mesmo padrão acima, com SYSTEM_PROMPT específico por módulo.


def build_llm_client() -> AsyncOpenAI:
    """Cria cliente LLM.

    - Por enquanto usa OpenAI, lendo OPENAI_API_KEY do ambiente.
    - No futuro, pode ser estendido para múltiplos provedores.
    """

    return AsyncOpenAI()


def get_agent(name: str, llm_client: AsyncOpenAI) -> BaseAgent:
    cfg = get_agent_config(name)

    if name == "orchestrator":
        return OrchestratorAgent(cfg, llm_client)
    if name == "estoque":
        return EstoqueAgent(cfg, llm_client)
    if name == "financeiro":
        return FinanceiroAgent(cfg, llm_client)

    # Fallback simples; em produção, lançar erro explícito
    return EstoqueAgent(cfg, llm_client)
