from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from datetime import date, timedelta
from app.models.produto import Produto
from app.models.agendamento import Agendamento
from app.models.cliente import Cliente, Pet
from app.models.venda import Venda, ItemVenda

class AITools:
    @staticmethod
    def get_stock_levels(db: Session, store_id: UUID):
        products = db.query(Produto).filter(Produto.store_id == store_id).all()
        return [
            {"id": str(p.id), "nome": p.name, "estoque": p.quantity, "minimo": p.min_qty}
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

    @staticmethod
    def get_inventory_predictions(db: Session, store_id: UUID):
        """
        Analisa histórico de vendas para prever quando o estoque acabará.
        Retorna sugestões de compra baseadas na velocidade de saída.
        """
        # 1. Pegar vendas dos últimos 30 dias para calcular velocidade
        trinta_dias_atras = date.today() - timedelta(days=30)
        
        vendas_recentes = db.query(
            ItemVenda.product_id,
            func.sum(ItemVenda.quantity).label("total_vendido")
        ).join(Venda, ItemVenda.sale_id == Venda.id).filter(
            Venda.created_at >= trinta_dias_atras
        ).group_by(ItemVenda.product_id).all()
        
        velocidade_vendas = {v.product_id: float(v.total_vendido) / 30 for v in vendas_recentes}
        
        # 2. Pegar estoque atual
        produtos = db.query(Produto).filter(Produto.store_id == store_id).all()
        
        previsoes = []
        for p in produtos:
            v_diaria = velocidade_vendas.get(p.id, 0)
            
            if v_diaria > 0:
                dias_restantes = int(p.quantity / v_diaria)
                if dias_restantes <= 10: # Só avisa se faltar 10 dias ou menos
                    previsoes.append({
                        "id": str(p.id),
                        "nome": p.name,
                        "estoque_atual": p.quantity,
                        "venda_diaria_media": round(v_diaria, 2),
                        "dias_restantes": dias_restantes,
                        "sugestao_compra": int(v_diaria * 30) # Sugere comprar para 30 dias
                    })
            elif p.quantity <= (p.min_qty or 0):
                # Se não teve vendas mas está abaixo do mínimo
                previsoes.append({
                    "id": str(p.id),
                    "nome": p.name,
                    "estoque_atual": p.quantity,
                    "venda_diaria_media": 0,
                    "dias_restantes": 0,
                    "sugestao_compra": 10 # Sugestão padrão
                })
                
        return sorted(previsoes, key=lambda x: x['dias_restantes'])

ai_tools = AITools()
