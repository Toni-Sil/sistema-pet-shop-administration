# 06 - Banco de Dados

**SGBD:** PostgreSQL 15

---

## Diagrama de Entidades (Resumo)

```
stores (lojas)
  |-- users (funcionarios/donos)
  |-- products (produtos)
  |    |-- stock_movements (movimentacoes)
  |-- sales (vendas)
  |    |-- sale_items (itens da venda)
  |-- expenses (despesas)
  |-- cashier_sessions (caixas)
  |-- services (servicos oferecidos)
  |-- appointments (agendamentos)
  |    |-- schedule_blocks (bloqueios)
  |-- clients (tutores)
  |    |-- pets (animais)
  |         |-- pet_vaccines (vacinas)
  |         |-- pet_notes (anotacoes)
```

---

## Schema SQL Completo

```sql
-- Habilitar UUID
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- LOJAS
-- ==========================================
CREATE TABLE stores (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name         VARCHAR(255) NOT NULL,
  slug         VARCHAR(100) UNIQUE NOT NULL,  -- usado no link publico
  phone        VARCHAR(20),
  address      TEXT,
  logo_url     TEXT,
  plan         VARCHAR(20) DEFAULT 'starter', -- starter|professional|enterprise
  is_active    BOOLEAN DEFAULT TRUE,
  settings     JSONB DEFAULT '{}',            -- configs da loja (horarios, etc)
  created_at   TIMESTAMP DEFAULT NOW()
);

-- ==========================================
-- USUARIOS
-- ==========================================
CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id      UUID NOT NULL REFERENCES stores(id),
  name          VARCHAR(255) NOT NULL,
  email         VARCHAR(255) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role          VARCHAR(20) DEFAULT 'employee', -- owner|manager|employee
  mfa_secret    TEXT,
  mfa_enabled   BOOLEAN DEFAULT FALSE,
  is_active     BOOLEAN DEFAULT TRUE,
  last_login    TIMESTAMP,
  created_at    TIMESTAMP DEFAULT NOW()
);

-- ==========================================
-- PRODUTOS
-- ==========================================
CREATE TABLE products (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id    UUID NOT NULL REFERENCES stores(id),
  name        VARCHAR(255) NOT NULL,
  sku         VARCHAR(100),
  category    VARCHAR(50) NOT NULL,
  cost_price  DECIMAL(10,2) NOT NULL,
  sale_price  DECIMAL(10,2) NOT NULL,
  quantity    INTEGER NOT NULL DEFAULT 0,
  min_qty     INTEGER NOT NULL DEFAULT 5,
  unit        VARCHAR(20) DEFAULT 'un',
  expires_at  DATE,
  image_url   TEXT,
  is_active   BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMP DEFAULT NOW(),
  UNIQUE(store_id, sku)
);

CREATE TABLE stock_movements (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id  UUID NOT NULL REFERENCES products(id),
  store_id    UUID NOT NULL REFERENCES stores(id),
  type        VARCHAR(10) NOT NULL CHECK (type IN ('entry', 'exit')),
  quantity    INTEGER NOT NULL,
  reason      VARCHAR(50),
  cost_price  DECIMAL(10,2),
  supplier    VARCHAR(255),
  sale_id     UUID,                           -- referencia se saida por venda
  user_id     UUID REFERENCES users(id),
  created_at  TIMESTAMP DEFAULT NOW()
);

-- ==========================================
-- VENDAS
-- ==========================================
CREATE TABLE sales (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id        UUID NOT NULL REFERENCES stores(id),
  user_id         UUID REFERENCES users(id),
  cashier_id      UUID,
  total           DECIMAL(10,2) NOT NULL,
  discount        DECIMAL(10,2) DEFAULT 0,
  payment_method  VARCHAR(20) NOT NULL CHECK (payment_method IN ('pix', 'cash', 'card', 'mixed')),
  payment_status  VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'cancelled', 'refunded')),
  asaas_charge_id VARCHAR(255),
  pix_qr_code     TEXT,
  notes           TEXT,
  paid_at         TIMESTAMP,
  created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sale_items (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sale_id     UUID NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
  product_id  UUID NOT NULL REFERENCES products(id),
  quantity    INTEGER NOT NULL,
  unit_price  DECIMAL(10,2) NOT NULL,
  total       DECIMAL(10,2) NOT NULL
);

-- ==========================================
-- FINANCEIRO
-- ==========================================
CREATE TABLE expenses (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id    UUID NOT NULL REFERENCES stores(id),
  description VARCHAR(255) NOT NULL,
  amount      DECIMAL(10,2) NOT NULL,
  category    VARCHAR(50) NOT NULL,
  due_date    DATE NOT NULL,
  paid_at     DATE,
  is_paid     BOOLEAN DEFAULT FALSE,
  notes       TEXT,
  created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cashier_sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id        UUID NOT NULL REFERENCES stores(id),
  user_id         UUID REFERENCES users(id),
  opening_balance DECIMAL(10,2) NOT NULL,
  closing_balance DECIMAL(10,2),
  total_sales     DECIMAL(10,2),
  notes           TEXT,
  opened_at       TIMESTAMP DEFAULT NOW(),
  closed_at       TIMESTAMP
);

-- ==========================================
-- AGENDAMENTOS
-- ==========================================
CREATE TABLE services (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id    UUID NOT NULL REFERENCES stores(id),
  name        VARCHAR(100) NOT NULL,
  description TEXT,
  duration    INTEGER NOT NULL,
  price       DECIMAL(10,2) NOT NULL,
  color       VARCHAR(7) DEFAULT '#3B82F6',
  is_active   BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE appointments (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id     UUID NOT NULL REFERENCES stores(id),
  service_id   UUID NOT NULL REFERENCES services(id),
  pet_id       UUID REFERENCES pets(id),
  client_name  VARCHAR(255) NOT NULL,
  client_phone VARCHAR(20) NOT NULL,
  pet_name     VARCHAR(100),
  scheduled_at TIMESTAMP NOT NULL,
  ends_at      TIMESTAMP NOT NULL,
  status       VARCHAR(20) DEFAULT 'pending',
  notes        TEXT,
  reminder_sent BOOLEAN DEFAULT FALSE,
  created_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE schedule_blocks (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id   UUID NOT NULL REFERENCES stores(id),
  starts_at  TIMESTAMP NOT NULL,
  ends_at    TIMESTAMP NOT NULL,
  reason     VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW()
);

-- ==========================================
-- CRM
-- ==========================================
CREATE TABLE clients (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id   UUID NOT NULL REFERENCES stores(id),
  name       VARCHAR(255) NOT NULL,
  phone      VARCHAR(20) NOT NULL,
  email      VARCHAR(255),
  address    TEXT,
  notes      TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pets (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id   UUID NOT NULL REFERENCES clients(id),
  store_id    UUID NOT NULL REFERENCES stores(id),
  name        VARCHAR(100) NOT NULL,
  species     VARCHAR(20) NOT NULL,
  breed       VARCHAR(100),
  birth_date  DATE,
  weight_kg   DECIMAL(5,2),
  allergies   TEXT,
  notes       TEXT,
  photo_url   TEXT,
  created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pet_vaccines (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pet_id      UUID NOT NULL REFERENCES pets(id),
  vaccine     VARCHAR(100) NOT NULL,
  applied_at  DATE NOT NULL,
  next_dose   DATE,
  notes       TEXT,
  created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pet_notes (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pet_id     UUID NOT NULL REFERENCES pets(id),
  user_id    UUID REFERENCES users(id),
  note       TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- ==========================================
-- INDICES (Performance)
-- ==========================================
CREATE INDEX idx_products_store ON products(store_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_stock_movements_product ON stock_movements(product_id);
CREATE INDEX idx_sales_store_created ON sales(store_id, created_at);
CREATE INDEX idx_appointments_store_date ON appointments(store_id, scheduled_at);
CREATE INDEX idx_clients_store_phone ON clients(store_id, phone);
CREATE INDEX idx_pets_client ON pets(client_id);
```

---

## Convencoes

- **UUID** como chave primaria em todas as tabelas
- **store_id** em todas as tabelas para isolamento por loja
- **created_at** em todas as tabelas (auditoria)
- **Soft delete** via `is_active = FALSE` (nao deletar registros)
- **JSONB** para configuracoes flexiveis (campo `settings` em stores)
- **Constraints CHECK** para campos com valores fixos (status, type, etc)
