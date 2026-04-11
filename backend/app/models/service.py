import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, Boolean, ForeignKey
from sqlalchemy import UUID
from app.database import Base

class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    duration = Column(Integer, nullable=False) # em minutos
    price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
