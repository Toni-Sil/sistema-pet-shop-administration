# 01 - Modulo de Estoque

**Status:** MVP | **Prioridade:** Alta | **Sprint:** 1-2

---

## User Stories

### US-01: Cadastro de Produto
> Como funcionario, quero cadastrar um produto com nome, SKU, preco de custo, preco de venda, quantidade minima e data de validade.

**Criterios de Aceite:**
- [ ] Campo SKU unico por loja
- [ ] Preco de venda deve ser maior que preco de custo
- [ ] Data de validade opcional (produtos sem validade aceitos)
- [ ] Categoria obrigatoria (Racao, Medicamento, Acessorio, Higiene, Outro)
- [ ] Foto do produto opcional (upload)

### US-02: Entrada de Estoque
> Como funcionario, quero registrar entrada de produtos (compra de fornecedor) para atualizar o estoque.

**Criterios de Aceite:**
- [ ] Selecionar produto existente ou cadastrar novo
- [ ] Informar quantidade, preco de custo e fornecedor
- [ ] Gerar historico de entrada com data e usuario
- [ ] Atualizar saldo de estoque automaticamente

### US-03: Saida de Estoque
> Como sistema, quero baixar o estoque automaticamente quando uma venda e finalizada no PDV.

**Criterios de Aceite:**
- [ ] Saida vinculada a venda no modulo financeiro
- [ ] Saida manual disponivel para perdas/ajustes
- [ ] Motivo obrigatorio em saidas manuais
- [ ] Nao permitir saldo negativo (bloquear venda se sem estoque)

### US-04: Alerta de Estoque Baixo
> Como dono, quero receber alerta quando produto atingir quantidade minima.

**Criterios de Aceite:**
- [ ] Alerta no dashboard (badge vermelho)
- [ ] Lista de produtos criticos na tela de estoque
- [ ] Notificacao por email (opcional, configuravel)

### US-05: Alerta de Vencimento
> Como dono, quero ver produtos proximos ao vencimento (30 dias) e vencidos.

**Criterios de Aceite:**
- [ ] Painel de vencimentos na tela de estoque
- [ ] Categorias: Vencido (vermelho), Vence em 7 dias (laranja), Vence em 30 dias (amarelo)
- [ ] Exportar lista de vencidos em CSV

### US-06: Relatorio de Estoque
> Como dono, quero ver relatorio completo do estoque atual com valor total.

**Criterios de Aceite:**
- [ ] Lista paginada com filtro por categoria
- [ ] Valor total em estoque (quantidade x preco custo)
- [ ] Exportar em PDF e CSV

---

## Endpoints da API

```
GET    /api/products              - Listar produtos (paginado, filtros)
POST   /api/products              - Cadastrar produto
GET    /api/products/{id}         - Detalhe do produto
PUT    /api/products/{id}         - Atualizar produto
DELETE /api/products/{id}         - Desativar produto (soft delete)

GET    /api/stock/movements        - Historico de movimentacoes
POST   /api/stock/entry            - Entrada de estoque
POST   /api/stock/exit             - Saida manual de estoque

GET    /api/stock/alerts           - Produtos com estoque baixo
GET    /api/stock/expiring         - Produtos proximos ao vencimento
GET    /api/stock/report           - Relatorio completo
```

---

## Schema de Dados

```sql
-- Produtos
CREATE TABLE products (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id    UUID NOT NULL REFERENCES stores(id),
  name        VARCHAR(255) NOT NULL,
  sku         VARCHAR(100) UNIQUE,
  category    VARCHAR(50) NOT NULL,
  cost_price  DECIMAL(10,2) NOT NULL,
  sale_price  DECIMAL(10,2) NOT NULL,
  quantity    INTEGER NOT NULL DEFAULT 0,
  min_qty     INTEGER NOT NULL DEFAULT 5,
  expires_at  DATE,
  image_url   TEXT,
  is_active   BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMP DEFAULT NOW()
);

-- Movimentacoes de Estoque
CREATE TABLE stock_movements (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id  UUID NOT NULL REFERENCES products(id),
  type        VARCHAR(10) NOT NULL, -- 'entry' | 'exit'
  quantity    INTEGER NOT NULL,
  reason      VARCHAR(100),         -- 'purchase' | 'sale' | 'loss' | 'adjust'
  cost_price  DECIMAL(10,2),
  supplier    VARCHAR(255),
  user_id     UUID REFERENCES users(id),
  created_at  TIMESTAMP DEFAULT NOW()
);
```

---

## Regras de Negocio

1. **Saldo negativo bloqueado:** Sistema nao permite saida maior que saldo disponivel
2. **SKU unico por loja:** Mesmo SKU pode existir em lojas diferentes
3. **Soft delete:** Produtos nao sao deletados, apenas desativados
4. **Historico imutavel:** Movimentacoes de estoque nao podem ser editadas, apenas estornadas
5. **Calculo de margem:** Sistema mostra margem de lucro automaticamente (preco venda - custo) / custo

---

## Componentes de Frontend

```
src/pages/stock/
  ProductList.tsx       - Lista principal com filtros
  ProductForm.tsx       - Formulario de cadastro/edicao
  ProductDetail.tsx     - Detalhe com historico de movimentacoes
  StockEntry.tsx        - Tela de entrada de estoque
  StockAlerts.tsx       - Painel de alertas (criticos + vencimentos)
  StockReport.tsx       - Relatorio exportavel

src/components/stock/
  ProductCard.tsx       - Card do produto
  StockBadge.tsx        - Badge de status (ok/baixo/critico)
  ExpirationTag.tsx     - Tag de vencimento colorida
  MovementHistory.tsx   - Tabela de historico
```

---

## Dependencias

- Modulo Financeiro (saida automatica ao finalizar venda)
- Auth (usuario logado para auditoria)

---

## Criterios de Conclusao (Definition of Done)

- [ ] Todos os endpoints implementados e testados
- [ ] Testes unitarios com cobertura > 80%
- [ ] Tela de lista, cadastro e alertas funcionando
- [ ] Alerta de estoque baixo aparece no dashboard
- [ ] Exportacao CSV funcionando
- [ ] Documentacao Swagger atualizada
