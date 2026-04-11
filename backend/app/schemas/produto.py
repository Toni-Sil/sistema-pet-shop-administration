from pydantic import BaseModel, ConfigDict, field_validator, field_serializer
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from decimal import Decimal
from enum import Enum

class SaleType(str, Enum):
    UNIT = "UNIT"
    WEIGHT = "WEIGHT"


class Categoria(str, Enum):
    RACAO = "Racao"
    MEDICAMENTO = "Medicamento"
    ACESSORIO = "Acessorio"
    HIGIENE = "Higiene"
    OUTRO = "Outro"


class ProdutoBase(BaseModel):
    name: str
    sku: Optional[str] = None
    codigo_barras: Optional[str] = None
    category: Categoria
    sale_type: SaleType = SaleType.UNIT
    cost_price: Decimal
    sale_price: Decimal
    min_qty: int = 5
    min_weight: Decimal = Decimal("0.5")
    unit: str = 'un'
    expires_at: Optional[date] = None
    image_url: Optional[str] = None
    is_active: bool = True
    
    @field_validator('name')
    @classmethod
    def name_must_be_valid(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Nome deve ter pelo menos 2 caracteres')
        if len(v) > 255:
            raise ValueError('Nome deve ter no máximo 255 caracteres')
        return v.strip()
    
    @field_validator('sale_price')
    @classmethod
    def sale_price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('sale_price deve ser positivo')
        return v
    
    @field_validator('cost_price')
    @classmethod
    def cost_price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('cost_price deve ser positivo')
        return v
    
    @field_validator('category', mode='before')
    @classmethod
    def normalize_category(cls, v):
        if v:
            return v.capitalize()
        return v


class ProdutoCreate(ProdutoBase):
    quantity: Optional[int] = None
    weight_in_stock: Optional[Decimal] = None

class ProdutoUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    codigo_barras: Optional[str] = None
    category: Optional[Categoria] = None
    sale_type: Optional[SaleType] = None
    cost_price: Optional[Decimal] = None
    sale_price: Optional[Decimal] = None
    quantity: Optional[int] = None
    weight_in_stock: Optional[Decimal] = None
    min_qty: Optional[int] = None
    min_weight: Optional[Decimal] = None
    unit: Optional[str] = None
    expires_at: Optional[date] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class ProdutoResponse(BaseModel):
    id: UUID
    store_id: UUID
    quantity: Optional[int] = None
    weight_in_stock: Optional[Decimal] = None
    min_weight: Decimal
    created_at: datetime
    category: str
    
    model_config = ConfigDict(from_attributes=True)
