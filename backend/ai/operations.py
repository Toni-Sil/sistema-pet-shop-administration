from __future__ import annotations
"""
OPERATIONAL FLOW - O Coração do Sistema
WhatsApp → Events → Agents → Actions → Memory → Human Supervision
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ai.layers import (
    event_bus, Event, EventType,
    memory_layer, get_client_context_memory,
    tool_registry, get_available_tools,
    business_rules_engine,
    SupervisorReasoning, IntentClassifier, ConversationAgent,
)


class MessageSource(str, Enum):
    WHATSAPP = "whatsapp"
    MANUAL = "manual"
    SYSTEM = "system"
    WEBHOOK = "webhook"


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    WAITING_RESPONSE = "waiting"
    COMPLETED = "completed"
    ESCALATED = "escalated"


@dataclass
class IncomingMessage:
    id: str = field(default_factory=lambda: str(uuid4()))
    source: MessageSource = MessageSource.WHATSAPP
    phone: str = ""
    message: str = ""
    media_url: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationalContext:
    conversation_id: str
    store_id: str
    client_id: str | None = None
    client_phone: str = ""
    pet_id: str | None = None
    intent: str = "unknown"
    entities: Dict[str, Any] = field(default_factory=dict)
    current_agent: str = ""
    step: str = "intake"
    requires_approval: bool = False
    approval_reason: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class OperationalFlow:
    """
    Fluxo operacional contínuo:
    WhatsApp recebe mensagem → Evento criado → Classificador → Supervisor →
    Agente executa → Tool executa → Memória atualizada → Humano supervisiona
    """

    def __init__(self, store_id: str) -> None:
        self.store_id = store_id
        self._active_conversations: Dict[str, OperationalContext] = {}
        self._llm = None

    def set_llm(self, llm) -> None:
        self._llm = llm
        self._intent_classifier = IntentClassifier(llm)
        self._supervisor = SupervisorReasoning(llm)
        self._conversation_agent = ConversationAgent(llm)

    async def process_incoming_message(self, incoming: IncomingMessage) -> Dict[str, Any]:
        conversation_id = incoming.phone
        ctx = self._get_or_create_context(conversation_id, incoming.phone)
        ctx.metadata["last_message_time"] = incoming.timestamp.isoformat()

        await event_bus.publish(Event(
            type=EventType.MENSAGEM_ENVIADA,
            payload={
                "conversation_id": conversation_id,
                "message": incoming.message,
                "source": incoming.source.value,
            },
            source_agent="whatsapp",
            correlation_id=conversation_id,
        ))

        classification = await self._classify_intent(incoming.message, ctx)
        ctx.intent = classification.get("intent", "unknown")
        ctx.entities.update(classification.get("entities", {}))

        ctx.current_agent = self._route_to_agent(ctx.intent, ctx.entities)

        await event_bus.publish(Event(
            type=EventType.ORCHESTRATOR_DECISION,
            payload={
                "intent": ctx.intent,
                "entities": ctx.entities,
                "target_agent": ctx.current_agent,
            },
            source_agent="intake",
            target_agent=ctx.current_agent,
            correlation_id=conversation_id,
        ))

        conversation = memory_layer.get_or_create_client_memory(
            ctx.client_id or "unknown", self.store_id
        )

        history = memory_layer.search_client_history(self.store_id, ctx.client_id or "", limit=5)

        if ctx.intent == "agendamento":
            result = await self._handle_agendamento(ctx, incoming.message, history)
        elif ctx.intent == "consulta":
            result = await self._handle_consulta(ctx, incoming.message, history)
        elif ctx.intent == "reclamacao":
            result = await self._handle_reclamacao(ctx, incoming.message)
        elif ctx.intent == "compra":
            result = await self._handle_compra(ctx, incoming.message)
        else:
            result = await self._handle_conversation(ctx, incoming.message, history)

        if ctx.requires_approval:
            return {
                "status": "pending_approval",
                "approval_reason": ctx.approval_reason,
                "suggested_response": result.get("response"),
                "action": result.get("action"),
            }

        return result

    def _get_or_create_context(self, conversation_id: str, phone: str) -> OperationalContext:
        if conversation_id not in self._active_conversations:
            self._active_conversations[conversation_id] = OperationalContext(
                conversation_id=conversation_id,
                store_id=self.store_id,
                client_phone=phone,
            )
        return self._active_conversations[conversation_id]

    async def _classify_intent(self, message: str, ctx: OperationalContext) -> Dict[str, Any]:
        if not self._llm:
            return {"intent": "consulta", "entities": {}, "confidence": 0.5}

        return await self._intent_classifier.classify(message, {"phone": ctx.client_phone})

    def _route_to_agent(self, intent: str, entities: Dict[str, Any]) -> str:
        routes = {
            "agendamento": "agendamento",
            "consulta_veterinaria": "atendimento",
            "reclamacao": "atendimento",
            "compra": "estoque",
            "pagamento": "financeiro",
            "consulta": "atendimento",
            "informacoes": "atendimento",
        }
        return routes.get(intent, "atendimento")

    async def _handle_agendamento(
        self,
        ctx: OperationalContext,
        message: str,
        history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        client_context = get_client_context_memory(self.store_id, ctx.client_id or "") if ctx.client_id else {}

        if not ctx.entities.get("service"):
            ctx.step = "collect_service"
            return {
                "response": "Qual serviço você gostaria de agendar? (banho, tosa, consulta, etc.)",
                "action": "ask_service",
                "agent": "agendamento",
            }

        if not ctx.entities.get("date"):
            ctx.step = "collect_date"
            return {
                "response": "Que dia você prefere?",
                "action": "ask_date",
                "agent": "agendamento",
            }

        if not ctx.entities.get("time"):
            from ai.layers.business import SchedulingBusinessRules
            slots = SchedulingBusinessRules.get_available_slots(
                datetime.utcnow(), "general"
            )
            slot_strs = [s.strftime("%H:%M") for s in slots[:5]]
            return {
                "response": f"Disponemos dos seguintes horários: {', '.join(slot_strs)}. Qual prefere?",
                "action": "ask_time",
                "agent": "agendamento",
            }

        return {
            "response": "Perfeito! Vou confirmar seu agendamento...",
            "action": "create_appointment",
            "agent": "agendamento",
            "entities": ctx.entities,
        }

    async def _handle_consulta(
        self,
        ctx: OperationalContext,
        message: str,
        history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        history_str = "\n".join([h.get("content", "")[:100] for h in history[-3:]])

        response = await self._conversation_agent.respond(
            message=message,
            history=[],
            context={
                "history": history_str,
                "client_id": ctx.client_id,
                "intent": ctx.intent,
            },
        )

        return {
            "response": response.get("response", "Posso ajudar com mais alguma coisa?"),
            "action": "respond",
            "agent": "atendimento",
        }

    async def _handle_reclamacao(
        self,
        ctx: OperationalContext,
        message: str,
    ) -> Dict[str, Any]:
        ctx.requires_approval = True
        ctx.approval_reason = "Reclamação requer atenção humana"

        await event_bus.publish(Event(
            type=EventType.ORCHESTRATOR_DECISION,
            payload={
                "type": "escalation",
                "reason": "reclamacao",
                "message": message,
            },
            source_agent="atendimento",
            target_agent="supervisor",
        ))

        return {
            "response": "Entendi. Vou direcionar seu caso para nossa equipe. Um momento, por favor.",
            "action": "escalate",
            "agent": "atendimento",
            "escalation": True,
        }

    async def _handle_compra(
        self,
        ctx: OperationalContext,
        message: str,
    ) -> Dict[str, Any]:
        return {
            "response": "Vou verificar nosso estoque para você...",
            "action": "check_stock",
            "agent": "estoque",
        }

    async def _handle_conversation(
        self,
        ctx: OperationalContext,
        message: str,
        history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        history_msgs = [{"role": "user" if h.get("type") == "incoming" else "assistant", "content": h.get("content", "")} for h in history[-5:]]

        response = await self._conversation_agent.respond(
            message=message,
            history=history_msgs,
            context={"client_id": ctx.client_id},
        )

        client_mem = memory_layer.get_or_create_client_memory(ctx.client_id or "", self.store_id)
        client_mem.remember_interaction("chat", message, response.get("response"))

        return {
            "response": response.get("response", "Posso ajudar com mais alguma coisa?"),
            "action": "respond",
            "agent": "atendimento",
        }


class OperationalDashboard:
    """Painel Operacional - Centro de Operações Autônomas"""

    @staticmethod
    def get_operations_summary(
        store_id: str,
        active_flows: Dict[str, OperationalContext],
    ) -> Dict[str, Any]:
        active_count = len(active_flows)
        waiting_approval = sum(1 for f in active_flows.values() if f.requires_approval)
        by_agent = {}

        for flow in active_flows.values():
            agent = flow.current_agent or "intake"
            by_agent[agent] = by_agent.get(agent, 0) + 1

        intents = {}
        for flow in active_flows.values():
            intent = flow.intent
            intents[intent] = intents.get(intent, 0) + 1

        return {
            "active_conversations": active_count,
            "waiting_approval": waiting_approval,
            "by_agent": by_agent,
            "by_intent": intents,
            "health": "operational" if active_count > 0 else "idle",
        }

    @staticmethod
    def get_agent_activity(
        store_id: str,
    ) -> List[Dict[str, Any]]:
        from ai.runtime import agent_registry
        
        runtimes = agent_registry.get_all_runtimes(store_id)
        
        return [
            {
                "agent": r.agent_id,
                "state": r.state.value,
                "recent_executions": len(r._execution_history),
                "last_execution": r._execution_history[-1].started_at.isoformat() if r._execution_history else None,
            }
            for r in runtimes
        ]


class OperationalService:
    """Serviço principal que coordena todo o fluxo operacional"""

    def __init__(self) -> None:
        self._flows: Dict[str, OperationalFlow] = {}
        self._llm = None

    def set_llm(self, llm) -> None:
        self._llm = llm

    def get_flow(self, store_id: str) -> OperationalFlow:
        if store_id not in self._flows:
            self._flows[store_id] = OperationalFlow(store_id)
            if self._llm:
                self._flows[store_id].set_llm(self._llm)
        return self._flows[store_id]

    async def process_message(
        self,
        store_id: str,
        phone: str,
        message: str,
        source: MessageSource = MessageSource.WHATSAPP,
    ) -> Dict[str, Any]:
        flow = self.get_flow(store_id)

        incoming = IncomingMessage(
            source=source,
            phone=phone,
            message=message,
        )

        result = await flow.process_incoming_message(incoming)

        await event_bus.publish(Event(
            type=EventType.AGENT_RESPONSE,
            payload=result,
            source_agent=result.get("agent", "system"),
            correlation_id=phone,
        ))

        return result

    def get_dashboard(self, store_id: str) -> Dict[str, Any]:
        flow = self._flows.get(store_id)
        if not flow:
            return {"status": "no_active_flows"}

        return {
            "summary": OperationalDashboard.get_operations_summary(
                store_id, flow._active_conversations
            ),
            "agents": OperationalDashboard.get_agent_activity(store_id),
        }


operational_service = OperationalService()