# 🐾 Sistema Automatico de Administracao Pet Shop

> SaaS modular para gestao completa de pet shops — controle de estoque, financeiro, agendamento e CRM de pets.

---

## 📋 Visao Geral

Este sistema foi projetado utilizando **Spec-Driven Development (SDD)** para garantir que cada modulo seja desenvolvido com clareza, rastreabilidade e qualidade desde o inicio.

O sistema e composto por **modulos independentes** que podem ser ativados conforme a necessidade do cliente:

| Modulo | Status | Descricao |
|--------|--------|-----------|
| 🏪 **Estoque** | `MVP` | Controle de produtos, entradas, saidas e alertas |
| 💰 **Financeiro** | `MVP` | Caixa, contas a pagar/receber, relatorios |
| 📅 **Agendamento** | `v2.0` | Agenda online, lembretes WhatsApp |
| 🐶 **CRM de Pets** | `v2.0` | Ficha de tutores, pets e historico clinico |
| 🤖 **IA** | `v3.0` | Relatorios inteligentes, upsell automatico |

---

## 🏗️ Arquitetura

```
Backend:    Python + FastAPI
Frontend:   React + TypeScript
Database:   PostgreSQL
Auth:       JWT + MFA
WhatsApp:   Evolution API (numero proprio do cliente)
Pagamento:  Asaas (Pix nativo)
IA:         OpenAI API + outros provedores (Anthropic, Gemini, Sabiá, etc.)
Infra:      Docker + Dokploy
```

---

## 📁 Estrutura de Documentacao SDD

```
docs/
├── 00-visao-geral.md              # Contexto, problema e solucao
├── 01-modulo-estoque.md           # Spec completa do modulo de estoque
├── 02-modulo-financeiro.md        # Spec completa do modulo financeiro
├── 03-modulo-agendamento.md       # Spec completa do modulo de agendamento
├── 04-modulo-crm.md               # Spec completa do CRM de pets
├── 05-arquitetura-tecnica.md      # Stack, endpoints, componentes
├── 06-banco-de-dados.md           # Schema PostgreSQL completo
├── 07-roadmap.md                  # Sprints, timeline e prioridades
├── 09-ia-multiagentes-llm.md      # Arquitetura de IA, multiagentes e estratégia de LLM
└── 10-ia-memoria-feedback.md      # Memória, feedback e aprendizado contínuo dos agentes
```

> Observacao: o repositorio, neste momento, e focado em **documentacao e design**. A implementacao sera guiada por estes arquivos SDD e pelas skills de IA descritas em `09` e `10` quando o sistema for para producao.

---

## 🚀 Roadmap Resumido

### MVP — Modulo Base (Semanas 1-6)
- [x] Setup do projeto + Auth + estrutura base
- [ ] Modulo de Estoque completo
- [ ] Modulo Financeiro + PDV + Pix
- [ ] Dashboard de metricas
- [ ] Deploy em producao

### v2.0 — Modulo Servicos (Semanas 7-12)
- [ ] Agendamento online com link publico
- [ ] Lembretes automaticos via WhatsApp
- [ ] CRM de tutores e pets
- [ ] Historico clinico por pet

### v3.0 — Modulo IA (Semanas 13-20)
- [ ] Agentes por modulo (estoque, financeiro, agendamento, CRM)
- [ ] Relatorios inteligentes com IA
- [ ] Sugestoes de reposicao de estoque
- [ ] Upsell automatico por perfil do pet
- [ ] Analise de churn de clientes

---

## 💰 Modelo de Negocio

| Plano | Preco | Modulos |
|-------|-------|---------|
| Starter | R$ 299/mes | Estoque + Financeiro |
| Professional | R$ 699/mes | + Agendamento + CRM |
| Enterprise | R$ 1.299/mes | + IA + White-label |

---

## 🛠️ Como Rodar Localmente

```bash
# Clone o repositorio
git clone https://github.com/Toni-Sil/sistema-pet-shop-administration.git

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## 📄 Licenca

Proprietario — Todos os direitos reservados © 2026 Toni-Sil
