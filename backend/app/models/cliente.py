import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Date, ForeignKey
from sqlalchemy import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Cliente(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255))
    phone = Column(String(20), nullable=False)
    cpf = Column(String(14))
    address = Column(Text)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pets = relationship("Pet", back_populates="client", cascade="all, delete-orphan")


class Pet(Base):
    __tablename__ = "pets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    species = Column(String(50), default="dog")  # dog, cat, bird, other
    breed = Column(String(100))
    birth_date = Column(Date)
    weight = Column(String(20))
    color = Column(String(50))
    photo_url = Column(Text)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Cliente", back_populates="pets")
    appointments = relationship("Agendamento", back_populates="pet")
