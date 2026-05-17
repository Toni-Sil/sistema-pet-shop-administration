from __future__ import annotations
"""
BUSINESS LAYER - Regras de Negócio
Responsabilidade: Regras de negócio isoladas da IA
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class BusinessRule:
    name: str
    condition: str
    action: str
    priority: int = 5


class SchedulingBusinessRules:
    @staticmethod
    def can_schedule(service: str, pet_type: str, duration_minutes: int) -> bool:
        rules = {
            "banho": {"pequeno": 30, "medio": 45, "grande": 60},
            "tosa": {"pequeno": 45, "medio": 60, "grande": 90},
            "consulta": {"pequeno": 30, "medio": 30, "grande": 45},
        }
        expected = rules.get(service, {}).get(pet_type, 30)
        return duration_minutes <= expected * 1.5

    @staticmethod
    def get_available_slots(date: datetime, professional: str) -> List[datetime]:
        start_hour = 8
        end_hour = 19
        slots = []
        current = date.replace(hour=start_hour, minute=0, second=0)
        end = date.replace(hour=end_hour, minute=0, second=0)
        
        while current < end:
            slots.append(current)
            current += timedelta(hours=1)
        
        return slots

    @staticmethod
    def calculate_lead_time(service: str) -> int:
        lead_times = {
            "banho": 60,
            "tosa": 120,
            "consulta": 30,
            "vacina": 15,
        }
        return lead_times.get(service, 60)


class FinancialBusinessRules:
    @staticmethod
    def calculate_discount(total: float, client_years: int) -> float:
        discount_rates = {
            (0, 1): 0.0,
            (1, 3): 0.05,
            (3, 5): 0.10,
            (5, 10): 0.15,
            (10, 999): 0.20,
        }
        for (min_years, max_years), rate in discount_rates.items():
            if min_years <= client_years < max_years:
                return rate
        return 0.0

    @staticmethod
    def requires_approval(amount: float) -> bool:
        return amount > 5000

    @staticmethod
    def get_payment_methods(total: float) -> List[str]:
        methods = ["dinheiro", "pix", "debito", "credito"]
        if total > 100:
            methods.append("credito_parcelado")
        return methods


class CRMBusinessRules:
    @staticmethod
    def is_inactive(last_visit: datetime) -> bool:
        return (datetime.utcnow() - last_visit).days > 60

    @staticmethod
    def should_send_vaccine_reminder(next_vaccine_date: datetime) -> bool:
        days_until = (next_vaccine_date - datetime.utcnow()).days
        return 0 <= days_until <= 7

    @staticmethod
    def get_campaign_eligibility(client_years: int, total_spent: float) -> List[str]:
        campaigns = []
        
        if client_years >= 1 and total_spent > 500:
            campaigns.append("loyalty_10")
        
        if client_years >= 3:
            campaigns.append("vip_treatment")
        
        if total_spent > 2000:
            campaigns.append("premium_discount")
        
        return campaigns


class InventoryBusinessRules:
    @staticmethod
    def calculate_reorder_point(
        daily_sales: float, 
        lead_time_days: int, 
        safety_stock_days: int = 3
    ) -> float:
        return daily_sales * (lead_time_days + safety_stock_days)

    @staticmethod
    def should_emergency_order(current_stock: float, daily_sales: float) -> bool:
        days_left = current_stock / daily_sales if daily_sales > 0 else 999
        return days_left < 2

    @staticmethod
    def get_optimal_order_quantity(
        current_stock: float,
        max_stock: float,
        daily_sales: float,
        days_to_cover: int = 30
    ) -> float:
        target = daily_sales * days_to_cover
        order = target - current_stock
        return min(order, max_stock - current_stock)


class BusinessRulesEngine:
    def __init__(self) -> None:
        self.scheduling = SchedulingBusinessRules()
        self.financial = FinancialBusinessRules()
        self.crm = CRMBusinessRules()
        self.inventory = InventoryBusinessRules()

    def evaluate(self, domain: str, rule: str, **params) -> Any:
        domain_rules = {
            "scheduling": self.scheduling,
            "financial": self.financial,
            "crm": self.crm,
            "inventory": self.inventory,
        }
        
        domain_obj = domain_rules.get(domain)
        if domain_obj and hasattr(domain_obj, rule):
            method = getattr(domain_obj, rule)
            return method(**params)
        
        return None


business_rules_engine = BusinessRulesEngine()