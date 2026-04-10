# 15 - Atualização do Sistema sem Derrubar a Loja

## Objetivo

Garantir que atualizações do sistema sejam aplicadas sem interromper o funcionamento do pet shop, especialmente durante o horário comercial.

---

## 1. Estratégia geral

- **Blue-Green Deploy** ou **Rolling Update** via Docker/Dokploy.
- Nova versão sobe em paralelo; tráfego é migrado somente após health check passar.
- Em caso de falha na nova versão: rollback automático para versão anterior em menos de 1 minuto.

---

## 2. Fluxo de deploy

```
1. Build da nova imagem Docker (CI/CD via GitHub Actions)
2. Push da imagem para registry
3. Dokploy detecta nova imagem ou recebe webhook
4. Sobe novo container (mantendo o atual ativo)
5. Health check no novo container:
   GET /health → 200 OK
6. Se OK: migrar tráfego para novo container
7. Desligar container antigo
8. Se falha no health check: manter container antigo, alertar desenvolvedor
```

---

## 3. Migrações de banco de dados

- Migrações **sempre compatíveis com versão anterior** (backward compatible):
  - Adicionar coluna: sempre com valor DEFAULT.
  - Remover coluna: deprecar primeiro, remover só na versão seguinte.
  - Renomear: criar coluna nova, migrar dados, remover antiga em etapa separada.
- Ferramenta: Alembic (FastAPI/Python) com versionamento explícito.
- Migração executada automaticamente no início do deploy, antes de trocar o tráfego.

---

## 4. Janela de manutenção (apenas para mudanças críticas)

- Para mudanças que exigem downtime inevitável (ex.: reestruturação completa de schema):
  - Agendar para **domingo entre 02h e 05h**.
  - Notificar donos de loja com **48h de antecedência** via e-mail e WhatsApp.
  - Exibir página de manutenção com tempo estimado.

---

## 5. Rollback

- Toda versão deployada tem tag de imagem Docker versionada (ex.: `v1.2.3`).
- Rollback manual: `dokploy rollback` ou alterar tag no docker-compose e fazer redeploy.
- Rollback de banco: via restore de backup pontual (ver doc 14).
