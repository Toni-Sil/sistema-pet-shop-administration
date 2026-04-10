# 21 - Observabilidade e Monitoramento de Erros

## Objetivo

Garantir que o desenvolvedor saiba quando algo quebrou em produção **antes que o cliente reclame**, com informações suficientes para diagnóstico rápido.

---

## 1. Camadas de observabilidade

| Camada | Ferramenta | O que monitora |
|---|---|---|
| Erros de aplicação | Sentry (plano gratuito) | Exceções Python/JS, stack trace, contexto |
| Logs de container | Docker logs + Loki/Grafana | Stdout/stderr dos serviços |
| Métricas de infra | Netdata ou Grafana | CPU, RAM, disco, rede do VPS |
| Health check | Endpoint `/health` | Status dos serviços e banco |
| Uptime externo | UptimeRobot (gratuito) | Alertas se o sistema ficar fora do ar |

---

## 2. Endpoint de health check

```python
# GET /health
{
  "status": "ok",         # ok | degraded | down
  "database": "ok",
  "redis": "ok",
  "version": "1.2.3",
  "uptime_seconds": 86400
}
```

- Verificado pelo Dokploy para zero downtime deploy.
- Verificado pelo UptimeRobot a cada 1 minuto.

---

## 3. Níveis de alerta

| Nível | Exemplo | Notificação |
|---|---|---|
| Info | Deploy realizado | Log apenas |
| Warning | Backup com atraso, integração instável | E-mail |
| Error | Exceção não tratada, falha de pagamento | E-mail + WhatsApp dev |
| Critical | Sistema fora do ar, banco inacessível | E-mail + WhatsApp imediato |

---

## 4. O que logar por padrão

- Todas as requisições HTTP com: método, rota, status, tempo de resposta.
- Erros com: stack trace completo, usuário (ID), loja (ID), dados de contexto (sem dados sensíveis).
- Operações críticas: pagamento, emissão fiscal, login, alteração de permissões.
- **Nunca logar:** senhas, tokens completos, dados de cartão, dados médicos.

---

## 5. Alertas proativos para o dono da loja

Algumas situações merecem notificação proativa ao dono (via e-mail ou WhatsApp):

- Backup falhou.
- Integração crítica desconectada por mais de 30 minutos.
- Sistema ficou fora do ar.
- Lote de notas fiscais rejeitadas.
- Agente de segurança detectou anomalia crítica.

---

## 6. Rastreamento de erros (Sentry)

- Configurar Sentry no backend (Python/FastAPI) e frontend (React).
- Agrupar erros por tipo, frequência e impacto.
- Configurar alertas para erros novos ou picos de erros conhecidos.
- Dados enviados ao Sentry: stack trace, rota, user_id (sem dados pessoais sensíveis).
