from __future__ import annotations
"""
TOOLS LAYER - Actions
Responsabilidade: Ações executadas pelos agentes
Separada da lógica de negócio e IA
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List
from sqlalchemy.orm import Session


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str | None = None
    tool_name: str = ""


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Callable] = {}
        self._db: Session | None = None
        self._store_id: str | None = None

    def set_context(self, db: Session, store_id: str) -> None:
        self._db = db
        self._store_id = store_id

    def register_tool(self, name: str, func: Callable) -> None:
        self._tools[name] = func

    def get_tool(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())


class BaseTool:
    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    async def execute(self, **params) -> ToolResult:
        raise NotImplementedError


class SchedulingTools:
    @staticmethod
    async def create_appointment(
        db: Session,
        store_id: str,
        pet_id: str,
        service: str,
        date: str,
        time: str,
        professional: str | None = None,
    ) -> ToolResult:
        try:
            from app.schemas.agendamento import AgendamentoCreate
            
            agendamento = AgendamentoCreate(
                pet_id=pet_id,
                service_id=service,
                date=datetime.fromisoformat(date),
                time=time,
                professional_id=professional,
            )
            
            result = AgendamentoService(db, store_id).create(agendamento)
            return ToolResult(
                success=True,
                data={"appointment_id": str(result.id), "status": "confirmed"},
                tool_name="create_appointment"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name="create_appointment")

    @staticmethod
    async def check_availability(
        db: Session,
        store_id: str,
        date: str,
        service: str | None = None,
    ) -> ToolResult:
        try:
            service_obj = AgendamentoService(db, store_id)
            slots = service_obj.check_availability(date, service)
            return ToolResult(
                success=True,
                data={"available_slots": slots},
                tool_name="check_availability"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name="check_availability")


class MessagingTools:
    @staticmethod
    async def send_whatsapp(
        db: Session,
        store_id: str,
        phone: str,
        message: str,
    ) -> ToolResult:
        try:
            result = WhatsAppService(db, store_id).send_message(phone, message)
            return ToolResult(
                success=True,
                data={"message_id": result.get("id"), "status": "sent"},
                tool_name="send_whatsapp"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name="send_whatsapp")

    @staticmethod
    async def send_template(
        db: Session,
        store_id: str,
        phone: str,
        template: str,
        params: Dict[str, str] | None = None,
    ) -> ToolResult:
        try:
            result = WhatsAppService(db, store_id).send_template(phone, template, params or {})
            return ToolResult(
                success=True,
                data={"message_id": result.get("id")},
                tool_name="send_template"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name="send_template")


class ClientTools:
    @staticmethod
    async def search_client(
        db: Session,
        store_id: str,
        query: str,
    ) -> ToolResult:
        try:
            clients = ClienteService(db, store_id).search(query)
            return ToolResult(
                success=True,
                data={"clients": [{"id": str(c.id), "name": c.nome, "phone": c.telefone} for c in clients]},
                tool_name="search_client"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name="search_client")

    @staticmethod
    async def get_client_history(
        db: Session,
        store_id: str,
        client_id: str,
    ) -> ToolResult:
        try:
            from app.services.cliente_service import ClienteService
            client_svc = ClienteService(db, store_id)
            client = client_svc.get_by_id(client_id)
            
            history = {
                "client": {"id": str(client.id), "name": client.nome},
                "pets": [{"name": p.nome, "species": p.especie} for p in client.pets],
                "total_spent": client.total_gasto,
                "visits": len(client.agendamentos),
            }
            
            return ToolResult(success=True, data=history, tool_name="get_client_history")
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name="get_client_history")


class InventoryTools:
    @staticmethod
    async def check_low_stock(db: Session) -> ToolResult:
        try:
            products = EstoqueService(db).get_low_stock_alerts()
            return ToolResult(
                success=True,
                data={"products": products},
                tool_name="check_low_stock"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name="check_low_stock")


class SalesTools:
    @staticmethod
    async def create_quick_sale(
        db: Session,
        store_id: str,
        client_id: str,
        items: List[Dict[str, Any]],
        payment_method: str,
    ) -> ToolResult:
        try:
            from app.schemas.venda import VendaCreate, ItemVendaCreate
            
            venda = VendaCreate(
                client_id=client_id,
                payment_method=payment_method,
                items=[
                    ItemVendaCreate(
                        product_id=item["product_id"],
                        quantity=item["quantity"],
                        unit_price=item["price"]
                    )
                    for item in items
                ]
            )
            
            result = VendaService(db, store_id).create(venda)
            return ToolResult(
                success=True,
                data={"sale_id": str(result.id), "total": result.total},
                tool_name="create_quick_sale"
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), tool_name="create_quick_sale")


tool_registry = ToolRegistry()


def get_available_tools() -> Dict[str, Callable]:
    return {
        "create_appointment": SchedulingTools.create_appointment,
        "check_availability": SchedulingTools.check_availability,
        "send_whatsapp": MessagingTools.send_whatsapp,
        "send_template": MessagingTools.send_template,
        "search_client": ClientTools.search_client,
        "get_client_history": ClientTools.get_client_history,
        "check_low_stock": InventoryTools.check_low_stock,
        "create_quick_sale": SalesTools.create_quick_sale,
    }