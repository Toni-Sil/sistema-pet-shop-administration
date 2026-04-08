# 02 - Modulo Financeiro

**Status:** MVP | **Prioridade:** Alta | **Sprint:** 3-4

---

## User Stories

### US-01: PDV (Ponto de Venda)
> Como funcionario, quero registrar uma venda selecionando produtos do estoque e finalizar com Pix ou dinheiro.

**Criterios de Aceite:**
- [ ] Buscar produto por nome ou SKU
- [ ] Adicionar multiplos itens em uma venda
- [ ] Calcular total automaticamente
- [ ] Aplicar desconto (valor fixo ou percentual)
- [ ] Formas de pagamento: Pix, Dinheiro, Cartao (manual)
- [ ] Gerar QR Code Pix via Asaas em tempo real
- [ ] Ao finalizar: baixar estoque automaticamente
- [ ] Emitir recibo digital (PDF ou link)

### US-02: Controle de Caixa
> Como dono, quero abrir e fechar o caixa do dia com saldo inicial e conferencia ao final.

**Criterios de Aceite:**
- [ ] Abertura de caixa com saldo inicial
- [ ] Registro de todas as entradas e saidas do dia
- [ ] Fechamento com total esperado vs total real
- [ ] Historico de caixas por data

### US-03: Contas a Pagar
> Como dono, quero registrar despesas (aluguel, fornecedor, luz) e acompanhar o que esta em aberto.

**Criterios de Aceite:**
- [ ] Cadastrar despesa com descricao, valor, vencimento e categoria
- [ ] Marcar como pago com data e forma de pagamento
- [ ] Alertas de contas vencidas e vencendo em 3 dias
- [ ] Relatorio de despesas por categoria e periodo

### US-04: Contas a Receber
> Como dono, quero ver todas as vendas pendentes de pagamento.

**Criterios de Aceite:**
- [ ] Listagem de vendas com status (pago/pendente/vencido)
- [ ] Filtro por periodo e status
- [ ] Total de receita do dia/semana/mes

### US-05: Dashboard Financeiro
> Como dono, quero ver no dashboard: receita do dia, despesas do mes, lucro liquido e fluxo de caixa.

**Criterios de Aceite:**
- [ ] Card: Receita hoje
- [ ] Card: Despesas do mes
- [ ] Card: Lucro liquido do mes
- [ ] Grafico: Receita dos ultimos 30 dias
- [ ] Grafico: Despesas por categoria (pizza)
- [ ] Top 5 produtos mais vendidos

### US-06: Relatorio Financeiro
> Como dono, quero exportar relatorio financeiro do mes.

**Criterios de Aceite:**
- [ ] Relatorio de vendas por periodo
- [ ] Relatorio de despesas por categoria
- [ ] DRE simplificado (receita - despesa = lucro)
- [ ] Exportar em PDF e CSV

---

## Endpoints da API

```
# PDV
POST   /api/sales                  - Criar venda
GET    /api/sales                  - Listar vendas
GET    /api/sales/{id}             - Detalhe da venda
POST   /api/sales/{id}/cancel      - Cancelar venda

# Pagamentos Pix (Asaas)
POST   /api/payments/pix           - Gerar QR Code Pix
GET    /api/payments/{id}/status   - Verificar status pagamento

# Caixa
POST   /api/cashier/open           - Abrir caixa
POST   /api/cashier/close          - Fechar caixa
GET    /api/cashier/current        - Caixa atual
GET    /api/cashier/history        - Historico de caixas

# Contas
GET    /api/bills/payable          - Contas a pagar
POST   /api/bills/payable          - Criar despesa
PUT    /api/bills/payable/{id}/pay - Marcar como pago
GET    /api/bills/receivable       - Contas a receber

# Relatorios
GET    /api/reports/financial      - Relatorio financeiro
GET    /api/reports/dre            - DRE simplificado
GET    /api/dashboard/financial    - Dados do dashboard
```

---

## Schema de Dados

```sql
-- Vendas
CREATE TABLE sales (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id        UUID NOT NULL REFERENCES stores(id),
  user_id         UUID REFERENCES users(id),
  total           DECIMAL(10,2) NOT NULL,
  discount        DECIMAL(10,2) DEFAULT 0,
  payment_method  VARCHAR(20) NOT NULL, -- 'pix' | 'cash' | 'card'
  payment_status  VARCHAR(20) DEFAULT 'pending', -- 'pending' | 'paid' | 'cancelled'
  asaas_charge_id VARCHAR(255),
  notes           TEXT,
  created_at      TIMESTAMP DEFAULT NOW()
);

-- Itens da Venda
CREATE TABLE sale_items (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sale_id     UUID NOT NULL REFERENCES sales(id),
  product_id  UUID NOT NULL REFERENCES products(id),
  quantity    INTEGER NOT NULL,
  unit_price  DECIMAL(10,2) NOT NULL,
  total       DECIMAL(10,2) NOT NULL
);

-- Despesas
CREATE TABLE expenses (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id    UUID NOT NULL REFERENCES stores(id),
  description VARCHAR(255) NOT NULL,
  amount      DECIMAL(10,2) NOT NULL,
  category    VARCHAR(50) NOT NULL,
  due_date    DATE NOT NULL,
  paid_at     DATE,
  is_paid     BOOLEAN DEFAULT FALSE,
  created_at  TIMESTAMP DEFAULT NOW()
);

-- Caixa
CREATE TABLE cashier_sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id        UUID NOT NULL REFERENCES stores(id),
  user_id         UUID REFERENCES users(id),
  opening_balance DECIMAL(10,2) NOT NULL,
  closing_balance DECIMAL(10,2),
  opened_at       TIMESTAMP DEFAULT NOW(),
  closed_at       TIMESTAMP
);
```

---

## Integracao Asaas (Pix)

```python
# Exemplo de geracao de cobranca Pix
import httpx

async def create_pix_charge(amount: float, description: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://api.asaas.com/v3/payments',
            headers={'access_token': ASAAS_API_KEY},
            json={
                'customer': STORE_CUSTOMER_ID,
                'billingType': 'PIX',
                'value': amount,
                'description': description,
                'dueDate': today_str()
            }
        )
    return response.json()
```

---

## Regras de Negocio

1. **Venda so finaliza com pagamento confirmado** (Pix) ou manual (dinheiro/cartao)
2. **Cancelamento de venda devolve estoque** automaticamente
3. **Caixa deve estar aberto** para registrar vendas
4. **Desconto maximo de 30%** (configuravel pelo dono)
5. **Webhook Asaas** atualiza status do pagamento em tempo real

---

## Criterios de Conclusao

- [ ] PDV funcionando com Pix e dinheiro
- [ ] QR Code Pix gerado em < 3 segundos
- [ ] Estoque baixa automaticamente ao finalizar venda
- [ ] Dashboard financeiro com graficos
- [ ] Relatorio exportavel em PDF
- [ ] Webhook Asaas configurado e testado
