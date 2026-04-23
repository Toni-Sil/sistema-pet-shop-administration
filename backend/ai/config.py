from pathlib import Path
from typing import Dict, Any

from pydantic import BaseModel


class AgentConfig(BaseModel):
    name: str
    model: str
    max_tokens: int = 512
    temperature: float = 0.2
    permissions: list[str] = []
    trigger: list[str] | None = None


# Configuração estática inicial (espelha docs/09-ia-multiagentes-llm.md)
RAW_AGENT_CONFIG: Dict[str, Dict[str, Any]] = {
    "orchestrator": {
        "name": "orchestrator",
        "model": "gpt-4.1-mini",
        "max_tokens": 512,
        "temperature": 0.2,
        "permissions": [
            "route:estoque",
            "route:financeiro",
            "route:agendamento",
            "route:crm",
            "route:relatorios",
            "route:whatsapp",
        ],
    },
    "estoque": {
        "name": "estoque",
        "model": "gpt-4.1-nano",
        "max_tokens": 512,
        "temperature": 0.1,
        "permissions": ["read:products", "read:stock_movements", "read:alerts"],
    },
    "financeiro": {
        "name": "financeiro",
        "model": "gpt-4.1-nano",
        "max_tokens": 768,
        "temperature": 0.1,
        "permissions": [
            "read:sales",
            "read:expenses",
            "read:cashier",
            "read:reports",
        ],
    },
    "agendamento": {
        "name": "agendamento",
        "model": "gpt-4.1-nano",
        "max_tokens": 512,
        "temperature": 0.2,
        "permissions": ["read:appointments", "write:appointments"],
    },
    "crm": {
        "name": "crm",
        "model": "sabia-4",
        "max_tokens": 768,
        "temperature": 0.2,
        "permissions": ["read:clients", "read:pets", "read:pet_history"],
    },
    "relatorios": {
        "name": "relatorios",
        "model": "gpt-4o",
        "max_tokens": 4096,
        "temperature": 0.3,
        "permissions": ["read:all"],
        "trigger": ["manual", "daily_batch"],
    },
    "whatsapp": {
        "name": "whatsapp",
        "model": "sabiazinho-4",
        "max_tokens": 256,
        "temperature": 0.4,
        "permissions": [
            "send_whatsapp_messages",
            "read_basic_client_data",
        ],
    },
}


AGENT_CONFIG: Dict[str, AgentConfig] = {
    name: AgentConfig(**cfg) for name, cfg in RAW_AGENT_CONFIG.items()
}


def get_agent_config(name: str, store_configs: Dict[str, Any] | None = None) -> AgentConfig:
    if name not in AGENT_CONFIG:
        raise KeyError(f"Agente desconhecido: {name}")
    
    config = AGENT_CONFIG[name].model_copy()
    
    # Se houver configuração específica da loja para este agente, sobrescreve
    if store_configs and "ai_agents" in store_configs:
        alias = {
            "estoque": "inventory",
            "financeiro": "financial",
            "agendamento": "scheduling",
            "crm": "crm",
            "orchestrator": "orchestrator",
        }
        key = alias.get(name, name)
        agent_overrides = store_configs["ai_agents"].get(name) or store_configs["ai_agents"].get(key)
        if isinstance(agent_overrides, str):
            config.model = agent_overrides
        elif isinstance(agent_overrides, dict):
            if "model" in agent_overrides and agent_overrides["model"]:
                config.model = agent_overrides["model"]
            if "temperature" in agent_overrides and isinstance(agent_overrides["temperature"], (int, float)):
                config.temperature = float(agent_overrides["temperature"])
                
    return config
