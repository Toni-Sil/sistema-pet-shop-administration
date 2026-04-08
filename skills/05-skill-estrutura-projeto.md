# Skill: Estrutura de Projeto

## Objetivo
Padronizar a estrutura de pastas e arquivos do backend FastAPI e frontend Next.js para o sistema pet shop, seguindo SDD e boas praticas de organizacao.

## Estrutura Backend (FastAPI)

```
pet-shop-api/
  app/
    __init__.py
    main.py              # Entry point FastAPI
    database.py          # Conexao SQLAlchemy
    env.py               # Importar todos os models (para Alembic)

    core/
      __init__.py
      config.py          # Settings / variaveis de ambiente
      security.py        # JWT, hash de senha
      deps.py            # Dependencias FastAPI (get_current_user, etc)

    models/              # SQLAlchemy ORM models
      __init__.py
      store.py
      usuario.py
      produto.py
      categoria.py
      estoque.py
      venda.py
      financeiro.py

    schemas/             # Pydantic schemas
      __init__.py
      auth.py
      usuario.py
      produto.py
      categoria.py
      estoque.py
      venda.py
      financeiro.py

    services/            # Logica de negocio
      __init__.py
      produto_service.py
      estoque_service.py
      venda_service.py
      financeiro_service.py
      relatorio_service.py

    routers/             # Endpoints FastAPI
      __init__.py
      auth.py
      produtos.py
      categorias.py
      estoque.py
      vendas.py
      financeiro.py
      relatorios.py
      usuarios.py

  alembic/               # Migrations
    versions/
    env.py
    alembic.ini

  tests/
    __init__.py
    conftest.py
    test_produtos.py
    test_estoque.py
    test_financeiro.py
    test_auth.py

  .env
  .env.example
  requirements.txt
  Dockerfile
  docker-compose.yml
  README.md
```

## Arquivo main.py

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, produtos, categorias, estoque, vendas, financeiro, relatorios, usuarios
from app.core.config import settings

app = FastAPI(
    title='Sistema Pet Shop API',
    description='API para gerenciamento de pet shops',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Prefixo global
API_PREFIX = '/api/v1'

# Registrar routers
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(produtos.router, prefix=API_PREFIX)
app.include_router(categorias.router, prefix=API_PREFIX)
app.include_router(estoque.router, prefix=API_PREFIX)
app.include_router(vendas.router, prefix=API_PREFIX)
app.include_router(financeiro.router, prefix=API_PREFIX)
app.include_router(relatorios.router, prefix=API_PREFIX)
app.include_router(usuarios.router, prefix=API_PREFIX)

@app.get('/health')
async def health_check():
    return {'status': 'ok', 'version': '1.0.0'}
```

## Arquivo database.py

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Arquivo env.py (para Alembic)

```python
# app/env.py
# IMPORTANTE: importar TODOS os models aqui para Alembic detectar
from app.database import Base
from app.models.store import Store
from app.models.usuario import Usuario
from app.models.produto import Produto
from app.models.categoria import Categoria
from app.models.estoque import MovimentacaoEstoque
from app.models.venda import Venda, ItemVenda
from app.models.financeiro import Transacao

__all__ = ['Base']
```

## Padrao de Service

```python
# app/services/produto_service.py
from sqlalchemy.orm import Session
from app.models.produto import Produto
from app.schemas.produto import ProdutoCreate, ProdutoUpdate
from fastapi import HTTPException, status
import uuid

def listar(db: Session, store_id: uuid.UUID, skip: int = 0, limit: int = 50):
    return db.query(Produto).filter(
        Produto.store_id == store_id,
        Produto.is_active == True
    ).offset(skip).limit(limit).all()

def buscar_por_id(db: Session, id: uuid.UUID, store_id: uuid.UUID):
    produto = db.query(Produto).filter(
        Produto.id == id,
        Produto.store_id == store_id
    ).first()
    if not produto:
        raise HTTPException(status_code=404, detail='Produto nao encontrado')
    return produto

def criar(db: Session, dados: ProdutoCreate, store_id: uuid.UUID):
    produto = Produto(**dados.model_dump(), store_id=store_id)
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto

def atualizar(db: Session, id: uuid.UUID, dados: ProdutoUpdate, store_id: uuid.UUID):
    produto = buscar_por_id(db, id, store_id)
    update_data = dados.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(produto, key, value)
    db.commit()
    db.refresh(produto)
    return produto

def deletar(db: Session, id: uuid.UUID, store_id: uuid.UUID):
    produto = buscar_por_id(db, id, store_id)
    produto.is_active = False  # Soft delete
    db.commit()
    return {'message': 'Produto desativado com sucesso'}
```

## Padrao de Router

```python
# app/routers/produtos.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_any_role, get_gerente_ou_admin, get_current_store_id
from app.schemas.produto import ProdutoCreate, ProdutoUpdate, ProdutoResponse, ProdutoList
from app.services import produto_service
from app.models.usuario import Usuario
import uuid

router = APIRouter(prefix='/produtos', tags=['Produtos'])

@router.get('', response_model=ProdutoList)
async def listar_produtos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_any_role),
    store_id: uuid.UUID = Depends(get_current_store_id)
):
    items = produto_service.listar(db, store_id, skip, limit)
    return ProdutoList(items=items, total=len(items), page=1, per_page=limit, pages=1)

@router.get('/{id}', response_model=ProdutoResponse)
async def buscar_produto(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_any_role),
    store_id: uuid.UUID = Depends(get_current_store_id)
):
    return produto_service.buscar_por_id(db, id, store_id)

@router.post('', response_model=ProdutoResponse, status_code=201)
async def criar_produto(
    produto: ProdutoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_gerente_ou_admin),
    store_id: uuid.UUID = Depends(get_current_store_id)
):
    return produto_service.criar(db, produto, store_id)

@router.patch('/{id}', response_model=ProdutoResponse)
async def atualizar_produto(
    id: uuid.UUID,
    produto: ProdutoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_gerente_ou_admin),
    store_id: uuid.UUID = Depends(get_current_store_id)
):
    return produto_service.atualizar(db, id, produto, store_id)

@router.delete('/{id}')
async def deletar_produto(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_gerente_ou_admin),
    store_id: uuid.UUID = Depends(get_current_store_id)
):
    return produto_service.deletar(db, id, store_id)
```

## Estrutura Frontend (Next.js)

```
pet-shop-frontend/
  app/
    (auth)/
      login/
        page.tsx
    (dashboard)/
      layout.tsx           # Layout com sidebar
      page.tsx             # Dashboard principal
      produtos/
        page.tsx           # Lista de produtos
        novo/page.tsx
        [id]/page.tsx      # Editar produto
      estoque/
        page.tsx
        movimentacoes/page.tsx
      vendas/
        page.tsx
        nova/page.tsx
      financeiro/
        page.tsx
        transacoes/page.tsx
      relatorios/
        page.tsx
      usuarios/
        page.tsx
      configuracoes/
        page.tsx

  components/
    ui/                    # shadcn/ui components
    layout/
      Sidebar.tsx
      Header.tsx
      PageTitle.tsx
    produtos/
      ProdutoTable.tsx
      ProdutoForm.tsx
      ProdutoCard.tsx
    estoque/
      EstoqueAlert.tsx
      MovimentacaoForm.tsx
    financeiro/
      TransacaoForm.tsx
      FinanceiroChart.tsx
    shared/
      DataTable.tsx
      ConfirmDialog.tsx
      LoadingSpinner.tsx
      EmptyState.tsx

  lib/
    api.ts                 # Axios instance configurado
    auth.ts                # Helpers de autenticacao
    utils.ts               # Utilitarios gerais
    formatters.ts          # Formatacao de moeda, datas

  hooks/
    useProdutos.ts
    useEstoque.ts
    useAuth.ts
    useFinanceiro.ts

  types/
    index.ts               # TypeScript types/interfaces

  .env.local
  package.json
  tailwind.config.ts
  next.config.ts
```

## Regras de Organizacao

1. **Services contem toda logica de negocio** - routers apenas orquestram
2. **Schemas separados de models** - nunca misturar ORM com validacao
3. **Um arquivo por recurso** - produtos.py, estoque.py, etc
4. **Imports relativos dentro do app** - `from app.models.produto import Produto`
5. **Prefixo de versao na API** - `/api/v1/` para facilitar futuras versoes
