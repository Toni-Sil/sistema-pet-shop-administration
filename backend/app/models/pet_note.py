import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Text, ForeignKey
from sqlalchemy import UUID
from app.database import Base

class PetNote(Base):
    __tablename__ = "pet_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pet_id = Column(UUID(as_uuid=True), ForeignKey("pets.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
