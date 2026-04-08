# 05 - Arquitetura Tecnica

---

## Stack Tecnologica

### Backend
```
Linguagem:    Python 3.11+
Framework:    FastAPI
ORM:          SQLAlchemy + Alembic (migrations)
Validacao:    Pydantic v2
Auth:         JWT (python-jose) + MFA (TOTP)
Tasks:        APScheduler (jobs agendados)
HTTP Client:  httpx (async)
Testes:       pytest + pytest-asyncio
```

### Frontend
```
Framework:    React 18 + TypeScript
Build:        Vite
UI:           Tailwind CSS + shadcn/ui
Estado:       Zustand
Formularios:  React Hook Form + Zod
Graficos:     Recharts
Calendario:   FullCalendar
HTTP:         Axios
Testes:       Vitest + Testing Library
```

### Banco de Dados
```
Principal:    PostgreSQL 15
Cache:        Redis (sessoes, rate limit)
Migracoes:    Alembic
Backup:       pg_dump automatico diario
```

### Integrações Externas
```
Pix/Pagamento:  Asaas API
WhatsApp:       Evolution API (self-hosted)
Email:          SMTP (Resend ou Gmail SMTP)
Storage:        MinIO (self-hosted) ou S3
IA:             OpenAI API (GPT-4o mini)
```

### Infraestrutura
```
Containers:   Docker + Docker Compose
Deploy:       Dokploy (VPS Hostinger)
Proxy:        Traefik (SSL automatico)
CI/CD:        GitHub Actions
Monitor:      Uptime Kuma
```

---

## Estrutura de Pastas

### Backend
```
backend/
  app/
    api/
      routes/
        auth.py
        products.py
        stock.py
        sales.py
        appointments.py
        clients.py
        pets.py
        reports.py
    core/
      config.py       # Variaveis de ambiente
      security.py     # JWT, hash de senha
      database.py     # Conexao PostgreSQL
    models/
      user.py
      store.py
      product.py
      sale.py
      appointment.py
      client.py
      pet.py
    schemas/
      product.py
      sale.py
      appointment.py
    services/
      stock_service.py
      payment_service.py   # Asaas
      whatsapp_service.py  # Evolution API
      ai_service.py        # OpenAI
    jobs/
      reminders.py         # Lembretes WhatsApp
      stock_alerts.py      # Alertas de estoque
      vaccine_alerts.py    # Alertas de vacinas
  alembic/               # Migrations
  tests/
  main.py
  requirements.txt
  Dockerfile
```

### Frontend
```
frontend/
  src/
    pages/
      dashboard/
      stock/
      financial/
      appointments/
      clients/
      reports/
    components/
      ui/              # shadcn/ui components
      stock/
      financial/
      appointments/
      shared/
    hooks/
    stores/            # Zustand
    services/          # API calls
    types/
  public/
  index.html
  vite.config.ts
  Dockerfile
```

---

## Docker Compose

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
      - ASAAS_API_KEY=${ASAAS_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on: [db, redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]

  db:
    image: postgres:15
    volumes: [pgdata:/var/lib/postgresql/data]
    environment:
      POSTGRES_DB: petshop
      POSTGRES_USER: petshop
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  redis:
    image: redis:7-alpine

  evolution:
    image: atendai/evolution-api:latest
    ports: ["8080:8080"]

volumes:
  pgdata:
```

---

## Fluxo de Autenticacao

```
1. POST /auth/login  {email, password}
2. Backend valida senha (bcrypt)
3. Se MFA ativo: retorna {mfa_required: true}
4. POST /auth/mfa   {totp_code}
5. Backend retorna {access_token, refresh_token}
6. Frontend armazena tokens em memoria (nao localStorage)
7. Refresh automatico a cada 55 minutos
```

---

## Fluxo de Venda com Pix

```
1. Funcionario seleciona produtos no PDV
2. POST /api/sales  (cria venda com status 'pending')
3. POST /api/payments/pix  (cria cobranca no Asaas)
4. Asaas retorna QR Code + payload Pix
5. Frontend exibe QR Code na tela
6. Cliente paga pelo app do banco
7. Asaas dispara webhook -> POST /webhooks/asaas
8. Backend atualiza venda para 'paid'
9. Backend baixa estoque automaticamente
10. Frontend notifica funcionario (WebSocket ou polling)
```

---

## Seguranca

- Todas as rotas autenticadas com JWT Bearer Token
- Senha armazenada com bcrypt (cost factor 12)
- MFA via TOTP (Google Authenticator compativel)
- Rate limiting: 100 req/min por IP (Redis)
- CORS configurado apenas para dominio da aplicacao
- Logs de auditoria para acoes criticas (venda, exclusao, login)
- HTTPS forcado via Traefik + Let's Encrypt

---

## Variaveis de Ambiente (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@db:5432/petshop

# Auth
SECRET_KEY=seu_secret_key_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Asaas (Pix)
ASSAS_API_KEY=sua_chave_asaas
ASSAS_WEBHOOK_TOKEN=token_webhook

# OpenAI
OPENAI_API_KEY=sk-...

# Evolution API (WhatsApp)
EVOLUTION_API_URL=http://evolution:8080
EVOLUTION_API_KEY=sua_chave

# Redis
REDIS_URL=redis://redis:6379

# Storage
MINIO_URL=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```
