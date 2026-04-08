# 07 - Roadmap e Sprints

**Inicio:** Abril 2026 | **MVP previsto:** Junho 2026

---

## Visao Geral das Fases

```
Fase 1 - MVP (Semanas 1-6)     Estoque + Financeiro + PDV
Fase 2 - Servicos (Sem. 7-12)  Agendamento + WhatsApp
Fase 3 - CRM (Sem. 10-13)      Tutores + Pets + Historico
Fase 4 - IA (Sem. 14-20)       Relatorios inteligentes
```

---

## FASE 1: MVP - Modulo Base

### Sprint 1 (Semana 1-2): Fundacao
**Objetivo:** Projeto rodando localmente com auth

- [ ] Setup repositorio + estrutura de pastas
- [ ] Docker Compose (backend + frontend + postgres + redis)
- [ ] FastAPI base com health check
- [ ] Migrations Alembic: stores, users
- [ ] Auth: login, JWT, refresh token
- [ ] MFA: TOTP setup e validacao
- [ ] React + Vite + Tailwind + shadcn setup
- [ ] Tela de login + dashboard vazio
- [ ] Deploy inicial no Dokploy (ambiente de dev)

**Entrega:** Sistema funcionando com login e MFA

---

### Sprint 2 (Semana 3-4): Modulo de Estoque
**Objetivo:** CRUD de produtos + movimentacoes funcionando

- [ ] Migration: products, stock_movements
- [ ] Endpoints: GET/POST/PUT/DELETE /api/products
- [ ] Endpoints: POST /api/stock/entry, /api/stock/exit
- [ ] Endpoint: GET /api/stock/alerts
- [ ] Endpoint: GET /api/stock/expiring
- [ ] Tela: Lista de produtos com filtros
- [ ] Tela: Formulario de produto (add/edit)
- [ ] Tela: Entrada de estoque
- [ ] Componente: Painel de alertas (estoque baixo + vencimento)
- [ ] Testes unitarios dos servicos de estoque

**Entrega:** Estoque completo e funcional

---

### Sprint 3 (Semana 5-6): Modulo Financeiro + PDV
**Objetivo:** Vender produto com Pix e ver relatorio

- [ ] Migration: sales, sale_items, expenses, cashier_sessions
- [ ] Integracao Asaas: criar cobranca Pix, webhook
- [ ] Endpoints: POST /api/sales, GET /api/sales
- [ ] Endpoints: POST /api/payments/pix
- [ ] Endpoints: /api/cashier (abrir/fechar)
- [ ] Endpoints: /api/bills/payable
- [ ] Endpoints: GET /api/dashboard/financial
- [ ] Tela: PDV (selecionar produtos, gerar Pix, finalizar)
- [ ] Tela: Dashboard financeiro com graficos
- [ ] Tela: Contas a pagar
- [ ] Componente: QR Code Pix
- [ ] Job: Verificar pagamentos pendentes
- [ ] Exportacao relatorio CSV

**Entrega:** MVP completo - vender com Pix e ver financeiro

---

### Sprint 4 (Semana 7): Ajustes MVP + Deploy Producao
**Objetivo:** MVP estavel e no ar para beta testers

- [ ] Testes de integracao (fluxo completo de venda)
- [ ] Correcao de bugs encontrados
- [ ] Setup GitHub Actions (CI: testes automaticos)
- [ ] Deploy producao no Dokploy + Traefik + SSL
- [ ] Dominio configurado
- [ ] Onboarding dos 5 beta testers
- [ ] Documentacao de uso para funcionarios

**Entrega:** Sistema no ar com 5 beta testers reais

---

## FASE 2: Modulo de Servicos

### Sprint 5 (Semana 8-9): Agendamento

- [ ] Migration: services, appointments, schedule_blocks
- [ ] Endpoints de servicos e agendamentos
- [ ] Tela: Agenda visual (FullCalendar)
- [ ] Tela: Gestao de servicos
- [ ] Pagina publica de agendamento (link unico)
- [ ] Verificacao de conflito de horarios
- [ ] Bloqueio de horarios

**Entrega:** Agendamento online funcionando

---

### Sprint 6 (Semana 10): WhatsApp (Evolution API)

- [ ] Setup Evolution API no Docker
- [ ] Tela: Conectar numero WhatsApp (QR Code)
- [ ] Job: Envio de lembretes 24h antes
- [ ] Mensagem de confirmacao ao agendar
- [ ] Log de mensagens enviadas

**Entrega:** Lembretes automaticos via WhatsApp

---

## FASE 3: CRM de Pets

### Sprint 7 (Semana 11-12): CRM

- [ ] Migration: clients, pets, pet_vaccines, pet_notes
- [ ] Endpoints de tutores e pets
- [ ] Tela: Lista de tutores com busca
- [ ] Tela: Ficha do pet (historico completo)
- [ ] Tela: Cartao de vacinas
- [ ] Alerta de vacinas vencendo
- [ ] Lista de clientes inativos

**Entrega:** CRM completo com historico de pets

---

## FASE 4: IA e Automacoes

### Sprint 8 (Semana 13-16): IA

- [ ] Integracao OpenAI API
- [ ] Relatorio financeiro com analise em linguagem natural
- [ ] Sugestoes de reposicao de estoque com base em historico
- [ ] Upsell automatico: recomendar servico com base no pet
- [ ] Dashboard de insights (IA explica tendencias)

**Entrega:** IA integrada nas principais telas

---

## Cronograma Visual

```
Abr 2026   Mai 2026   Jun 2026   Jul 2026   Ago 2026
|          |          |          |          |
Sprint 1   Sprint 3   Sprint 4   Sprint 6   Sprint 8
Sprint 2   ........   Sprint 5   Sprint 7   ........
```

---

## Metricas por Fase

| Fase | Duracao | Clientes Meta | MRR Meta |
|------|---------|---------------|----------|
| MVP (beta) | Semana 7 | 5 beta gratis | R$ 0 |
| MVP comercial | Semana 8-10 | 20 pagantes | R$ 6.000 |
| v2.0 lancado | Semana 12 | 50 pagantes | R$ 17.500 |
| v3.0 (IA) | Semana 16 | 100 pagantes | R$ 40.000 |

---

## Dependencias e Riscos

| Risco | Probabilidade | Mitigacao |
|-------|---------------|-----------|
| Integracao Asaas complexa | Baixa | Usar sandbox + documentacao oficial |
| Evolution API instavel | Media | Ter fallback manual para WhatsApp |
| Beta tester nao usa | Media | Onboarding presencial nos 5 primeiros |
| Escopo cresce muito | Alta | Seguir SDD estritamente, nao adicionar features |
| Bug critico em producao | Media | Rollback rapido via Dokploy |

---

## Definition of Done (DoD) Global

Uma feature so e considerada DONE quando:
- [ ] Codigo revisado e sem warnings
- [ ] Testes unitarios passando
- [ ] Endpoint documentado no Swagger
- [ ] Tela funcionando no mobile (responsiva)
- [ ] Sem erros no console do browser
- [ ] Testado manualmente em producao
