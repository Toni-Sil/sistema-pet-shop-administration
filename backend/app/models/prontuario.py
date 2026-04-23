import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy import UUID
from app.database import Base

class Prontuario(Base):
    """
    Representa uma consulta clínica ou prontuário estruturado para o Pet.
    """
    __tablename__ = "prontuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pet_id = Column(UUID(as_uuid=True), ForeignKey("pets.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Campos estruturados da consulta
    anamnese = Column(Text)
    exame_fisico = Column(Text)
    suspeita_diagnostica = Column(Text)
    prescricao = Column(Text)
    
    # Lista de URLs para anexos/exames
    attachments = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
