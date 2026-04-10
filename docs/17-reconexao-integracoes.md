# 17 - Reconexão e Expiração de Integrações

## Objetivo

Garantir que falhas nas integrações externas (Asaas/Pix, Evolution API/WhatsApp) sejam detectadas, comunicadas e resolvidas rapidamente, sem travar o funcionamento da loja.

---

## 1. Integrações críticas

| Integração | Impacto se falhar | Criticidade |
|---|---|---|
| Asaas (Pix) | Pagamentos Pix indisponíveis | Alta |
| Evolution API (WhatsApp) | Lembretes e automações parados | Média |
| Provedor fiscal (PlugNotas etc.) | Emissão de notas indisponível | Alta |

---

## 2. Monitoramento de status

- Health check periódico de cada integração (a cada 5 minutos).
- Status visível no painel de Configurações: ✅ Conectado / ⚠️ Instável / ❌ Desconectado.
- Se integração crítica falhar por mais de 5 minutos: notificar o dono da loja via e-mail.

---

## 3. Comportamento por integração

### 3.1 Asaas (Pix) desconectado

- PDV continua funcionando normalmente.
- Opção de Pix fica desabilitada com mensagem: "Pagamento via Pix temporariamente indisponível. Aceite dinheiro ou cartão."
- Vendas podem ser registradas sem Pix e o pagamento confirmado manualmente depois.
- Ao reconectar: nenhuma ação necessária (próximas cobranças funcionam normalmente).

### 3.2 Evolution API (WhatsApp) desconectada

- Lembretes e mensagens automáticas ficam em fila (ver doc 13).
- Ao reconectar: fila é processada em ordem, com respeito ao horário (não enviar mensagem fora do horário comercial da loja).
- Se desconexão for por token expirado: notificar admin com link para reconectar a instância WhatsApp.

### 3.3 Provedor fiscal desconectado

- Emissão de nota fiscal fica em modo de contingência (ver doc 13, seção 4).
- Ao reconectar: notas pendentes são transmitidas automaticamente.

---

## 4. Rotação e renovação de tokens

- Tokens de integração armazenados criptografados no banco (tabela `integrations`).
- Alertas proativos antes da expiração:
  - 30 dias antes: aviso informativo no painel.
  - 7 dias antes: aviso de atenção.
  - 1 dia antes: notificação urgente via e-mail.
- Tela de reconexão simples: botão "Reconectar" que guia o usuário pelo fluxo.

---

## 5. Tabela de integrações no banco

```sql
CREATE TABLE integrations (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id      UUID NOT NULL REFERENCES stores(id),
  provider      VARCHAR(50) NOT NULL, -- 'asaas', 'evolution', 'plugnotas'
  status        VARCHAR(20) DEFAULT 'connected', -- connected|disconnected|expired
  token_enc     TEXT,                -- token criptografado
  expires_at    TIMESTAMP,
  last_check_at TIMESTAMP,
  meta          JSONB DEFAULT '{}',  -- dados extras por provedor
  created_at    TIMESTAMP DEFAULT NOW(),
  updated_at    TIMESTAMP DEFAULT NOW()
);
```
