from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.agendamento import Agendamento
from app.models.produto import Produto
from app.models.pet_vaccine import PetVaccine
from app.models.store import Store
from app.services.whatsapp_service import WhatsAppService

def send_appointment_reminders():
    """Envia lembretes de agendamento 24h antes via WhatsApp"""
    db = SessionLocal()
    try:
        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        
        agendamentos = db.query(Agendamento).filter(
            Agendamento.date == tomorrow,
            Agendamento.status == 'scheduled'
        ).all()
        
        for ag in agendamentos:
            if ag.pet and ag.pet.client:
                phone = ag.pet.client.phone
                client_name = ag.pet.client.name
                pet_name = ag.pet.name
                service_name = ag.service_rel.name if ag.service_rel else ag.service_legacy
                date_str = f"{ag.date.strftime('%d/%m')} às {ag.time}"
                
                message = (
                    f"Olá {client_name}! 😊\n\n"
                    f"Lembrando que amanhã {date_str} tem {service_name} para o(a) {pet_name}.\n\n"
                    f"Qualquer dúvida, responda esta mensagem!"
                )
                
                WhatsAppService.send_message(db, ag.store_id, phone, message)
                print(f"Reminder sent to {phone}")
    except Exception as e:
        print(f"Error sending reminders: {e}")
    finally:
        db.close()


def check_expiring_vaccines():
    """Verifica vacinas prestes a vencer e notifica tutores"""
    db = SessionLocal()
    try:
        from datetime import date
        thirty_days = date.today() + timedelta(days=30)
        
        vaccines = db.query(PetVaccine).filter(
            PetVaccine.next_dose <= thirty_days,
            PetVaccine.next_dose >= date.today()
        ).all()
        
        for vaccine in vaccines:
            if vaccine.pet and vaccine.pet.client:
                phone = vaccine.pet.client.phone
                client_name = vaccine.pet.client.name
                pet_name = vaccine.pet.name
                vaccine_name = vaccine.vaccine
                due_date = vaccine.next_dose.strftime('%d/%m/%Y')
                
                message = (
                    f"Olá {client_name}! 🐾\n\n"
                    f"A vacina {vaccine_name} do(a) {pet_name} vence em {due_date}.\n"
                    f"Por favor, agende um reforço para manter a proteção em dia!"
                )
                
                WhatsAppService.send_message(db, vaccine.pet.store_id, phone, message)
                print(f"Vaccine alert sent to {phone}")
    except Exception as e:
        print(f"Error checking vaccines: {e}")
    finally:
        db.close()


def check_low_stock():
    """Verifica produtos com estoque baixo e alerta o dono"""
    db = SessionLocal()
    try:
        low_stock_products = db.query(Produto).filter(
            Produto.is_active == True,
            Produto.sale_type == 'UNIT',
            Produto.quantity != None,
            Produto.quantity <= Produto.min_qty
        ).all()
        
        low_weight_products = db.query(Produto).filter(
            Produto.is_active == True,
            Produto.sale_type == 'WEIGHT',
            Produto.weight_in_stock != None,
            Produto.weight_in_stock <= Produto.min_weight
        ).all()
        
        if low_stock_products or low_weight_products:
            store_ids = set([p.store_id for p in low_stock_products + low_weight_products])
            
            for store_id in store_ids:
                store = db.query(Store).filter(Store.id == store_id).first()
                if store and store.user:
                    phone = store.user.phone
                    
                    low_list = []
                    for p in low_stock_products + low_weight_products:
                        if p.store_id == store_id:
                            if p.sale_type == 'UNIT':
                                low_list.append(f"- {p.name}: {p.quantity} un (mín: {p.min_qty})")
                            else:
                                low_list.append(f"- {p.name}: {float(p.weight_in_stock):.3f} kg (mín: {float(p.min_weight):.3f} kg)")
                    
                    message = (
                        f"⚠️ Alerta de Estoque Baixo\n\n"
                        + "\n".join(low_list[:10])
                    )
                    
                    WhatsAppService.send_message(db, store_id, phone, message)
                    print(f"Low stock alert sent to store {store_id}")
    except Exception as e:
        print(f"Error checking stock: {e}")
    finally:
        db.close()


def check_expiring_products():
    """Verifica produtos próximos ao vencimento"""
    db = SessionLocal()
    try:
        from datetime import date
        thirty_days = date.today() + timedelta(days=30)
        seven_days = date.today() + timedelta(days=7)
        
        expiring = db.query(Produto).filter(
            Produto.is_active == True,
            Produto.expires_at != None,
            Produto.expires_at <= thirty_days
        ).all()
        
        for product in expiring:
            if product.store and product.store.user:
                phone = product.store.user.phone
                
                if product.expires_at < date.today():
                    status = "⚠️ VENCIDO!"
                    color = "🔴"
                elif product.expires_at <= seven_days:
                    status = "Vence em 7 dias"
                    color = "🟠"
                else:
                    status = "Vence em 30 dias"
                    color = "🟡"
                
                message = (
                    f"{color} Alerta de Validade\n\n"
                    f"{product.name}: {status} ({product.expires_at.strftime('%d/%m/%Y')})"
                )
                
                send_whatsapp_message(phone, message)
                print(f"Expiry alert sent to {phone} for {product.name}")
    except Exception as e:
        print(f"Error checking expiry: {e}")
    finally:
        db.close()


def check_pending_payments(db, store_id: UUID):
    """Verifica pagamentos Pix pendentes e atualiza status"""
    from app.models.venda import Venda
    from app.services import asaas_service
    
    vendas_pendentes = db.query(Venda).filter(
        Venda.store_id == store_id,
        Venda.payment_method == 'pix',
        Venda.payment_status == 'pending'
    ).all()
    
    for venda in vendas_pendentes:
        if not venda.asaas_charge_id:
            continue
        
        try:
            status = asaas_service.verificar_status_cobranca(venda.asaas_charge_id)
            status_pagamento = status.get("status")
            
            from datetime import datetime
            if status_pagamento in ("CONFIRMED", "RECEIVED"):
                venda.payment_status = 'paid'
                venda.paid_at = datetime.utcnow()
                
                for item in venda.items:
                    produto = item.product
                    if produto.sale_type == 'WEIGHT':
                        if item.weight:
                            produto.weight_in_stock = (produto.weight_in_stock or 0) - item.weight
                    else:
                        if item.quantity:
                            produto.quantity = (produto.quantity or 0) - item.quantity
                
                db.commit()
                print(f"Venda {venda.id} confirmada")
            elif status_pagamento in ("REJECTED", "OVERDUE", "CANCELLED"):
                venda.payment_status = 'cancelled'
                db.commit()
                print(f"Venda {venda.id} cancelada")
        except Exception as e:
            print(f"Erro ao verificar venda {venda.id}: {e}")


if __name__ == "__main__":
    print("Jobs scheduler loaded")
    print("Available jobs:")
    print("- send_appointment_reminders: Envia lembretes 24h antes")
    print("- check_expiring_vaccines: Verifica vacunas vencendo")
    print("- check_low_stock: Alerta estoque baixo")
    print("- check_expiring_products: Alerta produtos vencendo")
    print("- check_pending_payments(db, store_id): Verifica pagamentos Pix pendentes")