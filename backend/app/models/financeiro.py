import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Boolean, Date, ForeignKey, Text
from sqlalchemy import UUID

from app.database import Base

class Despesa(Base):
    __tablename__ = "expenses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String(50), nullable=False)
    due_date = Column(Date, nullable=False)
    paid_at = Column(Date)
    is_paid = Column(Boolean, default=False)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class CaixaSession(Base):
    __tablename__ = "cashier_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    opening_balance = Column(Numeric(10, 2), nullable=False)
    closing_balance = Column(Numeric(10, 2))
    total_sales = Column(Numeric(10, 2))
    notes = Column(Text)
    
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)
