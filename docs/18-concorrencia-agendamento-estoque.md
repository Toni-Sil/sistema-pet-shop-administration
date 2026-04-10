# 18 - Concorrência: Overbooking e Estoque Negativo

## Objetivo

Evitar situações onde dois usuários simultâneos causem conflitos de dados, como dois agendamentos no mesmo horário ou venda do mesmo produto em estoque insuficiente.

---

## 1. Problema de concorrência

Com múltiplos usuários simultâneos (ex.: 2 atendentes no PDV), sem controle adequado:
- Usuário A e Usuário B consultam estoque: 1 unidade disponível.
- Ambos registram venda ao mesmo tempo.
- Resultado: estoque vai para -1. ❌

---

## 2. Proteção de estoque (Pessimistic Lock)

- Ao iniciar uma venda, reservar os itens via `SELECT ... FOR UPDATE` no PostgreSQL.
- Isso garante que outro processo espere até a venda ser confirmada ou cancelada.

```sql
-- Ao adicionar item ao carrinho:
BEGIN;
SELECT quantity FROM products
WHERE id = $1 AND store_id = $2
FOR UPDATE;

-- Verificar se quantity >= quantidade_desejada
-- Se sim: prosseguir
-- Se não: retornar erro "Estoque insuficiente"
COMMIT;
```

- Constraint adicional no banco:
```sql
ALTER TABLE products
  ADD CONSTRAINT chk_quantity_non_negative
  CHECK (quantity >= 0);
```

- UX: se produto ficar sem estoque durante a venda, exibir mensagem clara:
  "Quantidade indisponível. Outro atendimento acabou de reservar este item."

---

## 3. Proteção de agenda (Overbooking)

- Ao confirmar agendamento, verificar conflito com `SELECT ... FOR UPDATE` na tabela `appointments`.
- Dois agendamentos conflitam se: mesmo `store_id`, mesmo profissional (se aplicável), e intervalos de tempo se sobrepõem.

```sql
SELECT COUNT(*) FROM appointments
WHERE store_id = $1
  AND status NOT IN ('cancelled', 'no_show')
  AND scheduled_at < $ends_at
  AND ends_at > $scheduled_at
FOR UPDATE;
```

- Se COUNT > 0: rejeitar com mensagem "Este horário acabou de ser ocupado. Escolha outro horário."
- Frontend deve recarregar horários disponíveis após conflito para mostrar estado atual.

---

## 4. Idempotência em operações críticas

- Operações críticas (criar venda, confirmar agendamento, emitir nota) devem ser **idempotentes**: se o usuário clicar duas vezes ou a requisição for reenviada, o resultado deve ser o mesmo (sem duplicar).
- Implementar via `idempotency_key` único por operação (UUID gerado no frontend):
```http
POST /api/sales
X-Idempotency-Key: <uuid-gerado-no-frontend>
```
- Backend verifica se já processou essa chave; se sim, retorna resultado anterior.
