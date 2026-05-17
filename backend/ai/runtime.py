from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

from ai.memory import AgentMemory, MemoryType
from ai.event_bus import Event, EventType, event_bus


class AgentState(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    SUSPENDED = "suspended"


class ExecutionMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"


@dataclass
class AgentPermission:
    resource: str
    actions: List[str]

    def can(self, action: str) -> bool:
        return action in self.actions or "*" in self.actions


@dataclass
class AgentTrigger:
    event_type: EventType
    condition: Callable[[Event], bool] | None = None
    action: str = "react"


@dataclass
class EscalationRule:
    condition: Callable[[Any], bool]
    target_agent: str
    reason: str


@dataclass
class WorkflowStep:
    name: str
    agent: str
    action: str
    on_success: str | None = None
    on_error: str | None = None
    timeout_seconds: int = 30


@dataclass
class AgentExecution:
    id: UUID = field(default_factory=uuid4)
    agent_id: str = ""
    state: AgentState = AgentState.IDLE
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    created_by: str = "system"
    correlation_id: str | None = None

    def duration_ms(self) -> float:
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "state": self.state.value,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms(),
            "created_by": self.created_by,
            "correlation_id": self.correlation_id,
        }


class AgentRuntime:
    def __init__(self, agent_id: str, store_id: str) -> None:
        self.agent_id = agent_id
        self.store_id = store_id
        self.state = AgentState.IDLE
        self.execution_mode = ExecutionMode.ASYNC
        self.permissions: List[AgentPermission] = []
        self.tools: List[str] = []
        self.triggers: List[AgentTrigger] = []
        self.workflow: List[WorkflowStep] = []
        self.escalation_rules: List[EscalationRule] = []
        self._memory = AgentMemory(agent_id, store_id)
        self._current_execution: AgentExecution | None = None
        self._execution_history: List[AgentExecution] = []

    def set_permissions(self, permissions: List[Dict[str, Any]]) -> None:
        self.permissions = [
            AgentPermission(resource=p["resource"], actions=p.get("actions", ["read"]))
            for p in permissions
        ]

    def add_trigger(self, event_type: EventType, action: str = "react") -> None:
        self.triggers.append(AgentTrigger(event_type=event_type, action=action))

    def set_workflow(self, steps: List[Dict[str, Any]]) -> None:
        self.workflow = [
            WorkflowStep(
                name=s["name"],
                agent=s["agent"],
                action=s["action"],
                on_success=s.get("on_success"),
                on_error=s.get("on_error"),
                timeout_seconds=s.get("timeout_seconds", 30),
            )
            for s in steps
        ]

    def add_escalation(self, condition: Callable, target_agent: str, reason: str) -> None:
        self.escalation_rules.append(EscalationRule(condition=condition, target_agent=target_agent, reason=reason))

    async def execute(
        self,
        action: str,
        payload: Dict[str, Any],
        created_by: str = "system",
        correlation_id: str | None = None,
    ) -> AgentExecution:
        execution = AgentExecution(
            agent_id=self.agent_id,
            state=AgentState.PROCESSING,
            input_data=payload,
            created_by=created_by,
            correlation_id=correlation_id,
        )
        self._current_execution = execution

        try:
            self.state = AgentState.PROCESSING
            result = await self._execute_action(action, payload)
            execution.output_data = result
            execution.state = AgentState.IDLE
            self.state = AgentState.IDLE

            self._memory.remember(
                key=f"execution_{execution.id}",
                value=result,
                memory_type=MemoryType.EPISODICA,
                tags=["execution"],
                importance=3,
                expires_hours=24,
            )

        except Exception as e:
            execution.error = str(e)
            execution.state = AgentState.ERROR
            self.state = AgentState.ERROR

            await self._check_escalation(execution)

        execution.completed_at = datetime.utcnow()
        self._execution_history.append(execution)
        if len(self._execution_history) > 100:
            self._execution_history = self._execution_history[-50:]

        await event_bus.publish(Event(
            type=EventType.AGENT_RESPONSE,
            payload=execution.to_dict(),
            source_agent=self.agent_id,
            correlation_id=correlation_id,
        ))

        return execution

    async def _execute_action(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "success", "action": action, "result": payload}

    async def _check_escalation(self, execution: AgentExecution) -> None:
        for rule in self.escalation_rules:
            if execution.error and rule.condition(execution.error):
                await event_bus.publish(Event(
                    type=EventType.ORCHESTRATOR_DECISION,
                    payload={
                        "escalation": True,
                        "from_agent": self.agent_id,
                        "target_agent": rule.target_agent,
                        "reason": rule.reason,
                        "execution_id": str(execution.id),
                    },
                    source_agent=self.agent_id,
                    target_agent=rule.target_agent,
                ))

    def get_history(self, limit: int = 10) -> List[AgentExecution]:
        return self._execution_history[-limit:]

    def get_current_state(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "state": self.state.value,
            "execution_mode": self.execution_mode.value,
            "current_execution": self._current_execution.to_dict() if self._current_execution else None,
            "recent_executions": len(self._execution_history),
        }

    def can_execute(self, action: str, resource: str) -> bool:
        for perm in self.permissions:
            if perm.resource == resource or perm.resource == "*":
                return perm.can(action)
        return False

    def on_event(self, event: Event) -> None:
        if event.target_agent and event.target_agent != self.agent_id:
            return

        for trigger in self.triggers:
            if trigger.event_type == event.type:
                asyncio.create_task(self.execute(
                    action=trigger.action,
                    payload=event.payload,
                    correlation_id=event.correlation_id,
                ))


class AgentRegistry:
    def __init__(self) -> None:
        self._runtimes: Dict[str, AgentRuntime] = {}

    def create_runtime(self, agent_id: str, store_id: str, config: Dict[str, Any]) -> AgentRuntime:
        runtime = AgentRuntime(agent_id, store_id)

        if "permissions" in config:
            runtime.set_permissions(config["permissions"])
        if "execution_mode" in config:
            runtime.execution_mode = ExecutionMode(config["execution_mode"])
        if "tools" in config:
            runtime.tools = config["tools"]
        if "triggers" in config:
            for t in config["triggers"]:
                runtime.add_trigger(EventType(t["event"]), t.get("action", "react"))
        if "workflow" in config:
            runtime.set_workflow(config["workflow"])

        self._runtimes[f"{store_id}:{agent_id}"] = runtime
        return runtime

    def get_runtime(self, agent_id: str, store_id: str) -> AgentRuntime | None:
        return self._runtimes.get(f"{store_id}:{agent_id}")

    def get_all_runtimes(self, store_id: str) -> List[AgentRuntime]:
        return [r for k, r in self._runtimes.items() if k.startswith(f"{store_id}:")]

    def remove_runtime(self, agent_id: str, store_id: str) -> bool:
        key = f"{store_id}:{agent_id}"
        if key in self._runtimes:
            del self._runtimes[key]
            return True
        return False


agent_registry = AgentRegistry()