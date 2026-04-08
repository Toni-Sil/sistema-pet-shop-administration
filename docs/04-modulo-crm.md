# 04 - Modulo CRM de Pets

**Status:** v2.0 | **Prioridade:** Media | **Sprint:** 10-11

---

## User Stories

### US-01: Cadastro de Tutor
> Como funcionario, quero cadastrar o tutor (dono do pet) com nome, telefone e endereco.

**Criterios de Aceite:**
- [ ] Nome, telefone (obrigatorio), email, endereco (opcional)
- [ ] Busca rapida por nome ou telefone
- [ ] Historico de visitas do tutor
- [ ] Total gasto pelo tutor no pet shop

### US-02: Cadastro de Pet
> Como funcionario, quero cadastrar o pet com nome, especie, raca, idade e observacoes.

**Criterios de Aceite:**
- [ ] Nome, especie (cao/gato/outro), raca, data nascimento
- [ ] Peso atual
- [ ] Alergias e observacoes importantes
- [ ] Foto do pet (opcional)
- [ ] Um tutor pode ter multiplos pets

### US-03: Historico Clinico / Ficha do Pet
> Como funcionario, quero acessar o historico completo do pet em uma tela.

**Criterios de Aceite:**
- [ ] Lista de servicos realizados com data e preco
- [ ] Registro de vacinas com data e proxima dose
- [ ] Anotacoes por atendimento
- [ ] Medicamentos em uso

### US-04: Cartao de Vacinas
> Como funcionario, quero registrar vacinas do pet e ser alertado quando vencer.

**Criterios de Aceite:**
- [ ] Tipo da vacina, data aplicacao, data proxima dose
- [ ] Alerta quando vacina vence em 30 dias
- [ ] Lista de vacinas por pet

### US-05: Fidelizacao
> Como dono, quero ver quais clientes nao voltam ha mais de 60 dias para reengajamento.

**Criterios de Aceite:**
- [ ] Lista de clientes inativos (sem visita em X dias)
- [ ] Exportar lista para campanha WhatsApp
- [ ] Tag de frequencia: regular, esporadico, inativo

---

## Endpoints da API

```
# Tutores
GET    /api/clients              - Listar tutores
POST   /api/clients              - Cadastrar tutor
GET    /api/clients/{id}         - Detalhe + historico
PUT    /api/clients/{id}         - Atualizar tutor

# Pets
GET    /api/pets                 - Listar pets
POST   /api/pets                 - Cadastrar pet
GET    /api/pets/{id}            - Ficha completa do pet
PUT    /api/pets/{id}            - Atualizar pet

# Historico
GET    /api/pets/{id}/history    - Historico de servicos
POST   /api/pets/{id}/notes      - Adicionar anotacao
GET    /api/pets/{id}/vaccines   - Cartao de vacinas
POST   /api/pets/{id}/vaccines   - Registrar vacina

# Fidelizacao
GET    /api/clients/inactive     - Clientes inativos
```

---

## Schema de Dados

```sql
-- Tutores
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

-- Pets
CREATE TABLE pets (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id   UUID NOT NULL REFERENCES clients(id),
  store_id    UUID NOT NULL REFERENCES stores(id),
  name        VARCHAR(100) NOT NULL,
  species     VARCHAR(20) NOT NULL, -- 'dog' | 'cat' | 'other'
  breed       VARCHAR(100),
  birth_date  DATE,
  weight_kg   DECIMAL(5,2),
  allergies   TEXT,
  notes       TEXT,
  photo_url   TEXT,
  created_at  TIMESTAMP DEFAULT NOW()
);

-- Vacinas
CREATE TABLE pet_vaccines (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pet_id      UUID NOT NULL REFERENCES pets(id),
  vaccine     VARCHAR(100) NOT NULL,
  applied_at  DATE NOT NULL,
  next_dose   DATE,
  notes       TEXT,
  created_at  TIMESTAMP DEFAULT NOW()
);

-- Anotacoes por Atendimento
CREATE TABLE pet_notes (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pet_id     UUID NOT NULL REFERENCES pets(id),
  user_id    UUID REFERENCES users(id),
  note       TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Regras de Negocio

1. **Pet sempre vinculado a tutor:** Nao existe pet sem tutor no sistema
2. **Historico imutavel:** Anotacoes nao podem ser editadas, apenas adicionadas
3. **Alerta de vacina:** Job diario verifica pets com vacina vencendo em 30 dias
4. **Cliente inativo:** Definido como sem visita em 60 dias (configuravel pelo dono)
5. **Busca unificada:** Buscar por nome do tutor ou nome do pet retorna resultados de ambos

---

## Criterios de Conclusao

- [ ] Cadastro de tutor e pet funcionando
- [ ] Ficha do pet com historico completo
- [ ] Cartao de vacinas com alertas
- [ ] Lista de clientes inativos
- [ ] Busca unificada tutor + pet
