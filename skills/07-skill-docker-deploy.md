# Skill: Docker e Deploy

## Objetivo
Configurar Docker para desenvolvimento local e deploy em producao com Dokploy/VPS, seguindo o padrao ja usado nos projetos existentes.

## Arquivos Necessarios

```
pet-shop-api/
  Dockerfile
  docker-compose.yml
  docker-compose.prod.yml
  .dockerignore
  .env.example
```

## Dockerfile (Backend)

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo
COPY . .

# Variavel de ambiente para producao
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Porta da aplicacao
EXPOSE 8000

# Comando de inicializacao
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## .dockerignore

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
.env
.venv
venv/
.git
.gitignore
.pytest_cache
htmlcov/
*.egg-info
dist/
build/
node_modules/
*.log
alembic/versions/*.pyc
test.db
```

## docker-compose.yml (Desenvolvimento)

```yaml
# docker-compose.yml
version: '3.9'

services:
  api:
    build: .
    container_name: pet-shop-api
    ports:
      - '8000:8000'
    volumes:
      - .:/app  # Hot reload em desenvolvimento
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/petshop
      - SECRET_KEY=dev-secret-key-nao-usar-em-producao
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=480
      - ALLOWED_ORIGINS=http://localhost:3000
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:16-alpine
    container_name: pet-shop-db
    ports:
      - '5432:5432'
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: petshop
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## docker-compose.prod.yml (Producao)

```yaml
# docker-compose.prod.yml
version: '3.9'

services:
  api:
    image: ${DOCKER_IMAGE:-pet-shop-api}:${VERSION:-latest}
    container_name: pet-shop-api
    restart: unless-stopped
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=480
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
    labels:
      # Labels para Traefik (Dokploy)
      - 'traefik.enable=true'
      - 'traefik.http.routers.petshop-api.rule=Host(`api.petshop.com`)'
      - 'traefik.http.routers.petshop-api.tls=true'
      - 'traefik.http.routers.petshop-api.tls.certresolver=letsencrypt'
      - 'traefik.http.services.petshop-api.loadbalancer.server.port=8000'
    networks:
      - traefik-public

networks:
  traefik-public:
    external: true
```

## .env.example

```env
# Banco de dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/petshop

# Seguranca
SECRET_KEY=gerar-com-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://app.petshop.com

# Ambiente
ENVIRONMENT=development
DEBUG=true
```

## requirements.txt

```txt
fastapi==0.111.x
uvicorn[standard]==0.30.x
sqlalchemy==2.0.x
alembic==1.13.x
psycopg2-binary==2.9.x
pydantic==2.7.x
pydantic-settings==2.3.x
python-jose[cryptography]==3.3.x
passlib[bcrypt]==1.7.x
python-multipart==0.0.9
httpx==0.27.x
```

## Comandos Essenciais

```bash
# Iniciar ambiente de desenvolvimento
docker compose up -d

# Ver logs
docker compose logs -f api

# Rodar migrations
docker compose exec api alembic upgrade head

# Criar nova migration
docker compose exec api alembic revision --autogenerate -m 'descricao'

# Acessar shell do container
docker compose exec api bash

# Rodar testes dentro do container
docker compose exec api pytest -v

# Rebuild apos mudar dependencias
docker compose up -d --build api

# Parar tudo
docker compose down

# Parar e remover volumes (reset DB)
docker compose down -v
```

## Deploy com Dokploy

### Configuracao no Dokploy

1. Criar novo projeto no Dokploy
2. Conectar repositorio GitHub
3. Selecionar `docker-compose.prod.yml` como arquivo compose
4. Configurar variaveis de ambiente:
   - `DATABASE_URL` - apontar para PostgreSQL externo ou servico Dokploy
   - `SECRET_KEY` - gerar com `openssl rand -hex 32`
   - `ALLOWED_ORIGINS` - dominio do frontend
5. Configurar dominio e SSL automatico via Traefik
6. Ativar deploy automatico no push para `main`

### Migracao em Producao

```bash
# Rodar migrations antes de iniciar o servico
# Adicionar ao entrypoint ou rodar manualmente:
docker exec pet-shop-api alembic upgrade head
```

## Dockerfile Frontend (Next.js)

```dockerfile
# Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Imagem de producao
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
```

## Boas Praticas

1. **Nunca commitar `.env`** - sempre usar `.env.example`
2. **Healthcheck no postgres** - garantir DB pronto antes da API
3. **Restart policy** - `unless-stopped` em producao
4. **Volumes nomeados** - para persistencia dos dados
5. **Multi-stage build no frontend** - imagem menor em producao
