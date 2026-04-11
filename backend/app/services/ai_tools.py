from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date, timedelta
from app.models.produto import Produto
from app.models.agendamento import Agendamento
from app.models.cliente import Cliente, Pet
from app.models.venda import Venda

class AITools:
    @staticmethod
    def get_stock_levels(db: Session, store_id: UUID):
        products = db.query(Produto).filter(Produto.store_id == store_id).all()
        return [
            {"nome": p.name, "estoque": p.quantity, "minimo": p.min_qty}
            for p in products if p.quantity <= p.min_qty
        ]

    @staticmethod
    def get_todays_appointments(db: Session, store_id: UUID):
        apps = db.query(Agendamento).filter(
            Agendamento.store_id == store_id, 
            Agendamento.date == date.today()
        ).all()
        return [
            {"pet": a.pet.name if a.pet else "Visitante", "servico": a.service_legacy or (a.service_rel.name if a.service_rel else "Serviço"), "hora": a.time, "status": a.status}
            for a in apps
        ]

    @staticmethod
    def get_upcoming_vaccines(db: Session, store_id: UUID):
        # Simplificado: Vacinas nos próximos 7 dias
        today = date.today()
        next_week = today + timedelta(days=7)
        # Precisamos importar PetVaccine e Pet no arquivo para isso funcionar
        # Vou assumir que o model está acessível ou fazer join
        from app.models.pet_vaccine import PetVaccine
        from app.models.cliente import Pet
        
        vaccines = db.query(PetVaccine).join(Pet).filter(
            Pet.store_id == store_id,
            PetVaccine.next_dose >= today,
            PetVaccine.next_dose <= next_week
        ).all()
        
        return [
            {"pet": v.pet.name, "vacina": v.vaccine, "data": str(v.next_dose)}
            for v in vaccines
        ]

    @staticmethod
    def get_financial_summary(db: Session, store_id: UUID):
        vendas = db.query(Venda).filter(Venda.store_id == store_id).all()
        total = sum(float(v.total) for v in vendas)
        return {
            "faturamento_total": total, 
            "total_vendas": len(vendas),
            "ticket_medio": total / len(vendas) if vendas else 0
        }

ai_tools = AITools()
