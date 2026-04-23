import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Integer, ForeignKey, Boolean
from sqlalchemy import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class Pacote(Base):
    __tablename__ = "pacotes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Itens que compõem o pacote (ex: 4 banhos)
    items = relationship("PacoteItem", back_populates="pacote", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.utcnow)

class PacoteItem(Base):
    __tablename__ = "pacote_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pacote_id = Column(UUID(as_uuid=True), ForeignKey("pacotes.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    
    pacote = relationship("Pacote", back_populates="items")

class ClientePacote(Base):
    """
    Controla o saldo de serviços que um cliente possui após comprar um pacote.
    Ex: Se comprou um pacote de 4 banhos, terá um registro aqui com balance=4 para o service_id de banho.
    """
    __tablename__ = "cliente_pacotes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    
    balance = Column(Integer, default=0) # Saldo restante de utilizações
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
