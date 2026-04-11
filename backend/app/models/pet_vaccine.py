import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Date, ForeignKey
from sqlalchemy import UUID
from app.database import Base

class PetVaccine(Base):
    __tablename__ = "pet_vaccines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pet_id = Column(UUID(as_uuid=True), ForeignKey("pets.id"), nullable=False, index=True)
    vaccine = Column(String(100), nullable=False)
    applied_at = Column(Date, nullable=False)
    next_dose = Column(Date)
    notes = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
