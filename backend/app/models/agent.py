from __future__ import annotations

import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class AgentDefinition(Base):
    __tablename__ = "agent_definitions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(PGUUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    model = Column(String(100), nullable=True)
    max_tokens = Column(Integer, default=512)
    temperature = Column(Float, default=0.2)
    permissions = Column(JSON, default=list)
    tools = Column(JSON, default=list)
    triggers = Column(JSON, default=list)
    workflow = Column(JSON, default=list)
    escalation_rules = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=5)
    parent_agent = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_config(self) -> dict:
        return {
            "permissions": self.permissions or [],
            "tools": self.tools or [],
            "triggers": self.triggers or [],
            "workflow": self.workflow or [],
            "escalation_rules": self.escalation_rules or [],
            "execution_mode": "async",
        }


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    store_id = Column(PGUUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    state = Column(String(50), default="idle")
    action = Column(String(100), nullable=False)
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    error = Column(Text, nullable=True)
    execution_mode = Column(String(50), default="async")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=True)
    correlation_id = Column(String(100), nullable=True, index=True)
    duration_ms = Column(Integer, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "store_id": str(self.store_id),
            "state": self.state,
            "action": self.action,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "created_by": self.created_by,
            "correlation_id": self.correlation_id,
        }


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    store_id = Column(PGUUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    memory_type = Column(String(50), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    importance = Column(Integer, default=5)
    embedding = Column(JSON, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(PGUUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    source_agent = Column(String(100), nullable=True)
    target_agent = Column(String(100), nullable=True)
    payload = Column(JSON, default=dict)
    meta = Column(JSON, default=dict)
    correlation_id = Column(String(100), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def to_event(self) -> dict:
        from ai.event_bus import EventType
        return {
            "id": str(self.id),
            "type": self.event_type,
            "payload": self.payload,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
        }


class EscalationLog(Base):
    __tablename__ = "escalation_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(PGUUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    execution_id = Column(PGUUID(as_uuid=True), nullable=True)
    from_agent = Column(String(100), nullable=False)
    to_agent = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    resolved_at = Column(DateTime, nullable=True)
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(PGUUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(JSON, default=dict)
    requester = Column(String(100), nullable=True)
    status = Column(String(50), default="pending")
    approver = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)