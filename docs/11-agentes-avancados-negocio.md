# 11 - Agentes Avançados de Negócio

## Objetivo

Definir agentes de IA adicionais que trazem valor real para donos de pet shop e para a operação da plataforma, sem focar em monitoramento de infraestrutura.

> Este documento é instrucional. Ele descreve comportamento e interfaces esperadas desses agentes para orientar a implementação futura.

Agentes contemplados aqui:
- Agente de Campanhas & Marketing
- Agente de Simulação de Preços e Pacotes ("what-if")
- Agente de Onboarding e Suporte Interno
- Agente de QA de Regras de Negócio
- Agente de Migração/Implantação
- Agente de Custo de IA

---

## 1. Agente de Campanhas & Marketing

### Visão Geral

Ajuda o dono do pet shop a criar campanhas de relacionamento e aumento de receita usando a base de clientes, pets e histórico de serviços.

### Entradas

- Filtros de público alvo (ex.: "pets idosos", "clientes que só fazem banho").
- Período de análise (ex.: últimos 6 meses).
- Canal desejado (WhatsApp, e-mail, SMS).

### Saídas

- Lista de clientes/pets alvo (ids/tutores/pets) para a campanha.
- Sugestões de ofertas ou pacotes (ex.: banho+tosa, check-up, vacina).
- Texto da campanha em linguagem natural, adaptado ao canal.

### Fontes de Dados

- `clients`, `pets`, `appointments`, `sales`, `pet_notes`, `pet_vaccines`.

### Integração com outros módulos

- Pode disparar campanhas via:
  - Agente de WhatsApp (mensagens em lote ou individuais com personalização).
  - Exportação de listas para CSV (caso o dono use outro canal). 

### Regras

- Respeitar preferências de comunicação (opt-out).
- Evitar spam: sugerir frequência máxima (ex.: 1 campanha por semana por cliente).

---

## 2. Agente de Simulação de Preços e Pacotes ("what-if")

### Visão Geral

Permite ao dono simular alterações de preços e pacotes e ver impacto estimado em faturamento, ticket médio e margem.

### Entradas

- Alterações propostas, por exemplo:
  - `+10%` no preço do banho.
  - Novo pacote "banho mensal + tosa trimestral" com preço X.
- Período base para análise (ex.: últimos 3 meses).

### Saídas

- Estimativa de:
  - Variação no ticket médio.
  - Faturamento mensal estimado.
  - Margem de contribuição dos principais serviços/produtos.
- Explicação textual simples ("Se o comportamento dos clientes se mantiver, sua receita mensal tende a...").

### Fontes de Dados

- `sales`, `sale_items`, `services`, possivelmente agrupados por tipo de serviço/produto.

### Regras

- Sempre deixar claro que é **simulação**, baseada em histórico, não garantia.
- Permitir salvar cenários simulados para comparar depois.

---

## 3. Agente de Onboarding e Suporte Interno

### Visão Geral

Um "tutor" embutido no sistema para treinar funcionários novos e responder dúvidas sobre como usar o sistema.

### Entradas

- Perguntas em linguagem natural, ex.:
  - "como abro o caixa?"
  - "como remarcar um banho?"
  - "como cadastrar um produto por peso?"

### Saídas

- Passo a passo em linguagem simples.
- Links/atalhos para as telas relevantes (ex.: `/app/pdv`, `/app/estoque`).

### Fontes de Conhecimento

- Documentação interna (trechos de `docs/*.md`).
- Descrições de telas e fluxos (futuro `docs/ui-*`).

### Integração

- Acessível via botão de ajuda (ex.: "Ajuda" ou F1) em qualquer tela.
- Pode usar contexto da página atual para respostas mais precisas.

---

## 4. Agente de QA de Regras de Negócio

### Visão Geral

Auxilia você (dev/arquitetura) a verificar se o código e endpoints estão alinhados com as especificações SDD.

### Entradas

- Trechos de documentação (`docs/01-modulo-estoque.md`, `docs/02-modulo-financeiro.md`, etc.).
- Lista de endpoints/arquivos de código (extraídos via script).

### Saídas

- Lista de gaps, por exemplo:
  - "Spec exige endpoint GET /api/stock/expiring, não encontrado no código".
  - "Regra 'saldo negativo bloqueado' não está claramente coberta em testes".
- Sugestões de testes unitários/integrados.

### Uso

- Rodado manualmente antes de releases grandes.
- Integrável em pipeline de CI para comentários automáticos em PRs.

---

## 5. Agente de Migração/Implantação

### Visão Geral

Facilita onboarding de novos pet shops que vêm de planilhas ou outros ERPs.

### Entradas

- Arquivos CSV/Excel com dados de clientes, pets, produtos, histórico básico.
- Informações de origem (ex.: "MarketUP", "planilha Excel").

### Saídas

- Mapeamento sugerido de colunas → campos do sistema (ex.: "Cliente" → `clients.name`, "Animal" → `pets.name`).
- Relatório de qualidade dos dados (linhas com problemas, campos obrigatórios faltando).
- Scripts ou instruções de importação.

### Regras

- Nunca importar automaticamente sem revisão humana.
- Marcar registros problemáticos para correção manual.

---

## 6. Agente de Custo de IA

### Visão Geral

Monitora e explica o custo de uso de LLMs por loja/plano, ajudando a manter a margem saudável e a evitar abuso.

### Entradas

- Logs de chamadas de IA por `store_id`, `agent_name`, modelo e tokens (a serem registrados no futuro).
- Tabela de preços vigente por modelo (input/output).

### Saídas

- Relatórios como:
  - Custo mensal de IA por cliente.
  - Custo por agente (estoque, financeiro, relatórios, etc.).
  - Sugestões de otimização (ex.: "Agente X poderia usar modelo Nano", "Relatórios poderiam ser executados 1x/dia").
- Alertas se o custo de IA se aproximar de um limite definido para o plano.

### Integração

- Painel interno para você (admin) e, opcionalmente, visão resumida para o cliente em planos Enterprise.
- Integração com a estratégia de roteamento (ex.: limitar uso de modelo premium quando custo atingir certo patamar).

---

## Relação com outros documentos

- **docs/09-ia-multiagentes-llm.md**: define os agentes principais (estoque, financeiro, agendamento, CRM, relatórios, WhatsApp) e a estratégia de custo/roteamento.
- **docs/10-ia-memoria-feedback.md**: define como agentes aprendem com memórias e feedback.
- **docs/11-agentes-avancados-negocio.md (este arquivo)**: descreve agentes de negócio adicionais que podem ser implementados depois que o núcleo do sistema estiver estável.

Esses agentes avançados são opcionais, mas oferecidos como caminho de evolução do produto para aumentar receita do cliente final e eficiência da operação da plataforma.
