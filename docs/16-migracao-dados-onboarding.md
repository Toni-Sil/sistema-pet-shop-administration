# 16 - Migração de Dados e Onboarding de Novo Cliente

## Objetivo

Garantir que novos clientes consigam começar a usar o sistema rapidamente, mesmo vindo de planilhas Excel, cadernos ou outros sistemas, reduzindo o churn nos primeiros 30 dias.

---

## 1. Fluxo de onboarding

```
Dia 0: Contrato assinado
  → Provisionamento automático da instância (Docker)
  → Envio de e-mail com link de acesso e senha temporária

Dia 1-3: Configuração inicial guiada
  → Wizard de primeiro acesso (ver seção 2)
  → Importação de dados (ver seção 3)

Dia 4-7: Treinamento
  → Vídeos curtos por módulo (PDV, estoque, agenda)
  → Suporte via WhatsApp incluso no plano

Dia 8-30: Acompanhamento ativo
  → Check-in semanal automático (e-mail ou WhatsApp)
  → Alerta se loja não fizer login por 3 dias seguidos
```

---

## 2. Wizard de primeiro acesso

Ao fazer o primeiro login, exibir um wizard de 5 passos (pode pular e retomar depois):

1. **Dados da loja** — Nome, CNPJ, telefone, logo, endereço.
2. **Horário de funcionamento** — Para bloquear agendamentos fora do horário.
3. **Cadastrar primeiros produtos** — Mínimo 5 produtos para habilitar PDV.
4. **Cadastrar serviços** — Banho, tosa, consulta etc. (pode pular se só loja).
5. **Convidar funcionários** — Adicionar outros usuários com seus papéis.

Após o wizard: exibir checklist de "próximos passos" no dashboard.

---

## 3. Importação de dados

### 3.1 Importação via CSV (self-service)

O sistema aceita upload de CSV para importar em massa:

| Entidade | Campos obrigatórios no CSV |
|---|---|
| Produtos | nome, categoria, preco_venda, quantidade |
| Clientes | nome, telefone |
| Pets | nome_pet, nome_cliente, especie |

- Template CSV disponível para download no painel.
- Validação linha a linha com relatório de erros antes de confirmar importação.
- Importação em background (não trava a tela).

### 3.2 Importação assistida (plano Professional+)

- Cliente envia planilha Excel/CSV para o suporte.
- Suporte faz o mapeamento e importa via script interno.
- Prazo: até 3 dias úteis.

### 3.3 Dados que NÃO são importados automaticamente

- Histórico financeiro detalhado (apenas saldo inicial).
- XMLs fiscais de sistemas anteriores (cliente mantém os originais).
- Histórico clínico em formato proprietário de outros sistemas.

---

## 4. Saldo inicial de caixa

- No primeiro acesso ao módulo financeiro, permitir informar **saldo inicial de caixa**.
- Isso garante que os relatórios financeiros comecem com o valor correto.

---

## 5. Métricas de onboarding

| Métrica | Meta |
|---|---|
| Tempo até primeiro login | < 24h após contrato |
| Tempo até primeira venda registrada | < 3 dias |
| Conclusão do wizard | > 80% dos clientes |
| Churn no primeiro mês | < 5% |
