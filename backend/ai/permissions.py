from __future__ import annotations
"""
AGENT PERMISSIONS & AUTONOMY SYSTEM
- Sandbox de permissões
- Níveis de autorização
- Estados de autonomia
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Set
from enum import Enum
from datetime import datetime


class AutonomyLevel(str, Enum):
    MANUAL = "manual"
    ASSISTED = "assisted"
    SEMI_AUTONOMOUS = "semi_autonomous"
    AUTONOMOUS = "autonomous"


class PermissionAction(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    APPROVE = "approve"
    SEND = "send"
    CREATE = "create"


class PermissionResource(str, Enum):
    CLIENTS = "clients"
    PETS = "pets"
    APPOINTMENTS = "appointments"
    PRODUCTS = "products"
    SALES = "sales"
    FINANCE = "finance"
    MESSAGES = "messages"
    REPORTS = "reports"
    AGENTS = "agents"
    SYSTEM = "system"


class AutonomyMode(BaseModel):
    level: AutonomyLevel
    description: str
    max_transaction_value: float = 0
    requires_approval_for: List[str] = Field(default_factory=list)
    auto_execute_tools: List[str] = Field(default_factory=list)
    blocked_tools: List[str] = Field(default_factory=list)


AUTONOMY_MODES = {
    AutonomyLevel.MANUAL: AutonomyMode(
        level=AutonomyLevel.MANUAL,
        description="Humano executa tudo. IA apenas sugere.",
        max_transaction_value=0,
        requires_approval_for=["*"],
        auto_execute_tools=[],
        blocked_tools=["create_sale", "process_refund", "send_bulk_messages", "create_client"],
    ),
    AutonomyLevel.ASSISTED: AutonomyMode(
        level=AutonomyLevel.ASSISTED,
        description="IA sugere ações. Humano aprova e executa.",
        max_transaction_value=0,
        requires_approval_for=["create_sale", "process_refund", "send_bulk_messages", "create_appointment"],
        auto_execute_tools=["search_client", "check_availability", "get_client_history", "check_stock"],
        blocked_tools=["process_refund", "send_bulk_messages"],
    ),
    AutonomyLevel.SEMI_AUTONOMOUS: AutonomyMode(
        level=AutonomyLevel.SEMI_AUTONOMOUS,
        description="IA executa automaticamente. Aprova humano para ações de risco.",
        max_transaction_value=1000,
        requires_approval_for=["create_sale", "process_refund", "send_bulk_messages"],
        auto_execute_tools=["create_appointment", "search_client", "send_whatsapp", "check_availability"],
        blocked_tools=["process_refund"],
    ),
    AutonomyLevel.AUTONOMOUS: AutonomyMode(
        level=AutonomyLevel.AUTONOMOUS,
        description="IA opera sozinha. Reporta para humano.",
        max_transaction_value=5000,
        requires_approval_for=["process_refund", "send_bulk_messages"],
        auto_execute_tools=["create_appointment", "create_sale", "search_client", "send_whatsapp", "check_stock"],
        blocked_tools=[],
    ),
}


class AgentPermission(BaseModel):
    resource: PermissionResource
    actions: Set[PermissionAction] = Field(default_factory=set)
    conditions: Dict[str, Any] = Field(default_factory=dict)

    def can(self, action: PermissionAction) -> bool:
        return action in self.actions

    def can_within_limit(self, action: PermissionAction, value: float, mode: AutonomyMode) -> bool:
        if not self.can(action):
            return False

        if action == PermissionAction.WRITE or action == PermissionAction.CREATE:
            return value <= mode.max_transaction_value or action in mode.requires_approval_for

        return True


class AgentPermissions(BaseModel):
    agent_id: str
    store_id: str
    permissions: Dict[str, AgentPermission] = Field(default_factory=dict)
    autonomy_level: AutonomyLevel = AutonomyLevel.ASSISTED
    max_value: float = 0
    blocked_resources: Set[str] = Field(default_factory=set)
    allowed_tools: Set[str] = Field(default_factory=set)

    def can_access(self, resource: PermissionResource, action: PermissionAction) -> bool:
        if resource.value in self.blocked_resources:
            return False

        perm = self.permissions.get(resource.value)
        if not perm:
            return False

        return perm.can(action)

    def can_execute_tool(self, tool_name: str, value: float = 0) -> tuple[bool, str | None]:
        mode = AUTONOMY_MODES.get(self.autonomy_level, AUTONOMY_MODES[AutonomyLevel.ASSISTED])

        if tool_name in mode.blocked_tools:
            return False, f"Tool {tool_name} bloqueada para nível {self.autonomy_level.value}"

        if tool_name in mode.requires_approval_for and value > mode.max_transaction_value:
            return False, f"Tool {tool_name} requer aprovação para valores acima de R$ {mode.max_transaction_value}"

        if self.allowed_tools and tool_name not in self.allowed_tools:
            return False, f"Tool {tool_name} não autorizada para este agente"

        return True, None

    def requires_approval(self, tool_name: str) -> bool:
        mode = AUTONOMY_MODES.get(self.autonomy_level, AUTONOMY_MODES[AutonomyLevel.ASSISTED])
        return tool_name in mode.requires_approval_for


class PermissionSandbox:
    DEFAULT_PERMISSIONS = {
        "clients": {
            "resource": PermissionResource.CLIENTS,
            "actions": [PermissionAction.READ, PermissionAction.WRITE],
        },
        "pets": {
            "resource": PermissionResource.PETS,
            "actions": [PermissionAction.READ, PermissionAction.WRITE],
        },
        "appointments": {
            "resource": PermissionResource.APPOINTMENTS,
            "actions": [PermissionAction.READ, PermissionAction.WRITE, PermissionAction.CREATE],
        },
        "products": {
            "resource": PermissionResource.PRODUCTS,
            "actions": [PermissionAction.READ],
        },
        "sales": {
            "resource": PermissionResource.SALES,
            "actions": [PermissionAction.READ, PermissionAction.CREATE],
        },
        "messages": {
            "resource": PermissionResource.MESSAGES,
            "actions": [PermissionAction.READ, PermissionAction.SEND],
        },
    }

    @staticmethod
    def create_for_agent(agent_id: str, store_id: str, role: str = "default") -> AgentPermissions:
        perms = AgentPermissions(
            agent_id=agent_id,
            store_id=store_id,
            autonomy_level=AutonomyLevel.ASSISTED,
        )

        if role == "atendimento":
            perms.autonomy_level = AutonomyLevel.SEMI_AUTONOMOUS
            perms.allowed_tools = {"search_client", "get_client_history", "send_whatsapp", "check_availability", "create_appointment"}

        elif role == "agendamento":
            perms.autonomy_level = AutonomyLevel.SEMI_AUTONOMOUS
            perms.allowed_tools = {"create_appointment", "check_availability", "send_whatsapp"}

        elif role == "financeiro":
            perms.autonomy_level = AutonomyLevel.SEMI_AUTONOMOUS
            perms.allowed_tools = {"create_sale", "search_client", "get_client_history"}
            perms.max_value = 1000

        elif role == "estoque":
            perms.autonomy_level = AutonomyLevel.ASSISTED
            perms.allowed_tools = {"check_stock", "search_client"}

        elif role == "supervisor":
            perms.autonomy_level = AutonomyLevel.AUTONOMOUS
            perms.allowed_tools = set()

        for key, value in PermissionSandbox.DEFAULT_PERMISSIONS.items():
            perms.permissions[key] = AgentPermission(
                resource=value["resource"],
                actions=set(value["actions"]),
            )

        return perms

    @staticmethod
    def check_resource(perms: AgentPermissions, resource: PermissionResource, action: PermissionAction) -> tuple[bool, str | None]:
        if not perms.can_access(resource, action):
            return False, f"Acesso negado: {action.value} em {resource.value}"

        return True, None


class ApprovalRequest(BaseModel):
    id: str
    agent_id: str
    store_id: str
    tool_name: str
    input_data: Dict[str, Any]
    reason: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"
    approver: str | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None


class ApprovalService:
    def __init__(self) -> None:
        self._pending: Dict[str, ApprovalRequest] = {}
        self._history: List[ApprovalRequest] = []

    def request_approval(
        self,
        agent_id: str,
        store_id: str,
        tool_name: str,
        input_data: Dict[str, Any],
        reason: str,
    ) -> ApprovalRequest:
        from uuid import uuid4
        req = ApprovalRequest(
            id=str(uuid4()),
            agent_id=agent_id,
            store_id=store_id,
            tool_name=tool_name,
            input_data=input_data,
            reason=reason,
        )
        self._pending[req.id] = req
        return req

    def approve(self, request_id: str, approver: str) -> bool:
        req = self._pending.get(request_id)
        if not req:
            return False

        req.status = "approved"
        req.approver = approver
        req.approved_at = datetime.utcnow()
        self._history.append(req)
        del self._pending[request_id]
        return True

    def reject(self, request_id: str, approver: str, reason: str) -> bool:
        req = self._pending.get(request_id)
        if not req:
            return False

        req.status = "rejected"
        req.approver = approver
        req.rejection_reason = reason
        self._history.append(req)
        del self._pending[request_id]
        return True

    def get_pending(self, store_id: str) -> List[ApprovalRequest]:
        return [r for r in self._pending.values() if r.store_id == store_id]


approval_service = ApprovalService()


def get_autonomy_mode(level: AutonomyLevel) -> AutonomyMode:
    return AUTONOMY_MODES.get(level, AUTONOMY_MODES[AutonomyLevel.ASSISTED])