from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class MemoryType(str, Enum):
    EPISODICA = "episodica"
    CONTEXTUAL = "contextual"
    PERSISTENTE = "persistente"
    WORKFLOW = "workflow"


@dataclass
class MemoryEntry:
    id: UUID = field(default_factory=uuid4)
    memory_type: MemoryType = MemoryType.CONTEXTUAL
    key: str = ""
    value: Any = None
    agent_id: str = ""
    store_id: str = ""
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "memory_type": self.memory_type.value,
            "key": self.key,
            "value": self.value if not isinstance(self.value, (dict, list)) else json.dumps(self.value),
            "agent_id": self.agent_id,
            "store_id": self.store_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tags": self.tags,
            "metadata": self.metadata,
            "importance": self.importance,
        }


class MemoryStore:
    def __init__(self) -> None:
        self._episodic: List[MemoryEntry] = []
        self._contextual: Dict[str, List[MemoryEntry]] = {}
        self._persistent: Dict[str, Dict[str, MemoryEntry]] = {}
        self._workflow: Dict[str, List[MemoryEntry]] = {}

    def store(self, entry: MemoryEntry) -> None:
        if entry.memory_type == MemoryType.EPISODICA:
            self._episodic.append(entry)
            if len(self._episodic) > 10000:
                self._episodic = self._episodic[-5000:]

        elif entry.memory_type == MemoryType.CONTEXTUAL:
            key = f"{entry.agent_id}:{entry.store_id}"
            if key not in self._contextual:
                self._contextual[key] = []
            self._contextual[key].append(entry)

        elif entry.memory_type == MemoryType.PERSISTENTE:
            key = f"{entry.agent_id}:{entry.store_id}"
            if key not in self._persistent:
                self._persistent[key] = {}
            self._persistent[key][entry.key] = entry

        elif entry.memory_type == MemoryType.WORKFLOW:
            workflow_id = entry.metadata.get("workflow_id", "default")
            if workflow_id not in self._workflow:
                self._workflow[workflow_id] = []
            self._workflow[workflow_id].append(entry)

    def retrieve(
        self,
        memory_type: MemoryType | None = None,
        agent_id: str | None = None,
        store_id: str | None = None,
        key: str | None = None,
        tags: List[str] | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> List[MemoryEntry]:
        results = []

        if memory_type == MemoryType.EPISODICA or memory_type is None:
            for entry in self._episodic:
                if self._matches(entry, agent_id, store_id, key, tags, since):
                    results.append(entry)

        if memory_type == MemoryType.CONTEXTUAL or memory_type is None:
            for entries in self._contextual.values():
                for entry in entries:
                    if self._matches(entry, agent_id, store_id, key, tags, since):
                        if entry not in results:
                            results.append(entry)

        if memory_type == MemoryType.PERSISTENTE or memory_type is None:
            for entries in self._persistent.values():
                for entry in entries.values():
                    if self._matches(entry, agent_id, store_id, key, tags, since):
                        if entry not in results:
                            results.append(entry)

        if memory_type == MemoryType.WORKFLOW or memory_type is None:
            for entries in self._workflow.values():
                for entry in entries:
                    if self._matches(entry, agent_id, store_id, key, tags, since):
                        if entry not in results:
                            results.append(entry)

        results.sort(key=lambda x: (x.importance, x.created_at), reverse=True)
        return results[:limit]

    def _matches(
        self,
        entry: MemoryEntry,
        agent_id: str | None,
        store_id: str | None,
        key: str | None,
        tags: List[str] | None,
        since: datetime | None,
    ) -> bool:
        if agent_id and entry.agent_id != agent_id:
            return False
        if store_id and entry.store_id != store_id:
            return False
        if key and entry.key != key:
            return False
        if tags and not any(t in entry.tags for t in tags):
            return False
        if since and entry.created_at < since:
            return False
        if entry.expires_at and entry.expires_at < datetime.utcnow():
            return False
        return True

    def get_client_history(self, store_id: str, client_id: str) -> List[MemoryEntry]:
        return self.retrieve(
            tags=[f"client:{client_id}"],
            store_id=store_id,
            limit=20,
        )

    def get_workflow_memory(self, workflow_id: str) -> List[MemoryEntry]:
        return self._workflow.get(workflow_id, [])

    def clear_expired(self) -> int:
        count = 0
        now = datetime.utcnow()

        for i in range(len(self._episodic) - 1, -1, -1):
            if self._episodic[i].expires_at and self._episodic[i].expires_at < now:
                del self._episodic[i]
                count += 1

        for key in list(self._contextual.keys()):
            for i in range(len(self._contextual[key]) - 1, -1, -1):
                if self._contextual[key][i].expires_at and self._contextual[key][i].expires_at < now:
                    del self._contextual[key][i]
                    count += 1

        return count


class AgentMemory:
    def __init__(self, agent_id: str, store_id: str) -> None:
        self.agent_id = agent_id
        self.store_id = store_id
        self._store: MemoryStore = memory_store

    def remember(
        self,
        key: str,
        value: Any,
        memory_type: MemoryType = MemoryType.CONTEXTUAL,
        tags: List[str] | None = None,
        importance: int = 5,
        expires_hours: int | None = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            memory_type=memory_type,
            key=key,
            value=value,
            agent_id=self.agent_id,
            store_id=self.store_id,
            tags=tags or [],
            importance=importance,
            expires_at=datetime.utcnow() + timedelta(hours=expires_hours) if expires_hours else None,
        )
        self._store.store(entry)
        return entry

    def recall(
        self,
        key: str | None = None,
        memory_type: MemoryType | None = None,
        tags: List[str] | None = None,
        since: datetime | None = None,
        limit: int = 10,
    ) -> List[MemoryEntry]:
        return self._store.retrieve(
            memory_type=memory_type,
            agent_id=self.agent_id,
            store_id=self.store_id,
            key=key,
            tags=tags,
            since=since,
            limit=limit,
        )

    def remember_client_interaction(
        self,
        client_id: str,
        interaction_type: str,
        content: str,
        outcome: str | None = None,
    ) -> None:
        self.remember(
            key=f"interaction_{client_id}_{uuid4().hex[:8]}",
            value={
                "client_id": client_id,
                "type": interaction_type,
                "content": content,
                "outcome": outcome,
            },
            memory_type=MemoryType.EPISODICA,
            tags=[f"client:{client_id}", f"type:{interaction_type}"],
            importance=7,
            expires_hours=720,
        )

    def remember_workflow_step(
        self,
        workflow_id: str,
        step: str,
        result: Any,
        next_action: str | None = None,
    ) -> None:
        self.remember(
            key=f"workflow_step_{step}",
            value={
                "step": step,
                "result": result,
                "next_action": next_action,
            },
            memory_type=MemoryType.WORKFLOW,
            tags=["workflow"],
            metadata={"workflow_id": workflow_id},
            importance=8,
        )


memory_store = MemoryStore()
memory_store.clear_expired()