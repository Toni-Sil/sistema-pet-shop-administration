import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Enum, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class QuartoStatus(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"

class HospedagemStatus(str, enum.Enum):
    PLANNED = "planned"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"

class Quarto(Base):
    """
    Representa uma vaga ou quarto físico no hotel/creche.
    """
    __tablename__ = "hotel_quartos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    name = Column(String, nullable=False)  # Ex: "Canil Luxo 01"
    tipo = Column(String)  # Ex: "Cachorro Pequeno", "Gato", "Suíte"
    status = Column(Enum(QuartoStatus), default=QuartoStatus.AVAILABLE)
    preco_diaria = Column(Numeric(10, 2), default=0.0)
    capacidade = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Hospedagem(Base):
    """
    Representa o registro de uma estadia (Check-in/Out).
    """
    __tablename__ = "hotel_hospedagens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False)
    pet_id = Column(UUID(as_uuid=True), ForeignKey("pets.id"), nullable=False)
    quarto_id = Column(UUID(as_uuid=True), ForeignKey("hotel_quartos.id"), nullable=False)
    
    pet = relationship("Pet")
    
    check_in_previsto = Column(DateTime, nullable=False)
    check_out_previsto = Column(DateTime, nullable=False)
    
    check_in_real = Column(DateTime)
    check_out_real = Column(DateTime)
    
    status = Column(Enum(HospedagemStatus), default=HospedagemStatus.PLANNED)
    
    valor_diaria = Column(Numeric(10, 2), nullable=False)
    valor_total = Column(Numeric(10, 2), default=0.0)
    
    # Detalhes específicos da estadia
    alimentacao = Column(Text)
    medicamentos = Column(Text)
    observacoes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class HospedagemDiario(Base):
    """
    Registros diários de monitoramento do pet durante a estadia.
    """
    __tablename__ = "hotel_hospedagem_diario"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospedagem_id = Column(UUID(as_uuid=True), ForeignKey("hotel_hospedagens.id"), nullable=False)
    
    nota = Column(Text, nullable=False)
    fotos = Column(JSON, default=list) # URLs de fotos do dia
    
    created_at = Column(DateTime, default=datetime.utcnow)
