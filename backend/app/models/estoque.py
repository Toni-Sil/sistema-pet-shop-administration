import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey
from sqlalchemy import UUID

from app.database import Base

class MovimentacaoEstoque(Base):
    __tablename__ = "stock_movements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    
    type = Column(String(10), nullable=False) # 'entry' or 'exit'
    quantity = Column(Integer, nullable=False)
    weight = Column(Numeric(10, 3))

    reason = Column(String(50))
    cost_price = Column(Numeric(10, 2))
    supplier = Column(String(255))
    
    sale_id = Column(UUID(as_uuid=True), nullable=True) # ForeignKey a sales quando existir
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
