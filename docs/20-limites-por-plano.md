# 20 - Limites por Plano e Controle de Uso

## Objetivo

Definir o que acontece quando um cliente atinge os limites do seu plano, garantindo experiência clara e sem surpresas, e incentivando o upgrade de forma não intrusiva.

---

## 1. Limites por plano

| Recurso | Starter | Professional | Enterprise |
|---|---|---|---|
| Usuários | 2 | 5 | Ilimitado |
| Produtos cadastrados | 300 | 2.000 | Ilimitado |
| Clientes cadastrados | 500 | Ilimitado | Ilimitado |
| Agendamentos/mês | 200 | Ilimitado | Ilimitado |
| Módulo IA | ❌ | ✅ Parcial | ✅ Completo |
| White-label | ❌ | ❌ | ✅ |
| Suporte | E-mail | WhatsApp | Prioritário |

---

## 2. Comportamento ao atingir limite

### Aproximando do limite (80%)

- Banner informativo no painel: "Você está usando 80% do limite de produtos do plano Starter."
- Nenhuma funcionalidade bloqueada ainda.

### Limite atingido (100%)

- Bloquear **somente a ação específica** que excede o limite.
  - Ex.: ao tentar cadastrar o 301º produto no Starter → modal explicando o limite com botão "Ver planos".
- **Nunca bloquear** funcionalidades que o cliente já usa (não apagar dados, não travar PDV).
- Dados existentes permanecem totalmente acessíveis e operacionais.

### UX do bloqueio

- Modal simples com:
  - O que está limitado e por quê.
  - Benefícios do plano superior.
  - Botão "Fazer upgrade" (abre tela de planos).
  - Botão "Agora não" (fecha sem forçar).
- Sem banners agressivos ou bloqueio de tela inteira.

---

## 3. Controle técnico dos limites

- Limites armazenados na tabela `stores` via campo `plan` + tabela de configuração de planos.
- Verificação feita no backend em cada operação de criação (middleware de quota).
- Nunca verificar só no frontend (pode ser burlado).

```sql
CREATE TABLE plan_limits (
  plan         VARCHAR(20) PRIMARY KEY,
  max_users    INTEGER,      -- NULL = ilimitado
  max_products INTEGER,
  max_clients  INTEGER,
  max_appts_month INTEGER,
  has_ai       BOOLEAN DEFAULT FALSE,
  has_whitelabel BOOLEAN DEFAULT FALSE
);

INSERT INTO plan_limits VALUES
  ('starter',      2,    300,  500,  200,  FALSE, FALSE),
  ('professional', 5,    2000, NULL, NULL, TRUE,  FALSE),
  ('enterprise',   NULL, NULL, NULL, NULL, TRUE,  TRUE);
```

---

## 4. Upgrade de plano

- Upgrade ativo imediatamente (sem necessidade de reiniciar sistema).
- Downgrade: só na próxima renovação; manter acesso ao plano atual até o vencimento.
- Se cliente fizer downgrade e tiver mais dados que o novo plano permite: manter dados, apenas bloquear criação de novos até que fique dentro do limite.
