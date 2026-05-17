from __future__ import annotations
"""
INFRAESTRUTURA - Redis + Celery para filas e eventos
"""

import os
from celery import Celery
from typing import Any, Dict, List
import json


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "pet_shop_agents",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="agent.process_message")
def process_agent_message(
    store_id: str,
    phone: str,
    message: str,
    source: str = "whatsapp",
) -> Dict[str, Any]:
    from ai.operations import operational_service
    from openai import AsyncOpenAI

    flow = operational_service.get_flow(store_id)
    flow.set_llm(AsyncOpenAI())

    import asyncio

    result = asyncio.run(
        operational_service.process_message(
            store_id=store_id,
            phone=phone,
            message=message,
        )
    )

    return result


@celery_app.task(name="agent.schedule_reminder")
def schedule_reminder(
    store_id: str,
    client_id: str,
    appointment_id: str,
    reminder_type: str = "whatsapp",
) -> Dict[str, Any]:
    return {
        "status": "scheduled",
        "reminder_type": reminder_type,
        "appointment_id": appointment_id,
    }


@celery_app.task(name="agent.process_vaccine_alerts")
def process_vaccine_alerts(store_id: str) -> Dict[str, Any]:
    return {
        "status": "processed",
        "alerts_sent": 0,
    }


@celery_app.task(name="agent.send_campaign")
def send_campaign(
    store_id: str,
    campaign_type: str,
    target_clients: List[str],
) -> Dict[str, Any]:
    return {
        "status": "sent",
        "campaign_type": campaign_type,
        "recipients": len(target_clients),
    }


@celery_app.task(name="agent.analyze_low_stock")
def analyze_low_stock(store_id: str) -> Dict[str, Any]:
    return {
        "status": "analyzed",
        "low_stock_items": [],
    }


@celery_app.task(name="agent.cleanup_memory")
def cleanup_expired_memory() -> Dict[str, Any]:
    from ai.memory import memory_store

    count = memory_store.clear_expired()
    return {
        "status": "cleaned",
        "entries_removed": count,
    }


celery_app.conf.beat_schedule = {
    "cleanup-memory-every-hour": {
        "task": "agent.cleanup_memory",
        "schedule": 3600.0,
    },
    "vaccine-alerts-daily": {
        "task": "agent.process_vaccine_alerts",
        "schedule": 86400.0,
    },
}


class QueueService:
    @staticmethod
    def enqueue_message(store_id: str, phone: str, message: str, source: str = "whatsapp"):
        process_agent_message.delay(store_id, phone, message, source)

    @staticmethod
    def enqueue_reminder(store_id: str, client_id: str, appointment_id: str):
        schedule_reminder.delay(store_id, client_id, appointment_id)

    @staticmethod
    def enqueue_vaccine_alerts(store_id: str):
        process_vaccine_alerts.delay(store_id)


queue_service = QueueService()