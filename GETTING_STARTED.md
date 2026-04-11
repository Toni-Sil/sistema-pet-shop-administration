# Sistema Pet Shop Administration — Guia de Inicialização

## Requisitos
- Python 3.10+
- Node.js 18+
- PostgreSQL 15+ OU Docker

---

## Opção 1 — Docker (recomendado)

```bash
# Na raiz do projeto:
docker compose up --build
```

Acesse: **http://localhost:3000**

---

## Opção 2 — Desenvolvimento Local

### Backend

```bash
cd backend

# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Criar .env a partir do exemplo
cp .env.example .env
# Edite .env com suas credenciais do PostgreSQL

# Rodar migrations
alembic upgrade head

# Popular banco com dados de demonstração (opcional)
python seed.py

# Subir API
uvicorn app.main:app --reload
```

API disponível em: **http://localhost:8000**
Documentação interativa: **http://localhost:8000/api/v1/openapi.json**

### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Subir servidor de desenvolvimento
npm run dev
```

Frontend disponível em: **http://localhost:5173**

---

## Credenciais de Demo (após rodar seed.py)

| Campo | Valor |
|-------|-------|
| E-mail | `admin@demo.com` |
| Senha | `admin123` |

---

## Endpoints Principais da API

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/register` | Criar loja + admin |
| POST | `/api/v1/auth/login` | Login (retorna JWT) |
| GET | `/api/v1/produtos` | Listar produtos |
| POST | `/api/v1/vendas` | Realizar venda |
| GET | `/api/v1/clientes` | Listar clientes |
| GET | `/api/v1/agendamentos` | Listar agendamentos |
| GET | `/api/v1/despesas` | Listar despesas |
| GET | `/api/v1/settings/loja` | Dados da loja logada |
