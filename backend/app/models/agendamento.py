import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Date, Time, ForeignKey
from sqlalchemy import UUID
from sqlalchemy.orm import relationship
from app.models.service import Service

from app.database import Base


class Agendamento(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)
    pet_id = Column(UUID(as_uuid=True), ForeignKey("pets.id"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), index=True)
    service_legacy = Column(String(100)) # para manter compatibilidade com dados antigos
    professional = Column(String(100))
    date = Column(Date, nullable=False, index=True)
    time = Column(String(10), nullable=False)       # HH:MM
    scheduled_at = Column(DateTime, index=True)     # Data + Hora combinada
    ends_at = Column(DateTime)                      # Horário de término
    status = Column(String(30), default="scheduled")  # scheduled, in_progress, done, absent, cancelled

    price = Column(String(20))
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    pet = relationship("Pet", back_populates="appointments")
    service_rel = relationship("Service")

    @property
    def service(self):
        return self.service_legacy
