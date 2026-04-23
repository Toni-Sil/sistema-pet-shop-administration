import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, Text
from sqlalchemy import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class Venda(Base):
    __tablename__ = "sales"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    cashier_id = Column(UUID(as_uuid=True), ForeignKey("cashier_sessions.id"))
    
    total = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(10, 2), default=0)
    payment_method = Column(String(20), nullable=False)
    payment_status = Column(String(20), default='pending')
    
    asaas_charge_id = Column(String(255))
    pix_qr_code = Column(Text)
    notes = Column(Text)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    items = relationship("ItemVenda", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("VendaPagamento", back_populates="sale", cascade="all, delete-orphan")

class VendaPagamento(Base):
    __tablename__ = "sale_payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    
    method = Column(String(20), nullable=False) # pix, cash, credit_card, debit_card
    amount = Column(Numeric(10, 2), nullable=False)
    fee_amount = Column(Numeric(10, 2), default=0) # Valor da taxa da maquininha
    net_amount = Column(Numeric(10, 2), nullable=False) # Valor líquido (recebido)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sale = relationship("Venda", back_populates="payments")

class ItemVenda(Base):
    __tablename__ = "sale_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    pacote_id = Column(UUID(as_uuid=True), ForeignKey("pacotes.id"), nullable=True)
    quantity = Column(Integer)
    weight = Column(Numeric(10, 3))
    unit_price = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    
    sale = relationship("Venda", back_populates="items")
