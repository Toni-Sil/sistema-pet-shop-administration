from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Set
from uuid import UUID, uuid4
import json


class EventType(str, Enum):
    NOVO_CLIENTE_CRIADO = "novo_cliente_criado"
    NOVA_VENDA = "nova_venda"
    AGENDAMENTO_CRIADO = "agendamento_criado"
    AGENDAMENTO_CONCLUIDO = "agendamento_concluido"
    ESTOQUE_BAIXO = "estoque_baixo"
    PAGAMENTO_RECEBIDO = "pagamento_recebido"
    PAGAMENTO_ATRASADO = "pagamento_atrasado"
    VACINA_VENCENDO = "vacina_vencendo"
    CLIENTE_INATIVO = "cliente_inativo"
    TAREFA_CRIADA = "tarefa_criada"
    TAREFA_CONCLUIDA = "tarefa_concluida"
    MENSAGEM_ENVIADA = "mensagem_enviada"
    AGENT_RESPONSE = "agent_response"
    ORCHESTRATOR_DECISION = "orchestrator_decision"


@dataclass
class Event:
    id: UUID = field(default_factory=uuid4)
    type: EventType = EventType.AGENT_RESPONSE
    payload: Dict[str, Any] = field(default_factory=dict)
    source_agent: str = "system"
    target_agent: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "type": self.type.value,
            "payload": self.payload,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }


EventHandler = Callable[[Event], Any]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, Set[EventHandler]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000

    def subscribe(self, event_type: EventType | str, handler: EventHandler) -> None:
        key = event_type.value if isinstance(event_type, EventType) else event_type
        if key not in self._subscribers:
            self._subscribers[key] = set()
        self._subscribers[key].add(handler)

    def unsubscribe(self, event_type: EventType | str, handler: EventHandler) -> None:
        key = event_type.value if isinstance(event_type, EventType) else event_type
        if key in self._subscribers:
            self._subscribers[key].discard(handler)

    async def publish(self, event: Event) -> List[Any]:
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        key = event.type.value
        handlers = self._subscribers.get(key, set())

        if event.target_agent:
            handlers = {h for h in handlers if self._get_handler_agent(h) == event.target_agent}

        results = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(event)
                else:
                    result = handler(event)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

        return results

    def _get_handler_agent(self, handler: EventHandler) -> str | None:
        return getattr(handler, "_agent_name", None)

    def get_history(
        self,
        event_type: EventType | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> List[Event]:
        events = self._event_history

        if event_type:
            events = [e for e in events if e.type == event_type]

        if since:
            events = [e for e in events if e.timestamp >= since]

        return events[-limit:]

    def clear_history(self) -> None:
        self._event_history.clear()


event_bus = EventBus()


def subscribe(event_type: EventType | str, agent_name: str | None = None):
    def decorator(func: EventHandler) -> EventHandler:
        func._agent_name = agent_name
        event_bus.subscribe(event_type, func)
        return func
    return decorator