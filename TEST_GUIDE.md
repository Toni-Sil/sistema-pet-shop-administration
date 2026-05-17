# Guia de Teste - Sistema Agentic

## 1. Instalação

### Dependências do Backend
```bash
cd backend
pip install -r requirements.txt
```

Novas dependências:
- `celery` - Workers assíncronos
- `redis` - Filas de eventos

### Infraestrutura Necessária
```bash
# Redis (filas e eventos)
docker run -d -p 6379:6379 redis:alpine

# PostgreSQL (já deve estar rodando)
# executar migração:
alembic upgrade head
```

### Migração do Banco
```bash
cd backend
alembic upgrade head
```

Cria as tabelas:
- `agent_definitions`
- `agent_executions`
- `agent_memories`
- `agent_events`
- `escalation_logs`
- `approval_requests`

---

## 2. Testes via API

### 2.1 Health Check
```bash
curl http://localhost:8000/api/v1/ai/operations/health
```

**Esperado:** `{"status":"operational","active_conversations":0,"llm_connected":false}`

### 2.2 Dashboard Operacional
```bash
curl http://localhost:8000/api/v1/ai/operations/dashboard
```

**Esperado:**
```json
{
  "summary": {
    "active_conversations": 0,
    "waiting_approval": 0,
    "by_agent": {},
    "by_intent": {},
    "health": "idle"
  },
  "agents": [...]
}
```

### 2.3 Processar Mensagem (WhatsApp)
```bash
curl -X POST http://localhost:8000/api/v1/ai/operations/message \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5511999999999",
    "message": "Quero agendar um banho para meu dog",
    "source": "whatsapp"
  }'
```

**Esperado:** Resposta do agente de atendimento com intent detectada

### 2.4 Status dos Agentes
```bash
curl http://localhost:8000/api/v1/ai/operations/agents/status
```

**Esperado:** Lista de agentes com seus estados

### 2.5 Eventos Recentes
```bash
curl http://localhost:8000/api/v1/ai/operations/events/recent?limit=10
```

**Esperado:** Lista de eventos do Event Bus

### 2.6 Testar Contrato de Ferramentas
```python
from ai.tools_contract import get_tool_contract, validate_tool_input

# Verificar tool existe
tool = get_tool_contract("create_appointment")
print(tool.name, tool.category, tool.requires_approval)

# Validar input
valid, error = validate_tool_input("create_appointment", {
    "client_id": "123",
    "pet_id": "456",
    "service": "banho",
    "date": "2024-01-15",
    "time": "14:00"
})
print(f"Valid: {valid}, Error: {error}")
```

### 2.7 Testar Permissões e Autonomia
```python
from ai.permissions import (
    PermissionSandbox, AutonomyLevel, get_autonomy_mode
)

# Criar permissions para agente de atendimento
perms = PermissionSandbox.create_for_agent(
    agent_id="atendimento",
    store_id="store-123",
    role="atendimento"
)

print(f"Autonomy: {perms.autonomy_level}")
print(f"Max Value: {perms.max_value}")
print(f"Allowed Tools: {perms.allowed_tools}")

# Verificar se pode executar tool
can, error = perms.can_execute_tool("create_appointment")
print(f"Can execute: {can}, Error: {error}")

can, error = perms.can_execute_tool("process_refund")
print(f"Can execute refund: {can}, Error: {error}")

# Verificar modo de autonomia
mode = get_autonomy_mode(AutonomyLevel.SEMI_AUTONOMOUS)
print(f"Max transaction: {mode.max_transaction_value}")
```

### 2.8 Testar Tool Executor
```python
from ai.tool_executor import AgentToolExecutor
from ai.tools_contract import ToolExecutionRequest

executor = AgentToolExecutor.create_for_agent(
    agent_id="atendimento",
    store_id="store-123",
    role="atendimento"
)

request = ToolExecutionRequest(
    tool="create_appointment",
    input={
        "client_id": "123",
        "pet_id": "456",
        "service": "banho",
        "date": "2024-01-15",
        "time": "14:00"
    },
    agent_id="atendimento",
    correlation_id="test-123"
)

import asyncio
result = asyncio.run(executor.execute(request))
print(f"Status: {result.status}, Output: {result.output}")
```

### 2.9 Testar Fluxo Operacional
```python
from ai.operations import operational_service, MessageSource
from openai import AsyncOpenAI
import asyncio

# Configurar LLM (necessário para classificação de intent)
flow = operational_service.get_flow("store-123")
flow.set_llm(AsyncOpenAI())  # Ou cliente real com API key

# Processar mensagem
result = asyncio.run(operational_service.process_message(
    store_id="store-123",
    phone="5511999999999",
    message="Quero agendar banho para o Thor",
    source=MessageSource.WHATSAPP
))

print(f"Result: {result}")
```

---

## 3. Teste de Integração

### 3.1 Fluxo Completo: Agendamento via WhatsApp
```
1. WhatsApp recebe: "Quero agendar um banho"
2. Event: mensagem_enviada
3. Intent Classifier: -> "agendamento"
4. Supervisor: -> roteia para "agendamento"
5. Agendamento Agent: -> coleta informações
6. Tools: check_availability -> available_slots
7. Memory: recuerda interação
8. humano supervisiona no painel
```

### 3.2 Fluxo com Aprovação
```
1. Agente tenta: create_sale (valor > R$ 1000)
2. Tool Executor: detecta requires_approval
3. ApprovalRequest criado
4. Event: orchestrator_decision -> "requires_approval"
5. Painel: humano aprova ou rejeita
6. Se aprovado: tool executa
```

---

## 4. Variáveis de Ambiente Necessárias

```bash
# .env
OPENAI_API_KEY=sk-...
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://...
```

---

## 5. Troubleshooting

### Problema: "Tool not found"
- Verificar se tool está em `TOOL_CONTRACTS` em `ai/tools_contract.py`

### Problema: "Permission denied"
- Verificar `AgentPermissions` do agente
- Verificar se tool está em `allowed_tools` ou `blocked_tools`

### Problema: "Requires approval"
- Esperado para tools perigosas (process_refund, send_bulk_messages)
- Usar painel para aprovar: `POST /ai/operations/approval`

### Problema: Redis connection
- Verificar se Redis está rodando: `docker ps` ou `redis-cli ping`

---

## 6. Endpoints Summary

| Endpoint | Descrição |
|----------|-----------|
| `GET /ai/operations/health` | Health do sistema |
| `GET /ai/operations/dashboard` | Resumo operacional |
| `GET /ai/operations/conversations` | Conversas ativas |
| `GET /ai/operations/agents/status` | Status dos agentes |
| `GET /ai/operations/events/recent` | Eventos do Event Bus |
| `POST /ai/operations/message` | Processar mensagem |
| `POST /ai/operations/approval` | Aprovar/rejeitar |
| `GET /ai/v2/status` | Status V2 |
| `POST /ai/v2/chat` | Chat com hierarquia |
| `GET /ai/v2/memory/{agent}` | Memória do agente |

---

## 7. Próximos Passos

1. ✅ Event Bus - funcionando
2. ✅ Memory Layer - funcionando
3. ✅ Runtime de Agentes - funcionando
4. ✅ Hierarquia Cognitiva - funcionando
5. ✅ Contrato de Tools - funcionando
6. ✅ Permissões/Autonomia - funcionando
7. 🔄 Testar com LLM real (OpenAI/Gemini)
8. 🔄 Integrar WhatsApp real
9. 🔄 Dashboard frontend