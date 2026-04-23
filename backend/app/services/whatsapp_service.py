import httpx
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
import logging

from app.models.whatsapp_log import WhatsAppLog
from app.models.store import Store
from app.core.config import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    @staticmethod
    async def send_message(db: Session, store_id: UUID, phone: str, message: str):
        # 1. Obter configuração da loja ou usar global
        store = db.query(Store).filter(Store.id == store_id).first()
        instance = settings.EVOLUTION_GLOBAL_INSTANCE
        
        # Se a loja tiver uma instância específica no settings (JSON), usamos ela
        if store and store.settings and isinstance(store.settings, dict):
            instance = store.settings.get("evolution_instance", instance)

        status = "pending"
        
        if not settings.EVOLUTION_API_URL or not settings.EVOLUTION_API_KEY or not instance:
            logger.warning("WhatsApp não configurado (URL, API Key ou Instance ausentes). Simulando envio no log.")
            logger.info(f"[WhatsApp SIM] {phone}: {message}")
            status = "simulated"
        else:
            try:
                # Limpar o número (apenas dígitos)
                clean_phone = "".join(filter(str.isdigit, phone))
                # Se não começar com código do país, assume 55 (Brasil)
                if len(clean_phone) <= 11:
                    clean_phone = "55" + clean_phone
                
                url = f"{settings.EVOLUTION_API_URL.rstrip('/')}/message/sendText/{instance}"
                headers = {
                    "Content-Type": "application/json",
                    "apikey": settings.EVOLUTION_API_KEY
                }
                payload = {
                    "number": clean_phone,
                    "text": message,
                    "delay": 1200,
                    "linkPreview": True
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload, headers=headers, timeout=15.0)
                    
                if response.status_code in [200, 201]:
                    logger.info(f"[WhatsApp] Mensagem enviada para {phone} via Evolution API")
                    status = "sent"
                else:
                    logger.error(f"[WhatsApp Error] Falha ao enviar para {phone}. Status: {response.status_code}, Body: {response.text}")
                    status = "error"
            except Exception as e:
                logger.error(f"[WhatsApp Error] Exceção no envio para {phone}: {str(e)}")
                status = "error"

        # Registra o log
        log = WhatsAppLog(
            store_id=store_id,
            phone=phone,
            message=message,
            status=status
        )
        db.add(log)
        db.commit()
        return status == "sent"

    @staticmethod
    async def notify_appointment_created(db: Session, store_id: UUID, client_name: str, pet_name: str, service: str, date: str, time: str, phone: str):
        store = db.query(Store).filter(Store.id == store_id).first()
        store_name = store.name if store else "Pet Shop"
        
        msg = (
            f"Olá {client_name}! 🐾\n\n"
            f"Seu agendamento para o pet *{pet_name}* ({service}) foi solicitado com sucesso para o dia {date} às {time}.\n"
            f"Local: {store_name}\n\n"
            "Qualquer dúvida, entre em contato conosco! ✅"
        )
        return await WhatsAppService.send_message(db, store_id, phone, msg)

    @staticmethod
    async def notify_status_change(db: Session, store_id: UUID, client_name: str, pet_name: str, status: str, phone: str):
        label = "Confirmado" if status == "confirmed" else "Cancelado"
        emoji = "✅" if status == "confirmed" else "❌"
        
        msg = f"Olá {client_name}! Seu agendamento para *{pet_name}* está *{label}* {emoji}."
        return await WhatsAppService.send_message(db, store_id, phone, msg)

    @staticmethod
    async def send_status_update(db: Session, store_id: UUID, phone: str, pet_name: str, status_type: str):
        """
        Envia atualizações de status em tempo real (Live Status).
        Tipos: 'bath_start', 'bath_end', 'meal', 'play', 'sleep'
        """
        templates = {
            "bath_start": f"Oi! Passando para avisar que o(a) *{pet_name}* já entrou para o banho! 🛁 Já já ele(a) estará cheiroso(a).",
            "bath_end": f"Oba! O banho do(a) *{pet_name}* terminou. 🎀 Ele(a) está pronto(a) e te esperando!",
            "meal": f"Hora do papa! 😋 *{pet_name}* acabou de comer e adorou a refeição.",
            "play": f"Momento diversão! 🎾 *{pet_name}* está brincando e gastando muita energia aqui no pátio.",
            "sleep": f"Hora do descanso. 😴 *{pet_name}* já está acomodado para tirar uma soneca tranquila."
        }
        
        message = templates.get(status_type, f"Olá! Passando para dar notícias do(a) *{pet_name}*. Tudo correndo bem por aqui! 🐾")
        return await WhatsAppService.send_message(db, store_id, phone, message)

whatsapp_service = WhatsAppService()
