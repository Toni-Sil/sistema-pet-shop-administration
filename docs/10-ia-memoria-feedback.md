# 10 - IA: Memória, Feedback e Aprendizado Contínuo

## Objetivo

Definir **como** os agentes de IA do sistema vão:
- Registrar memórias relevantes por loja/usuário.
- Receber feedback de qualidade das respostas.
- Usar essas informações para se **aprimorar ao longo do tempo**, sem treinar modelo do zero.

> Importante: este documento é **instrucional**. Ele descreve comportamento e modelos de dados para serem implementados no futuro, alinhado à visão do projeto e às skills de IA.

---

## Conceitos

### Memória de Agente

Registro persistente de informações que ajudam o agente a responder melhor no futuro, por exemplo:
- Preferências do dono (ex.: forma de ver relatórios, filtros mais usados).
- Regras específicas daquela loja (ex.: horários preferidos de banho/tosa).
- Correções recorrentes (ex.: "não venda medicamento X sem receita").

### Feedback de Resposta

Avaliação explícita de uma interação de IA:
- Usuário marca resposta como **boa** ou **ruim**.
- Opcionalmente adiciona um comentário ("faltou considerar agendamentos de domingo").

Esses dados **não mudam os pesos do modelo**, mas são usados para ajustar prompts, exemplos e filtros.

---

## Estrutura de Dados Proposta

### Tabela `ai_agent_memories`

```sql
CREATE TABLE ai_agent_memories (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id    UUID NOT NULL REFERENCES stores(id),
  user_id     UUID REFERENCES users(id),
  agent_name  VARCHAR(50) NOT NULL,          -- 'estoque', 'financeiro', 'agendamento', etc.
  key         VARCHAR(255) NOT NULL,         -- chave semântica (ex.: 'preferencia_relatorio_diario')
  value       TEXT NOT NULL,                 -- conteúdo da memória
  importance  SMALLINT NOT NULL DEFAULT 1,   -- 1 = baixa, 5 = muito importante
  created_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ai_memories_store_agent
  ON ai_agent_memories (store_id, agent_name);
```

### Tabela `ai_agent_feedback`

```sql
CREATE TABLE ai_agent_feedback (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id     UUID NOT NULL REFERENCES stores(id),
  user_id      UUID REFERENCES users(id),
  agent_name   VARCHAR(50) NOT NULL,
  interaction_id UUID,                      -- id da interação/log, se houver
  rating       SMALLINT NOT NULL,           -- 1 = ruim, 5 = excelente
  comment      TEXT,
  created_at   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ai_feedback_store_agent
  ON ai_agent_feedback (store_id, agent_name);
```

> Observação: as tabelas acima não precisam ser criadas agora; elas servem como guia para a fase de implementação de memória/feedback.

---

## Fluxos de Uso

### 1. Registro de Feedback

1. Frontend exibe, próximo à resposta de IA, botões "👍" e "👎".
2. Usuário clica em um dos botões e, opcionalmente, escreve um comentário.
3. Frontend envia POST para o backend com:

```json
{
  "agent_name": "estoque",
  "rating": 5,
  "comment": "Resposta perfeita, mostrou todos os produtos em falta."
}
```

4. Backend grava em `ai_agent_feedback` associado à loja e ao usuário.

### 2. Criação de Memórias

Memórias podem ser criadas de duas formas:

- **Manual / explícita:** dono configura preferências em tela de configurações (ex.: "sempre mostrar relatórios em período semanal").
- **Automática / derivada de uso:**
  - Exemplo: se o mesmo filtro de relatório é usado muitas vezes, o backend cria uma memória com `key='filtro_relatorio_default'`.

### 3. Uso das Memórias pelos Agentes

Antes de chamar o LLM, o backend:

1. Identifica `store_id`, `user_id` e `agent_name`.
2. Busca memórias relevantes em `ai_agent_memories` (por ex.: top 10 por `importance` e data).
3. Concatena essas memórias em um bloco de contexto para o agente, algo como:

```text
Memórias relevantes para esta loja/usuário:
- Preferência: relatórios financeiros em visão semanal.
- Regra: não agendar banho aos domingos.
- Regra: destacar produtos com validade < 15 dias.
```

4. Envia esse bloco junto ao `SYSTEM_PROMPT` e à pergunta do usuário.

---

## Endpoints Instrucionais

> Estes endpoints são apenas um **esqueleto planejado** para a futura fase de implementação.

### POST `/api/ai/feedback`

- **Descrição:** registrar feedback de resposta de IA.
- **Body (exemplo):**

```json
{
  "agent_name": "financeiro",
  "rating": 2,
  "comment": "Não considerou as vendas de ontem."
}
```

- **Ações esperadas:**
  - Validar `agent_name` contra a configuração de agentes.
  - Descobrir `store_id` e `user_id` a partir do token JWT.
  - Inserir registro em `ai_agent_feedback`.

### GET `/api/ai/memories`

- **Descrição:** listar memórias ativas para um agente e loja.
- **Uso:** backend chama internamente antes de executar o agente.

### POST `/api/ai/memories`

- **Descrição:** criar/atualizar memória relevante (ex.: configurada via painel de preferências).
- **Body (exemplo):**

```json
{
  "agent_name": "agendamento",
  "key": "nao_agendar_domingo",
  "value": "Não permitir novos agendamentos aos domingos.",
  "importance": 5
}
```

---

## Estratégia de Aprendizado Contínuo (sem treinar modelo)

1. **Personalização por loja:**
   - Cada loja tem seu conjunto de memórias; agentes passam a responder de forma alinhada ao jeito de operar daquele pet shop.

2. **Uso de feedback para priorizar memórias:**
   - Respostas mal avaliadas podem gerar novas memórias (ex.: "sempre considerar agendamentos de domingo").
   - As memórias que aparecem em muitas interações podem ter `importance` elevado.

3. **Ajuste iterativo de prompts:**
   - Com o tempo, regras gerais aprendidas via memórias podem ser promovidas para o `SYSTEM_PROMPT` fixo de cada agente, reduzindo tokens de contexto.

4. **Métricas de melhoria:**
   - Taxa de respostas bem avaliadas por agente.
   - Número de memórias por loja que são efetivamente usadas nas chamadas de IA.

---

## Relação com `docs/09-ia-multiagentes-llm.md`

- O documento 09 define **quais agentes existem** e **o que fazem**.
- Este documento 10 define **como eles vão aprender com o uso real**, sem alterar pesos do modelo, usando:
  - Memórias por loja/usuário/agente.
  - Feedback explícito de qualidade.
  - Uso dessas informações como contexto adicional nas próximas chamadas.

Assim, quando o sistema for para produção, já existe um plano claro para que os agentes se tornem, de fato, mais úteis e personalizados ao longo do tempo.
