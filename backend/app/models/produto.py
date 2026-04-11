import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric, Integer, Date, ForeignKey, Index
from sqlalchemy import UUID

from app.database import Base

class Produto(Base):
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), index=True)
    codigo_barras = Column(String(100), index=True)
    category = Column(String(50), nullable=False, index=True)
    
    sale_type = Column(String(20), default='UNIT')
    cost_price = Column(Numeric(10, 2), nullable=False)
    sale_price = Column(Numeric(10, 2), nullable=False)
    
    quantity = Column(Integer)
    min_qty = Column(Integer, default=5)
    
    weight_in_stock = Column(Numeric(10, 3))
    min_weight = Column(Numeric(10, 3), default=0.5)
    
    unit = Column(String(20), default='un')
    expires_at = Column(Date)
    image_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_products_codigo_barras_store', 'codigo_barras', 'store_id'),
    )
