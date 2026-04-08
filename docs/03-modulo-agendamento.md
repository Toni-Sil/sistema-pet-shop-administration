# 03 - Modulo de Agendamento

**Status:** v2.0 | **Prioridade:** Media | **Sprint:** 7-9

---

## User Stories

### US-01: Agenda Visual do Dia
> Como funcionario, quero ver todos os agendamentos do dia em formato de agenda visual por horario.

**Criterios de Aceite:**
- [ ] Visualizacao por dia, semana e mes
- [ ] Cor diferente por tipo de servico
- [ ] Status visual: confirmado, pendente, concluido, falta
- [ ] Clicar no agendamento para ver detalhes

### US-02: Agendamento Online (Link Publico)
> Como cliente, quero agendar um servico pelo link do pet shop sem precisar ligar.

**Criterios de Aceite:**
- [ ] Link publico unico por pet shop
- [ ] Selecionar servico, data e horario disponivel
- [ ] Informar nome, telefone e nome do pet
- [ ] Confirmacao automatica por WhatsApp
- [ ] Nao mostrar horarios ja ocupados

### US-03: Lembrete Automatico WhatsApp
> Como sistema, quero enviar lembrete via WhatsApp 24h antes do agendamento.

**Criterios de Aceite:**
- [ ] Mensagem automatica 24h antes
- [ ] Mensagem de confirmacao ao agendar
- [ ] Opcao de cancelar pelo WhatsApp
- [ ] Log de mensagens enviadas

### US-04: Gestao de Servicos
> Como dono, quero cadastrar os servicos oferecidos com nome, duracao e preco.

**Criterios de Aceite:**
- [ ] Nome, descricao, duracao (minutos), preco
- [ ] Servicos ativos/inativos
- [ ] Duracao usada para calcular disponibilidade

### US-05: Bloqueio de Horarios
> Como funcionario, quero bloquear horarios especificos (ferias, almoco, manutencao).

**Criterios de Aceite:**
- [ ] Bloquear horario unico ou recorrente
- [ ] Motivo do bloqueio (interno, nao visivel ao cliente)
- [ ] Horarios bloqueados nao aparecem no link publico

---

## Endpoints da API

```
GET    /api/appointments              - Listar agendamentos
POST   /api/appointments              - Criar agendamento (interno)
GET    /api/appointments/{id}         - Detalhe
PUT    /api/appointments/{id}         - Atualizar status
DELETE /api/appointments/{id}         - Cancelar

GET    /api/appointments/public/{slug}       - Disponibilidade (link publico)
POST   /api/appointments/public/{slug}       - Criar agendamento (link publico)

GET    /api/services                  - Listar servicos
POST   /api/services                  - Criar servico
PUT    /api/services/{id}             - Atualizar servico

POST   /api/schedule/block            - Bloquear horario
GET    /api/schedule/availability     - Horarios disponiveis
```

---

## Schema de Dados

```sql
-- Servicos
CREATE TABLE services (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id    UUID NOT NULL REFERENCES stores(id),
  name        VARCHAR(100) NOT NULL,
  description TEXT,
  duration    INTEGER NOT NULL, -- em minutos
  price       DECIMAL(10,2) NOT NULL,
  is_active   BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMP DEFAULT NOW()
);

-- Agendamentos
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
  status       VARCHAR(20) DEFAULT 'pending', -- pending|confirmed|done|cancelled|no_show
  notes        TEXT,
  created_at   TIMESTAMP DEFAULT NOW()
);

-- Bloqueios de Horario
CREATE TABLE schedule_blocks (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id   UUID NOT NULL REFERENCES stores(id),
  starts_at  TIMESTAMP NOT NULL,
  ends_at    TIMESTAMP NOT NULL,
  reason     VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Integracao Evolution API (WhatsApp)

```python
async def send_whatsapp_reminder(phone: str, client_name: str, service: str, date_str: str):
    message = f"Ola {client_name}! Lembrando que seu agendamento de {service} e amanha as {date_str}. Qualquer duvida, responda esta mensagem."
    
    await evolution_api.send_text(
        phone=phone,
        message=message
    )
```

**Configuracao:** Cada pet shop conecta seu proprio numero WhatsApp via QR Code na Evolution API.

---

## Regras de Negocio

1. **Sem sobreposicao:** Sistema verifica conflito de horario antes de confirmar
2. **Horario de funcionamento:** Agendamentos so podem ser criados dentro do horario cadastrado
3. **Antecedencia minima:** Nao permite agendar com menos de 2h de antecedencia (configuravel)
4. **Lembrete automatico:** Job roda toda madrugada e dispara WhatsApp para agendamentos do dia seguinte
5. **Link publico unico:** Gerado com slug do pet shop (ex: /agendar/petshop-do-ze)

---

## Criterios de Conclusao

- [ ] Agenda visual funcionando (dia/semana)
- [ ] Link publico de agendamento acessivel
- [ ] Lembrete WhatsApp enviado automaticamente
- [ ] Sem conflito de horario em nenhum cenario
- [ ] Gestao de servicos completa
