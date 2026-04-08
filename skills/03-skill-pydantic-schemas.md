# Skill: Pydantic Schemas

## Objetivo
Definir como criar e organizar schemas Pydantic para validacao de dados, serialização e documentacao automatica no FastAPI.

## Regras Fundamentais

1. **Sempre separar schemas por operacao**: `Create`, `Update`, `Response`, `List`
2. **Nunca expor campos sensiveis** no schema de Response (senhas, tokens internos)
3. **Usar `model_config` com `from_attributes=True`** para compatibilidade com ORM
4. **Campos opcionais no Update** sempre com `Optional` e default `None`
5. **Validadores customizados** com `@field_validator` para regras de negocio

## Estrutura de Schemas por Modulo

```
app/
  schemas/
    __init__.py
    produto.py
    categoria.py
    estoque.py
    venda.py
    financeiro.py
    usuario.py
    auth.py
```

## Padroes de Schema

### Schema Base
```python
from pydantic import BaseModel, field_validator, UUID4
from typing import Optional
from datetime import datetime
import uuid

class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    categoria_id: UUID4

    @field_validator('preco')
    @classmethod
    def preco_positivo(cls, v):
        if v <= 0:
            raise ValueError('Preco deve ser maior que zero')
        return round(v, 2)

    @field_validator('nome')
    @classmethod
    def nome_nao_vazio(cls, v):
        if not v.strip():
            raise ValueError('Nome nao pode ser vazio')
        return v.strip()
```

### Schema Create
```python
class ProdutoCreate(ProdutoBase):
    codigo_barras: Optional[str] = None
    estoque_minimo: int = 0
    estoque_atual: int = 0
```

### Schema Update (campos opcionais)
```python
class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    categoria_id: Optional[UUID4] = None
    codigo_barras: Optional[str] = None
    estoque_minimo: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator('preco')
    @classmethod
    def preco_positivo(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Preco deve ser maior que zero')
        return v
```

### Schema Response
```python
class ProdutoResponse(ProdutoBase):
    id: UUID4
    codigo_barras: Optional[str]
    estoque_minimo: int
    estoque_atual: int
    is_active: bool
    store_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {'from_attributes': True}
```

### Schema List (paginado)
```python
from typing import List

class ProdutoList(BaseModel):
    items: List[ProdutoResponse]
    total: int
    page: int
    per_page: int
    pages: int
```

## Schemas de Estoque

```python
class MovimentacaoCreate(BaseModel):
    produto_id: UUID4
    tipo: str  # 'entrada' | 'saida' | 'ajuste'
    quantidade: int
    motivo: Optional[str] = None
    custo_unitario: Optional[float] = None

    @field_validator('tipo')
    @classmethod
    def tipo_valido(cls, v):
        tipos = ['entrada', 'saida', 'ajuste']
        if v not in tipos:
            raise ValueError(f'Tipo deve ser um de: {tipos}')
        return v

    @field_validator('quantidade')
    @classmethod
    def quantidade_positiva(cls, v):
        if v <= 0:
            raise ValueError('Quantidade deve ser maior que zero')
        return v

class MovimentacaoResponse(MovimentacaoCreate):
    id: UUID4
    store_id: UUID4
    usuario_id: UUID4
    created_at: datetime

    model_config = {'from_attributes': True}
```

## Schemas Financeiros

```python
from enum import Enum

class TipoTransacao(str, Enum):
    receita = 'receita'
    despesa = 'despesa'

class StatusPagamento(str, Enum):
    pendente = 'pendente'
    pago = 'pago'
    cancelado = 'cancelado'

class TransacaoCreate(BaseModel):
    tipo: TipoTransacao
    valor: float
    descricao: str
    categoria: str
    data_vencimento: Optional[datetime] = None
    status: StatusPagamento = StatusPagamento.pendente

class TransacaoResponse(TransacaoCreate):
    id: UUID4
    store_id: UUID4
    created_at: datetime

    model_config = {'from_attributes': True}
```

## Schemas de Auth

```python
class LoginRequest(BaseModel):
    email: str
    senha: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    expires_in: int

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str
    role: str = 'funcionario'  # 'admin' | 'gerente' | 'funcionario'

class UsuarioResponse(BaseModel):
    id: UUID4
    nome: str
    email: str
    role: str
    is_active: bool
    store_id: UUID4
    created_at: datetime

    model_config = {'from_attributes': True}
```

## Boas Praticas

1. **Importar schemas no `__init__.py`** para facilitar imports
2. **Usar Enums** para campos com valores fixos (tipo, status, role)
3. **Documentar campos** com `Field(description='...')` para Swagger
4. **Nunca retornar senha** mesmo hasheada no Response
5. **Validar UUIDs** usando `UUID4` do pydantic, nao `str`

## Exemplo com Field e documentacao

```python
from pydantic import BaseModel, Field

class ProdutoCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255, description='Nome do produto')
    preco: float = Field(..., gt=0, description='Preco de venda em reais')
    estoque_atual: int = Field(default=0, ge=0, description='Quantidade atual em estoque')
    estoque_minimo: int = Field(default=5, ge=0, description='Alerta de estoque baixo')
```
