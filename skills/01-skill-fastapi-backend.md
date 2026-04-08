# Skill: FastAPI Backend

## Contexto do Projeto
Este e um sistema de administracao para pet shops construido com FastAPI + PostgreSQL.
Cada endpoint deve ser isolado por `store_id` (uma instancia por loja).

---

## Padroes Obrigatorios

### Estrutura de um Router
```python
# app/api/routes/products.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=list[ProductResponse])
async def list_products(
    category: str | None = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista produtos da loja com paginacao e filtros."""
    return await ProductService.list(db, current_user.store_id, category, page, limit)

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cadastra novo produto."""
    return await ProductService.create(db, current_user.store_id, data)
```

### Formato de Erro Padrao
```python
# Sempre retornar neste formato
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={"detail": "Produto nao encontrado", "code": "PRODUCT_NOT_FOUND"}
)
```

### Estrutura de Service
```python
# app/services/product_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.product import Product
from app.schemas.product import ProductCreate
from uuid import UUID

class ProductService:

    @staticmethod
    async def list(db: AsyncSession, store_id: UUID, category: str | None, page: int, limit: int):
        # Sempre filtrar por store_id
        query = select(Product).where(
            and_(
                Product.store_id == store_id,
                Product.is_active == True
            )
        )
        if category:
            query = query.where(Product.category == category)
        query = query.offset((page - 1) * limit).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, store_id: UUID, data: ProductCreate) -> Product:
        product = Product(store_id=store_id, **data.model_dump())
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product
```

### Schema Pydantic v2
```python
# app/schemas/product.py
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class ProductBase(BaseModel):
    name: str
    sku: str | None = None
    category: str
    cost_price: Decimal
    sale_price: Decimal
    min_qty: int = 5

    @field_validator('sale_price')
    @classmethod
    def sale_price_must_be_positive(cls, v, info):
        if v <= 0:
            raise ValueError('Preco de venda deve ser maior que zero')
        return v

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    name: str | None = None
    category: str | None = None

class ProductResponse(ProductBase):
    id: UUID
    store_id: UUID
    quantity: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

### Registro do Router no main.py
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, products, stock, sales, appointments, clients, pets

app = FastAPI(title="Sistema Pet Shop", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(products.router, prefix="/api")
app.include_router(stock.router, prefix="/api/stock")
app.include_router(sales.router, prefix="/api")
app.include_router(appointments.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(pets.router, prefix="/api")
```

### Conexao Async com PostgreSQL
```python
# app/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### Config com Pydantic Settings
```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ASAAS_API_KEY: str
    OPENAI_API_KEY: str
    EVOLUTION_API_URL: str
    EVOLUTION_API_KEY: str
    REDIS_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Regras Desta Skill

1. **Sempre usar async/await** - nenhuma funcao sincrona nos endpoints
2. **Sempre passar store_id via current_user** - nunca aceitar store_id do body da requisicao
3. **Services separados** - logica de negocio nunca fica no router
4. **Paginacao padrao** - todas as listagens com `page` e `limit`
5. **Soft delete sempre** - `is_active = False`, nunca `DELETE` no banco
6. **Erros com codigo** - sempre incluir `code` no detail do HTTPException
7. **Documentar com docstring** - resumo em portugues em cada endpoint

---

## requirements.txt Base
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
alembic==1.13.0
pydantic==2.8.0
pydantic-settings==2.4.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.0
redis==5.0.8
pyotp==2.9.0
apscheduler==3.10.4
python-multipart==0.0.9
```
