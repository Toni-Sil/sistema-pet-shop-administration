from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
import logging

from app.models.whatsapp_log import WhatsAppLog
from app.models.store import Store

logger = logging.getLogger(__name__)

class WhatsAppService:
    @staticmethod
    async def send_message(db: Session, store_id: UUID, phone: str, message: str):
        # Simula o envio (delay ou print)
        logger.info(f"[WhatsApp SIM] Enviando para {phone}: {message}")
        
        # Registra o log
        log = WhatsAppLog(
            store_id=store_id,
            phone=phone,
            message=message,
            status="sent"
        )
        db.add(log)
        db.commit()
        return True

    @staticmethod
    async def notify_appointment_created(db: Session, store_id: UUID, client_name: str, pet_name: str, service: str, date: str, time: str, phone: str):
        store = db.query(Store).filter(Store.id == store_id).first()
        store_name = store.name if store else "Pet Shop"
        
        msg = (
            f"Olá {client_name}! 🐾\n"
            f"Seu agendamento para o pet *{pet_name}* ({service}) foi solicitado com sucesso para o dia {date} às {time}.\n"
            f"Local: {store_name}\n\n"
            "Qualquer dúvida, entre em contato."
        )
        return await WhatsAppService.send_message(db, store_id, phone, msg)

    @staticmethod
    async def notify_status_change(db: Session, store_id: UUID, client_name: str, pet_name: str, status: str, phone: str):
        label = "Confirmado" if status == "confirmed" else "Cancelado"
        emoji = "✅" if status == "confirmed" else "❌"
        
        msg = f"Olá {client_name}! Seu agendamento para *{pet_name}* está *{label}* {emoji}."
        return await WhatsAppService.send_message(db, store_id, phone, msg)

whatsapp_service = WhatsAppService()
