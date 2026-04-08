# Skill: SQLAlchemy + Alembic

## Contexto
Todos os models usam SQLAlchemy 2.0 com sintaxe declarativa moderna.
Migrations gerenciadas pelo Alembic. Banco: PostgreSQL 15.

---

## Padrao de Model

```python
# app/models/product.py
from sqlalchemy import String, Boolean, Integer, Numeric, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Product(Base):
    __tablename__ = "products"

    # Chave primaria sempre UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Sempre incluir store_id
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    cost_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sale_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_qty: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    expires_at: Mapped[str | None] = mapped_column(Date, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Soft delete - nunca deletar
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(server_default=func.now())

    # Relacionamentos
    store: Mapped["Store"] = relationship(back_populates="products")
    stock_movements: Mapped[list["StockMovement"]] = relationship(back_populates="product")
```

## Base Declarativa
```python
# app/core/database.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

---

## Alembic: Criar Migration

```bash
# Gerar migration automatica apos criar/editar um model
alembic revision --autogenerate -m "add products table"

# Aplicar migrations
alembic upgrade head

# Reverter ultima migration
alembic downgrade -1

# Ver historico
alembic history
```

## alembic/env.py (configuracao padrao)
```python
from app.core.database import Base
from app.models import user, store, product, sale, appointment, client, pet  # importar TODOS os models

target_metadata = Base.metadata
```

---

## Queries Comuns

### Buscar com filtros
```python
from sqlalchemy import select, and_, or_

# Sempre filtrar por store_id
query = select(Product).where(
    and_(
        Product.store_id == store_id,
        Product.is_active == True,
        Product.category == category if category else True
    )
)
result = await db.execute(query)
products = result.scalars().all()
```

### Buscar por ID com validacao
```python
async def get_or_404(db: AsyncSession, model, id: UUID, store_id: UUID):
    result = await db.execute(
        select(model).where(
            and_(model.id == id, model.store_id == store_id, model.is_active == True)
        )
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail={"detail": "Nao encontrado", "code": "NOT_FOUND"})
    return obj
```

### Atualizar campos
```python
async def update(db: AsyncSession, product: Product, data: ProductUpdate) -> Product:
    # Atualizar apenas campos enviados (exclude_unset)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    return product
```

### Soft delete
```python
async def delete(db: AsyncSession, product: Product):
    product.is_active = False  # Nunca db.delete(product)
    await db.commit()
```

### Contar registros
```python
from sqlalchemy import func, select

count_query = select(func.count()).select_from(Product).where(
    and_(Product.store_id == store_id, Product.is_active == True)
)
count = await db.scalar(count_query)
```

---

## Regras Desta Skill

1. **Sempre usar Mapped[] typing** na definicao de colunas (SQLAlchemy 2.0)
2. **UUID como PK** com `default=uuid.uuid4`
3. **store_id obrigatorio** em todos os models (exceto stores e users)
4. **Nunca usar db.delete()** - sempre `is_active = False`
5. **Importar todos os models em env.py** para o Alembic detectar mudancas
6. **Usar `exclude_unset=True`** no update para nao sobrescrever campos nao enviados
7. **Indices** para colunas de busca frequente (store_id, created_at, status)

---

## Migration Template
```python
# alembic/versions/xxxx_add_products_table.py
def upgrade() -> None:
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('stores.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()')),
    )
    op.create_index('idx_products_store', 'products', ['store_id'])

def downgrade() -> None:
    op.drop_index('idx_products_store')
    op.drop_table('products')
```
