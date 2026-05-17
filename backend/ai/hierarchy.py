from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ai.runtime import AgentRuntime, agent_registry, ExecutionMode, AgentState
from ai.event_bus import Event, EventType, event_bus
from ai.memory import AgentMemory, MemoryType


class SupervisorDecision(str, Enum):
    EXECUTE_AGENT = "execute_agent"
    EXECUTE_MULTIPLE = "execute_multiple"
    REQUIRE_HUMAN_APPROVAL = "require_human_approval"
    ESCALATE = "escalate"
    DEFER = "defer"
    RESOLVE = "resolve"


@dataclass
class SubAgent:
    name: str
    role: str
    enabled: bool = True
    priority: int = 5
    conflict_resolution: str = "supervisor_decides"


@dataclass
class SupervisorDecision:
    decision: SupervisorDecision
    target_agents: List[str] = field(default_factory=list)
    reasoning: str = ""
    confidence: float = 0.0
    requires_approval: bool = False
    approval_reason: str | None = None


class CognitiveHierarchy:
    HIERARCHY = {
        "supervisor": {
            "role": "coordenacao_geral",
            "sub_agents": [
                "atendimento",
                "agendamento",
                "financeiro",
                "estoque",
                "crm",
            ],
            "capabilities": [
                "coordenacao",
                "resolucao_conflitos",
                "definir_prioridade",
                "aprovar_acao_humana",
            ],
        },
        "atendimento": {
            "role": "suporte_cliente",
            "sub_agents": [],
            "capabilities": ["faq", "suporte", "encaminhamento"],
        },
        "agendamento": {
            "role": "gestao_agenda",
            "sub_agents": [],
            "capabilities": ["criar", "consultar", "lembrete"],
        },
        "financeiro": {
            "role": "gestao_financeira",
            "sub_agents": [],
            "capabilities": ["vendas", "despesas", "relatorios"],
        },
        "estoque": {
            "role": "gestao_estoque",
            "sub_agents": ["compras"],
            "capabilities": ["consultar", "alertas", "reposicao"],
        },
        "crm": {
            "role": "relacionamento",
            "sub_agents": ["marketing"],
            "capabilities": ["historico", "vacinas", "campanhas"],
        },
        "compras": {
            "role": "reposicao",
            "sub_agents": [],
            "capabilities": ["identificar_falta", "sugerir_compra"],
        },
        "marketing": {
            "role": "divulgacao",
            "sub_agents": [],
            "capabilities": ["campanhas", "mensagens"],
        },
    }

    def __init__(self, store_id: str) -> None:
        self.store_id = store_id
        self._supervisor_runtime: Optional[AgentRuntime] = None
        self._sub_agents: Dict[str, AgentRuntime] = {}
        self._init_hierarchy()

    def _init_hierarchy(self) -> None:
        supervisor_config = {
            "execution_mode": "async",
            "permissions": [
                {"resource": "*", "actions": ["read", "execute", "delegate"]}
            ],
            "tools": ["route", "delegate", "approve", "escalate"],
            "triggers": [
                {"event": "novo_cliente_criado", "action": "welcome"},
                {"event": "nova_venda", "action": "track"},
                {"event": "estoque_baixo", "action": "evaluate"},
                {"event": "cliente_inativo", "action": "campaign"},
            ],
            "workflow": [
                {"name": "analyze", "agent": "supervisor", "action": "analyze", "timeout_seconds": 10},
                {"name": "delegate", "agent": "supervisor", "action": "delegate", "timeout_seconds": 5},
                {"name": "merge_results", "agent": "supervisor", "action": "merge", "timeout_seconds": 10},
            ],
        }

        self._supervisor_runtime = agent_registry.create_runtime(
            "supervisor", self.store_id, supervisor_config
        )

        for agent_name, agent_config in self.HIERARCHY.items():
            if agent_name == "supervisor":
                continue

            config = {
                "execution_mode": "async",
                "permissions": self._get_permissions_for_role(agent_config["role"]),
                "tools": agent_config["capabilities"],
                "triggers": [],
                "workflow": [],
            }
            runtime = agent_registry.create_runtime(agent_name, self.store_id, config)
            self._sub_agents[agent_name] = runtime

    def _get_permissions_for_role(self, role: str) -> List[Dict[str, Any]]:
        role_perms = {
            "coordenacao_geral": [{"resource": "*", "actions": ["*"]}],
            "suporte_cliente": [{"resource": "clientes", "actions": ["read"]}],
            "gestao_agenda": [{"resource": "agendamentos", "actions": ["read", "write"]}],
            "gestao_financeira": [{"resource": "financeiro", "actions": ["read", "write"]}],
            "gestao_estoque": [{"resource": "estoque", "actions": ["read", "write"]}],
            "relacionamento": [{"resource": "crm", "actions": ["read", "write"]}],
            "reposicao": [{"resource": "compras", "actions": ["read", "write"]}],
            "divulgacao": [{"resource": "marketing", "actions": ["read", "send"]}],
        }
        return role_perms.get(role, [{"resource": "*", "actions": ["read"]}])

    async def process_request(
        self,
        message: str,
        context: Dict[str, Any],
        user_id: str | None = None,
    ) -> Dict[str, Any]:
        correlation_id = str(uuid4())

        await event_bus.publish(Event(
            type=EventType.ORCHESTRATOR_DECISION,
            payload={"message": message, "context": context, "user_id": user_id},
            source_agent="client",
            correlation_id=correlation_id,
        ))

        decision = await self._supervisor_decide(message, context, correlation_id)

        if decision.requires_approval:
            return {
                "status": "pending_approval",
                "decision": decision.decision.value,
                "reason": decision.approval_reason,
                "message": message,
            }

        results = await self._execute_decision(decision, context, correlation_id)

        await event_bus.publish(Event(
            type=EventType.AGENT_RESPONSE,
            payload={"results": results, "decision": decision.decision.value},
            source_agent="supervisor",
            correlation_id=correlation_id,
        ))

        return {
            "status": "success",
            "decision": decision.decision.value,
            "reasoning": decision.reasoning,
            "confidence": decision.confidence,
            "results": results,
        }

    async def _supervisor_decide(
        self,
        message: str,
        context: Dict[str, Any],
        correlation_id: str,
    ) -> SupervisorDecision:
        message_lower = message.lower()

        if any(w in message_lower for w in ["comprar", "repor", "estoque"]):
            agents = ["estoque", "compras"]
            confidence = 0.85
            requires_approval = context.get("high_value", False) or context.get("amount", 0) > 5000

            return SupervisorDecision(
                decision=SupervisorDecision.EXECUTE_MULTIPLE if len(agents) > 1 else SupervisorDecision.EXECUTE_AGENT,
                target_agents=agents,
                reasoning="Solicitação de reposição de estoque",
                confidence=confidence,
                requires_approval=requires_approval,
                approval_reason="Alto valor" if requires_approval else None,
            )

        if any(w in message_lower for w in ["venda", "faturamento", "dinheiro"]):
            return SupervisorDecision(
                decision=SupervisorDecision.EXECUTE_AGENT,
                target_agents=["financeiro"],
                reasoning="Análise financeira",
                confidence=0.9,
            )

        if any(w in message_lower for w in ["agendar", "hora", "dia"]):
            return SupervisorDecision(
                decision=SupervisorDecision.EXECUTE_AGENT,
                target_agents=["agendamento"],
                reasoning="Gerenciamento de agenda",
                confidence=0.9,
            )

        if any(w in message_lower for w in ["pet", "vacina", "cliente"]):
            return SupervisorDecision(
                decision=SupervisorDecision.EXECUTE_AGENT,
                target_agents=["crm"],
                reasoning="Relacionamento com cliente",
                confidence=0.85,
            )

        if any(w in message_lower for w in ["mensagem", "campanha", "promocao"]):
            return SupervisorDecision(
                decision=SupervisorDecision.EXECUTE_MULTIPLE,
                target_agents=["crm", "marketing"],
                reasoning="Campaigna de marketing",
                confidence=0.8,
            )

        return SupervisorDecision(
            decision=SupervisorDecision.EXECUTE_MULTIPLE,
            target_agents=["atendimento", "financeiro"],
            reasoning="Requisição geral",
            confidence=0.6,
        )

    async def _execute_decision(
        self,
        decision: SupervisorDecision,
        context: Dict[str, Any],
        correlation_id: str,
    ) -> List[Dict[str, Any]]:
        results = []

        for agent_name in decision.target_agents:
            runtime = self._sub_agents.get(agent_name)
            if runtime:
                execution = await runtime.execute(
                    action="process",
                    payload={"message": context.get("message", ""), "context": context},
                    correlation_id=correlation_id,
                )
                results.append({
                    "agent": agent_name,
                    "result": execution.output_data,
                    "state": execution.state.value,
                })

        return results

    def get_hierarchy_status(self) -> Dict[str, Any]:
        return {
            "supervisor": self._supervisor_runtime.get_current_state() if self._supervisor_runtime else None,
            "sub_agents": {
                name: runtime.get_current_state()
                for name, runtime in self._sub_agents.items()
            },
        }

    def get_agent(self, agent_name: str) -> AgentRuntime | None:
        if agent_name == "supervisor":
            return self._supervisor_runtime
        return self._sub_agents.get(agent_name)


class HierarchyRegistry:
    def __init__(self) -> None:
        self._hierarchies: Dict[str, CognitiveHierarchy] = {}

    def get_or_create(self, store_id: str) -> CognitiveHierarchy:
        if store_id not in self._hierarchies:
            self._hierarchies[store_id] = CognitiveHierarchy(store_id)
        return self._hierarchies[store_id]

    def remove(self, store_id: str) -> bool:
        if store_id in self._hierarchies:
            del self._hierarchies[store_id]
            return True
        return False


hierarchy_registry = HierarchyRegistry()