from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.agent import (
    AgentDefinition,
    AgentExecution,
    AgentMemory,
    AgentEvent,
    EscalationLog,
    ApprovalRequest,
)
from ai.hierarchy import hierarchy_registry, CognitiveHierarchy
from ai.event_bus import Event, EventType, event_bus
from ai.memory import AgentMemory as AgentMemoryClass, MemoryType, memory_store
from ai.runtime import AgentState


class AgentSystemService:
    def __init__(self) -> None:
        pass

    async def initialize_store(self, db: Session, store_id: UUID) -> CognitiveHierarchy:
        hierarchy = hierarchy_registry.get_or_create(str(store_id))
        await self._sync_from_database(db, store_id)
        return hierarchy

    async def _sync_from_database(self, db: Session, store_id: UUID) -> None:
        agents = db.query(AgentDefinition).filter(
            AgentDefinition.store_id == store_id,
            AgentDefinition.is_active == True,
        ).all()

        hierarchy = hierarchy_registry.get_or_create(str(store_id))

        for agent in agents:
            if agent.name == "supervisor":
                continue

            runtime = hierarchy.get_agent(agent.name)
            if runtime and agent.permissions:
                runtime.set_permissions(agent.permissions)

    async def process_message(
        self,
        db: Session,
        store_id: UUID,
        message: str,
        context: Dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> Dict[str, Any]:
        hierarchy = await self.initialize_store(db, store_id)

        await self._log_event(db, store_id, "user_message", source_agent="user", payload={"message": message})

        result = await hierarchy.process_request(
            message=message,
            context=context or {},
            user_id=user_id,
        )

        await self._log_event(
            db,
            store_id,
            "agent_response",
            source_agent="supervisor",
            payload=result,
        )

        return result

    async def execute_agent(
        self,
        db: Session,
        store_id: UUID,
        agent_name: str,
        action: str,
        payload: Dict[str, Any],
        user_id: str | None = None,
    ) -> Dict[str, Any]:
        hierarchy = hierarchy_registry.get_or_create(str(store_id))
        agent = hierarchy.get_agent(agent_name)

        if not agent:
            return {"error": f"Agent {agent_name} not found"}

        execution = await agent.execute(
            action=action,
            payload=payload,
            created_by=user_id or "system",
        )

        await self._save_execution(db, store_id, agent_name, execution)

        return execution.to_dict()

    async def get_agent_status(
        self,
        db: Session,
        store_id: UUID,
    ) -> Dict[str, Any]:
        hierarchy = hierarchy_registry.get_or_create(str(store_id))
        return hierarchy.get_hierarchy_status()

    async def get_execution_history(
        self,
        db: Session,
        store_id: UUID,
        agent_name: str | None = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        query = db.query(AgentExecution).filter(AgentExecution.store_id == store_id)

        if agent_name:
            query = query.filter(AgentExecution.agent_name == agent_name)

        executions = query.order_by(AgentExecution.started_at.desc()).limit(limit).all()
        return [e.to_dict() for e in executions]

    async def get_pending_approvals(
        self,
        db: Session,
        store_id: UUID,
    ) -> List[Dict[str, Any]]:
        approvals = db.query(ApprovalRequest).filter(
            ApprovalRequest.store_id == store_id,
            ApprovalRequest.status == "pending",
        ).order_by(ApprovalRequest.created_at.desc()).all()

        return [
            {
                "id": str(a.id),
                "agent_name": a.agent_name,
                "action": a.action,
                "details": a.details,
                "requester": a.requester,
                "created_at": a.created_at.isoformat(),
            }
            for a in approvals
        ]

    async def approve_action(
        self,
        db: Session,
        approval_id: UUID,
        approver: str,
    ) -> Dict[str, Any]:
        approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()

        if not approval:
            return {"error": "Approval not found"}

        approval.status = "approved"
        approval.approver = approver
        approval.approved_at = datetime.utcnow()
        db.commit()

        hierarchy = hierarchy_registry.get_or_create(str(approval.store_id))
        agent = hierarchy.get_agent(approval.agent_name)

        if agent:
            await agent.execute(
                action=approval.action,
                payload=approval.details,
                created_by=approver,
            )

        return {"status": "approved", "approval_id": str(approval_id)}

    async def reject_action(
        self,
        db: Session,
        approval_id: UUID,
        approver: str,
        reason: str,
    ) -> Dict[str, Any]:
        approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()

        if not approval:
            return {"error": "Approval not found"}

        approval.status = "rejected"
        approval.approver = approver
        approval.rejected_at = datetime.utcnow()
        approval.rejection_reason = reason
        db.commit()

        return {"status": "rejected", "approval_id": str(approval_id)}

    async def get_event_history(
        self,
        db: Session,
        store_id: UUID,
        event_type: str | None = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        query = db.query(AgentEvent).filter(AgentEvent.store_id == store_id)

        if event_type:
            query = query.filter(AgentEvent.event_type == event_type)

        events = query.order_by(AgentEvent.timestamp.desc()).limit(limit).all()
        return [e.to_event() for e in events]

    async def trigger_event(
        self,
        db: Session,
        store_id: UUID,
        event_type: str,
        payload: Dict[str, Any],
        source_agent: str = "system",
    ) -> Dict[str, Any]:
        event = Event(
            type=EventType(event_type),
            payload=payload,
            source_agent=source_agent,
        )

        await event_bus.publish(event)

        await self._log_event(
            db,
            store_id,
            event_type,
            source_agent=source_agent,
            payload=payload,
        )

        return {"status": "published", "event_id": str(event.id)}

    async def get_agent_memory(
        self,
        db: Session,
        store_id: UUID,
        agent_name: str,
        memory_type: str | None = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        mem_type = MemoryType(memory_type) if memory_type else None
        entries = memory_store.retrieve(
            memory_type=mem_type,
            agent_id=agent_name,
            store_id=str(store_id),
            limit=limit,
        )

        return [e.to_dict() for e in entries]

    async def _log_event(
        self,
        db: Session,
        store_id: UUID,
        event_type: str,
        source_agent: str | None = None,
        target_agent: str | None = None,
        payload: Dict[str, Any] | None = None,
    ) -> None:
        event = AgentEvent(
            store_id=store_id,
            event_type=event_type,
            source_agent=source_agent,
            target_agent=target_agent,
            payload=payload or {},
        )
        db.add(event)
        db.commit()

    async def _save_execution(
        self,
        db: Session,
        store_id: UUID,
        agent_name: str,
        execution,
    ) -> None:
        db_execution = AgentExecution(
            agent_id=execution.id,
            agent_name=agent_name,
            store_id=store_id,
            state=execution.state,
            action=execution.input_data.get("action", "process"),
            input_data=execution.input_data,
            output_data=execution.output_data,
            error=execution.error,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            created_by=execution.created_by,
            correlation_id=execution.correlation_id,
            duration_ms=int(execution.duration_ms()),
        )
        db.add(db_execution)
        db.commit()


agent_system_service = AgentSystemService()