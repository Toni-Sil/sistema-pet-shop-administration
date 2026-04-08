# 00 - Visao Geral do Projeto

## Contexto

Pet shops no Brasil enfrentam um problema critico: **80-85% operam sem nenhum sistema de gestao adequado**. Usam planilhas Excel, cadernos e WhatsApp para controlar estoque, agendamentos e financeiro.

Este sistema resolve isso com uma solucao SaaS moderna, acessivel e modular.

---

## O Problema

| Problema | Impacto no Negocio |
|----------|--------------------|
| Estoque no olho | Produtos vencem, falta item na hora errada |
| Financeiro em Excel | Nao sabe quanto lucra por servico/produto |
| Agendamento no caderno | Overbooking, cliente sem lembrete, falta |
| Historico do pet perdido | Recomeca do zero a cada atendimento |
| Sem dashboard | Decisoes na intuicao, sem dados reais |
| Comunicacao manual | Horas perdidas enviando mensagens uma a uma |

---

## A Solucao

Sistema modular com **2 fases de entrega**:

### Fase 1 - MVP (Modulo Base)
Foco em loja de produtos pet:
- Controle de estoque completo
- PDV com Pix integrado
- Financeiro (caixa, contas, relatorios)
- Dashboard de metricas

### Fase 2 - Modulo Servicos
Foco em servicos (banho, tosa, consulta):
- Agendamento online
- Lembretes automaticos WhatsApp
- CRM de tutores e pets
- Historico clinico

### Fase 3 - Modulo IA
- Relatorios inteligentes
- Sugestoes de reposicao
- Upsell automatico

---

## Publico-Alvo

**Primario:** Pet shops de pequeno e medio porte (1-5 funcionarios)
- Faturamento mensal: R$ 20.000 - R$ 80.000
- Sem sistema atual ou com sistema desatualizado
- Localizados em cidades brasileiras de medio e grande porte

**Secundario:** Redes de pet shops (2-10 unidades)
- Precisam de visao consolidada
- Plano Enterprise com multitenancy

---

## Proposta de Valor

> "Controle total do seu pet shop em um unico sistema. Estoque, financeiro e clientes — tudo integrado, simples e acessivel."

**Para o dono:**
- Sabe exatamente quanto lucra todo dia
- Nao perde venda por falta de estoque
- Clientes voltam mais (lembretes automaticos)

**Para o funcionario:**
- Interface simples, aprende em 1 dia
- Menos retrabalho e erro humano
- Historico do pet sempre disponivel

---

## Modelo de Instalacao

- **Instalacao individual por cliente** (nao e SaaS multi-tenant)
- Cada pet shop tem sua propria instancia
- Deploy via Docker no VPS do cliente ou hospedado pelo desenvolvedor
- Suporte e atualizacoes inclusos no plano

---

## Metricas de Sucesso (KPIs do Produto)

| KPI | Meta MVP | Meta 6 meses |
|-----|----------|--------------|
| Clientes ativos | 5 (beta) | 50 |
| Churn mensal | < 5% | < 3% |
| NPS | > 7 | > 8.5 |
| Ticket medio | R$ 400/mes | R$ 550/mes |
| MRR | R$ 2.000 | R$ 27.500 |

---

## Referencias e Benchmarks

- **SimplesVet** - Concorrente principal, interface complexa, sem IA
- **NuvemVet** - Bom em clinicas, fraco em loja
- **PetMaster** - UX razoavel, sem automacao
- **Auto-Tech-Lith** (repositorio proprio) - Base de auth, agentes IA e agendamento reaproveitavel
- **systema-de-gerenciamento-S.F.C.P.C** (repositorio proprio) - Base de controle de estoque reaproveitavel
