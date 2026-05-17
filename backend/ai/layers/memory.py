from __future__ import annotations
"""
MEMORY LAYER - Context
Responsabilidade: Memória persistente, vetorial e contextual
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ai.memory import MemoryEntry, MemoryType, memory_store


@dataclass
class ConversationMemory:
    session_id: str
    agent_id: str
    store_id: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.updated_at = datetime.utcnow()
        
        memory_store.store(MemoryEntry(
            memory_type=MemoryType.EPISODICA,
            key=f"msg_{self.session_id}_{len(self.messages)}",
            value={"role": role, "content": content},
            agent_id=self.agent_id,
            store_id=self.store_id,
            tags=[f"session:{self.session_id}", "conversation"],
            importance=3,
        ))


@dataclass
class ClientMemory:
    client_id: str
    store_id: str
    pet_preferences: Dict[str, Any] = field(default_factory=dict)
    communication_tone: str = "formal"
    last_interactions: List[Dict[str, Any]] = field(default_factory=list)
    total_spent: float = 0.0
    visit_frequency_days: int = 30
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def remember_interaction(self, interaction_type: str, content: str, outcome: str | None = None) -> None:
        self.last_interactions.append({
            "type": interaction_type,
            "content": content,
            "outcome": outcome,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        if len(self.last_interactions) > 50:
            self.last_interactions = self.last_interactions[-50:]
        
        memory_store.store(MemoryEntry(
            memory_type=MemoryType.PERSISTENTE,
            key=f"client_interaction_{self.client_id}",
            value={
                "interaction_type": interaction_type,
                "content": content,
                "outcome": outcome,
            },
            agent_id="memory",
            store_id=self.store_id,
            tags=[f"client:{self.client_id}", interaction_type],
            importance=7,
        ))
        
        self.last_updated = datetime.utcnow()


@dataclass
class WorkflowMemory:
    workflow_id: str
    store_id: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: str = ""
    state: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_step(self, step_name: str, result: Any, next_step: str | None = None) -> None:
        self.steps.append({
            "step": step_name,
            "result": result,
            "next": next_step,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        self.current_step = next_step or ""
        
        memory_store.store(MemoryEntry(
            memory_type=MemoryType.WORKFLOW,
            key=f"workflow_{self.workflow_id}_{step_name}",
            value={"step": step_name, "result": result, "next": next_step},
            agent_id="workflow",
            store_id=self.store_id,
            tags=[f"workflow:{self.workflow_id}"],
            metadata={"workflow_id": self.workflow_id},
            importance=8,
        ))


class MemoryLayer:
    def __init__(self) -> None:
        self._conversations: Dict[str, ConversationMemory] = {}
        self._client_memories: Dict[str, ClientMemory] = {}
        self._workflows: Dict[str, WorkflowMemory] = {}

    def create_conversation(self, session_id: str, agent_id: str, store_id: str, context: Dict[str, Any] | None = None) -> ConversationMemory:
        conv = ConversationMemory(
            session_id=session_id,
            agent_id=agent_id,
            store_id=store_id,
            context=context or {},
        )
        self._conversations[session_id] = conv
        return conv

    def get_conversation(self, session_id: str) -> ConversationMemory | None:
        conv = self._conversations.get(session_id)
        if not conv:
            entries = memory_store.retrieve(
                tags=[f"session:{session_id}"],
                memory_type=MemoryType.EPISODICA,
                limit=100,
            )
            if entries:
                conv = ConversationMemory(
                    session_id=session_id,
                    agent_id=entries[0].agent_id,
                    store_id=entries[0].store_id,
                )
                for e in entries:
                    if e.value and isinstance(e.value, dict):
                        conv.messages.append(e.value)
        return conv

    def get_or_create_client_memory(self, client_id: str, store_id: str) -> ClientMemory:
        key = f"{store_id}:{client_id}"
        if key not in self._client_memories:
            self._client_memories[key] = ClientMemory(
                client_id=client_id,
                store_id=store_id,
            )
        return self._client_memories[key]

    def create_workflow(self, workflow_id: str, store_id: str, initial_state: Dict[str, Any] | None = None) -> WorkflowMemory:
        wf = WorkflowMemory(
            workflow_id=workflow_id,
            store_id=store_id,
            state=initial_state or {},
        )
        self._workflows[workflow_id] = wf
        return wf

    def get_workflow(self, workflow_id: str) -> WorkflowMemory | None:
        wf = self._workflows.get(workflow_id)
        if not wf:
            entries = memory_store.retrieve(
                tags=[f"workflow:{workflow_id}"],
                memory_type=MemoryType.WORKFLOW,
                limit=50,
            )
            if entries:
                wf = WorkflowMemory(
                    workflow_id=workflow_id,
                    store_id=entries[0].store_id,
                )
                for e in entries:
                    if e.value and isinstance(e.value, dict):
                        wf.add_step(
                            e.value.get("step", ""),
                            e.value.get("result"),
                            e.value.get("next"),
                        )
        return wf

    def search_client_history(self, store_id: str, client_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        entries = memory_store.get_client_history(store_id, client_id)
        return [
            {
                "type": e.tags[1] if len(e.tags) > 1 else "unknown",
                "content": e.value if isinstance(e.value, str) else str(e.value),
                "timestamp": e.created_at.isoformat(),
                "importance": e.importance,
            }
            for e in entries[:limit]
        ]


memory_layer = MemoryLayer()


def get_client_context_memory(store_id: str, client_id: str) -> Dict[str, Any]:
    client_mem = memory_layer.get_or_create_client_memory(client_id, store_id)
    
    history = memory_layer.search_client_history(store_id, client_id, limit=10)
    
    return {
        "client_id": client_id,
        "pet_preferences": client_mem.pet_preferences,
        "communication_tone": client_mem.communication_tone,
        "total_spent": client_mem.total_spent,
        "visit_frequency_days": client_mem.visit_frequency_days,
        "recent_interactions": history,
    }