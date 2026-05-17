from __future__ import annotations
"""
TOOL CONTRACT - Contrato Padronizado de Ferramentas
Todo agente usa tools com este contrato padronizado
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime


class ToolCategory(str, Enum):
    SCHEDULING = "scheduling"
    MESSAGING = "messaging"
    CLIENT = "client"
    INVENTORY = "inventory"
    SALES = "sales"
    PAYMENT = "payment"
    NOTIFICATION = "notification"
    ANALYTICS = "analytics"
    SYSTEM = "system"


class ToolInputField(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    validation: Dict[str, Any] | None = None


class ToolInputSchema(BaseModel):
    type: str = "object"
    fields: Dict[str, ToolInputField] = {}


class ToolOutputSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any] = {}


class ToolResultStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PARTIAL = "partial"


class ToolExecutionRequest(BaseModel):
    tool: str = Field(..., description="Nome da ferramenta")
    input: Dict[str, Any] = Field(default_factory=dict, description="Dados de entrada")
    agent_id: str = Field(..., description="ID do agente que executa")
    correlation_id: str | None = Field(None, description="ID de correlação")
    context: Dict[str, Any] = Field(default_factory=dict, description="Contexto adicional")


class ToolExecutionResponse(BaseModel):
    status: ToolResultStatus
    tool: str
    output: Dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    execution_time_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ToolDefinition(BaseModel):
    name: str
    category: ToolCategory
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    requires_approval: bool = False
    requires_confirmation: bool = False
    dangerous: bool = False
    rate_limit: int = 10
    timeout_seconds: int = 30
    retry_on_error: bool = False
    max_retries: int = 2


TOOL_CONTRACTS: Dict[str, ToolDefinition] = {
    "create_appointment": ToolDefinition(
        name="create_appointment",
        category=ToolCategory.SCHEDULING,
        description="Cria um novo agendamento para o pet",
        input_schema={
            "type": "object",
            "fields": {
                "client_id": {"type": "string", "description": "ID do cliente", "required": True},
                "pet_id": {"type": "string", "description": "ID do pet", "required": True},
                "service": {"type": "string", "description": "Serviço (banho, tosa, consulta)", "required": True},
                "date": {"type": "string", "description": "Data ISO 8601", "required": True},
                "time": {"type": "string", "description": "Horário (HH:MM)", "required": True},
                "professional_id": {"type": "string", "description": "ID do profissional", "required": False},
                "notes": {"type": "string", "description": "Observações", "required": False},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "appointment_id": {"type": "string"},
                "status": {"type": "string"},
                "confirmation_sent": {"type": "boolean"},
            },
        },
        requires_approval=False,
        requires_confirmation=True,
    ),

    "check_availability": ToolDefinition(
        name="check_availability",
        category=ToolCategory.SCHEDULING,
        description="Verifica horários disponíveis para agendamento",
        input_schema={
            "type": "object",
            "fields": {
                "date": {"type": "string", "description": "Data para verificar", "required": True},
                "service": {"type": "string", "description": "Serviço específico", "required": False},
                "professional_id": {"type": "string", "description": "Profissional específico", "required": False},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "available_slots": {"type": "array", "items": {"type": "string"}},
                "fully_booked": {"type": "boolean"},
            },
        },
        requires_approval=False,
    ),

    "send_whatsapp": ToolDefinition(
        name="send_whatsapp",
        category=ToolCategory.MESSAGING,
        description="Envia mensagem via WhatsApp",
        input_schema={
            "type": "object",
            "fields": {
                "phone": {"type": "string", "description": "Número com país", "required": True},
                "message": {"type": "string", "description": "Texto da mensagem", "required": True},
                "template_id": {"type": "string", "description": "ID do template", "required": False},
                "variables": {"type": "object", "description": "Variáveis do template", "required": False},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "message_id": {"type": "string"},
                "status": {"type": "string"},
                "sent_at": {"type": "string"},
            },
        },
        requires_approval=False,
    ),

    "search_client": ToolDefinition(
        name="search_client",
        category=ToolCategory.CLIENT,
        description="Busca cliente por nome, telefone ou email",
        input_schema={
            "type": "object",
            "fields": {
                "query": {"type": "string", "description": "Termo de busca", "required": True},
                "limit": {"type": "integer", "description": "Limite de resultados", "required": False, "default": 10},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "clients": {"type": "array", "items": {"type": "object"}},
                "count": {"type": "integer"},
            },
        },
        requires_approval=False,
    ),

    "get_client_history": ToolDefinition(
        name="get_client_history",
        category=ToolCategory.CLIENT,
        description="Retorna histórico completo do cliente",
        input_schema={
            "type": "object",
            "fields": {
                "client_id": {"type": "string", "description": "ID do cliente", "required": True},
                "include_pets": {"type": "boolean", "description": "Incluir pets", "required": False, "default": True},
                "include_appointments": {"type": "boolean", "description": "Incluir agendamentos", "required": False, "default": True},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "client": {"type": "object"},
                "pets": {"type": "array"},
                "recent_appointments": {"type": "array"},
                "total_spent": {"type": "number"},
            },
        },
        requires_approval=False,
    ),

    "create_client": ToolDefinition(
        name="create_client",
        category=ToolCategory.CLIENT,
        description="Cria novo cliente",
        input_schema={
            "type": "object",
            "fields": {
                "name": {"type": "string", "description": "Nome completo", "required": True},
                "phone": {"type": "string", "description": "Telefone", "required": True},
                "email": {"type": "string", "description": "Email", "required": False},
                "address": {"type": "string", "description": "Endereço", "required": False},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "client_id": {"type": "string"},
                "created": {"type": "boolean"},
            },
        },
        requires_approval=False,
    ),

    "check_stock": ToolDefinition(
        name="check_stock",
        category=ToolCategory.INVENTORY,
        description="Verifica produtos com estoque baixo",
        input_schema={
            "type": "object",
            "fields": {
                "category": {"type": "string", "description": "Filtrar por categoria", "required": False},
                "threshold": {"type": "integer", "description": "Limite mínimo", "required": False, "default": 10},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "low_stock_items": {"type": "array"},
                "critical_items": {"type": "array"},
            },
        },
        requires_approval=False,
    ),

    "create_sale": ToolDefinition(
        name="create_sale",
        category=ToolCategory.SALES,
        description="Cria uma venda",
        input_schema={
            "type": "object",
            "fields": {
                "client_id": {"type": "string", "description": "ID do cliente", "required": True},
                "items": {"type": "array", "description": "Itens da venda", "required": True},
                "payment_method": {"type": "string", "description": "Método de pagamento", "required": True},
                "discount_percent": {"type": "number", "description": "Desconto %", "required": False},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "sale_id": {"type": "string"},
                "total": {"type": "number"},
                "receipt_url": {"type": "string"},
            },
        },
        requires_approval=True,
        requires_confirmation=True,
    ),

    "process_refund": ToolDefinition(
        name="process_refund",
        category=ToolCategory.PAYMENT,
        description="Processa estorno de pagamento",
        input_schema={
            "type": "object",
            "fields": {
                "sale_id": {"type": "string", "description": "ID da venda", "required": True},
                "amount": {"type": "number", "description": "Valor do estorno", "required": True},
                "reason": {"type": "string", "description": "Motivo", "required": True},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "refund_id": {"type": "string"},
                "status": {"type": "string"},
                "processed_at": {"type": "string"},
            },
        },
        requires_approval=True,
        dangerous=True,
    ),

    "send_bulk_messages": ToolDefinition(
        name="send_bulk_messages",
        category=ToolCategory.MESSAGING,
        description="Envia mensagens em massa",
        input_schema={
            "type": "object",
            "fields": {
                "recipients": {"type": "array", "description": "Lista de phones", "required": True},
                "message": {"type": "string", "description": "Mensagem", "required": True},
                "campaign_name": {"type": "string", "description": "Nome da campanha", "required": False},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "sent": {"type": "integer"},
                "failed": {"type": "integer"},
                "campaign_id": {"type": "string"},
            },
        },
        requires_approval=True,
    ),
}


def get_tool_contract(tool_name: str) -> ToolDefinition | None:
    return TOOL_CONTRACTS.get(tool_name)


def validate_tool_input(tool_name: str, input_data: Dict[str, Any]) -> tuple[bool, str | None]:
    contract = get_tool_contract(tool_name)
    if not contract:
        return False, f"Tool {tool_name} não encontrada"

    for field_name, field_def in contract.input_schema.get("fields", {}).items():
        if field_def.required and field_name not in input_data:
            return False, f"Campo obrigatório ausente: {field_name}"

    return True, None


def get_tools_by_category(category: ToolCategory) -> List[ToolDefinition]:
    return [t for t in TOOL_CONTRACTS.values() if t.category == category]


def get_tools_requiring_approval() -> List[ToolDefinition]:
    return [t for t in TOOL_CONTRACTS.values() if t.requires_approval]


def get_dangerous_tools() -> List[ToolDefinition]:
    return [t for t in TOOL_CONTRACTS.values() if t.dangerous]