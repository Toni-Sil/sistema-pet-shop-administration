from __future__ import annotations
"""
TOOL EXECUTOR - Executor de tools com contrato e permissões
Executa tools usando o contrato padronizado com validação e permissões
"""

import time
from typing import Any, Dict, Optional
from datetime import datetime

from ai.tools_contract import (
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolResultStatus,
    get_tool_contract,
    validate_tool_input,
    TOOL_CONTRACTS,
)
from ai.permissions import (
    AgentPermissions,
    PermissionSandbox,
    AutonomyLevel,
    approval_service,
    get_autonomy_mode,
)
from ai.event_bus import Event, EventType, event_bus


class ToolExecutor:
    def __init__(self, db=None, store_id: str = "") -> None:
        self.db = db
        self.store_id = store_id

    def set_permissions(self, permissions: AgentPermissions) -> None:
        self.permissions = permissions

    async def execute(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResponse:
        start_time = time.time()

        contract = get_tool_contract(request.tool)
        if not contract:
            return ToolExecutionResponse(
                status=ToolResultStatus.ERROR,
                tool=request.tool,
                error=f"Tool {request.tool} não encontrada",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        valid, error = validate_tool_input(request.tool, request.input)
        if not valid:
            return ToolExecutionResponse(
                status=ToolResultStatus.ERROR,
                tool=request.tool,
                error=error,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        can_execute, perm_error = self.permissions.can_execute_tool(
            request.tool,
            request.input.get("amount", 0),
        )
        if not can_execute:
            if contract.requires_approval:
                return await self._request_approval_and_execute(request, perm_error, start_time)
            else:
                return ToolExecutionResponse(
                    status=ToolResultStatus.ERROR,
                    tool=request.tool,
                    error=perm_error,
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

        if contract.requires_approval and not contract.dangerous:
            return await self._request_approval_and_execute(request, "Requer aprovação", start_time)

        return await self._execute_tool(request, start_time)

    async def _request_approval_and_execute(
        self,
        request: ToolExecutionRequest,
        reason: str,
        start_time: float,
    ) -> ToolExecutionResponse:
        approval_req = approval_service.request_approval(
            agent_id=request.agent_id,
            store_id=self.store_id,
            tool_name=request.tool,
            input_data=request.input,
            reason=reason,
        )

        await event_bus.publish(Event(
            type=EventType.ORCHESTRATOR_DECISION,
            payload={
                "type": "approval_request",
                "request_id": approval_req.id,
                "tool": request.tool,
                "input": request.input,
                "reason": reason,
            },
            source_agent=request.agent_id,
            target_agent="supervisor",
        ))

        return ToolExecutionResponse(
            status=ToolResultStatus.PENDING,
            tool=request.tool,
            output={"approval_request_id": approval_req.id, "message": "Aguardando aprovação"},
            execution_time_ms=int((time.time() - start_time) * 1000),
        )

    async def _execute_tool(
        self,
        request: ToolExecutionRequest,
        start_time: float,
    ) -> ToolExecutionResponse:
        result = await self._dispatch_tool(request.tool, request.input, request.context)

        execution_time = int((time.time() - start_time) * 1000)

        await event_bus.publish(Event(
            type=EventType.AGENT_RESPONSE,
            payload={
                "tool": request.tool,
                "result": result,
                "agent_id": request.agent_id,
            },
            source_agent=request.agent_id,
            correlation_id=request.correlation_id,
        ))

        return ToolExecutionResponse(
            status=ToolResultStatus.SUCCESS if result.get("success") else ToolResultStatus.ERROR,
            tool=request.tool,
            output=result.get("data", {}),
            error=result.get("error"),
            execution_time_ms=execution_time,
        )

    async def _dispatch_tool(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        if tool_name == "create_appointment":
            return await self._create_appointment(input_data, context)
        elif tool_name == "check_availability":
            return await self._check_availability(input_data, context)
        elif tool_name == "send_whatsapp":
            return await self._send_whatsapp(input_data, context)
        elif tool_name == "search_client":
            return await self._search_client(input_data, context)
        elif tool_name == "get_client_history":
            return await self._get_client_history(input_data, context)
        elif tool_name == "create_client":
            return await self._create_client(input_data, context)
        elif tool_name == "check_stock":
            return await self._check_stock(input_data, context)
        elif tool_name == "create_sale":
            return await self._create_sale(input_data, context)
        else:
            return {"success": False, "error": f"Tool {tool_name} não implementada"}

    async def _create_appointment(self, input_data: Dict, context: Dict) -> Dict:
        return {
            "success": True,
            "data": {
                "appointment_id": "generated-id",
                "status": "confirmed",
                "confirmation_sent": True,
            },
        }

    async def _check_availability(self, input_data: Dict, context: Dict) -> Dict:
        date = input_data.get("date", "")
        return {
            "success": True,
            "data": {
                "available_slots": ["09:00", "10:00", "11:00", "14:00", "15:00"],
                "fully_booked": False,
            },
        }

    async def _send_whatsapp(self, input_data: Dict, context: Dict) -> Dict:
        return {
            "success": True,
            "data": {
                "message_id": "msg-id",
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat(),
            },
        }

    async def _search_client(self, input_data: Dict, context: Dict) -> Dict:
        return {
            "success": True,
            "data": {
                "clients": [],
                "count": 0,
            },
        }

    async def _get_client_history(self, input_data: Dict, context: Dict) -> Dict:
        return {
            "success": True,
            "data": {
                "client": {},
                "pets": [],
                "recent_appointments": [],
                "total_spent": 0,
            },
        }

    async def _create_client(self, input_data: Dict, context: Dict) -> Dict:
        return {
            "success": True,
            "data": {
                "client_id": "new-client-id",
                "created": True,
            },
        }

    async def _check_stock(self, input_data: Dict, context: Dict) -> Dict:
        return {
            "success": True,
            "data": {
                "low_stock_items": [],
                "critical_items": [],
            },
        }

    async def _create_sale(self, input_data: Dict, context: Dict) -> Dict:
        return {
            "success": True,
            "data": {
                "sale_id": "sale-id",
                "total": input_data.get("items", [{}])[0].get("quantity", 0) * 100,
                "receipt_url": None,
            },
        }


class AgentToolExecutor:
    @staticmethod
    def create_for_agent(agent_id: str, store_id: str, role: str = "default") -> ToolExecutor:
        executor = ToolExecutor(store_id=store_id)
        permissions = PermissionSandbox.create_for_agent(agent_id, store_id, role)
        executor.set_permissions(permissions)
        return executor


executor = ToolExecutor()