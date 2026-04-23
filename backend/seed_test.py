from app.database import SessionLocal, Base, engine
from app.models.store import Store
from app.models.user import User
from app.models.cliente import Cliente, Pet
from app.models.pet_vaccine import PetVaccine
from app.models.prontuario import Prontuario
from app.models.produto import Produto as Product
from app.models.agendamento import Agendamento
from app.models.hotel import Hospedagem
from app.models.pacote import Pacote
from uuid import uuid4
import bcrypt

def seed():
    db = SessionLocal()
    try:
        # Create Store
        store = db.query(Store).first()
        if not store:
            store = Store(
                id=uuid4(),
                name="Pet Shop Teste",
                slug="pet-shop-teste",
                settings={
                    "payment_fees": {
                        "pix": 0,
                        "cash": 0,
                        "credit_card": 2.99,
                        "debit_card": 1.50
                    }
                }
            )
            db.add(store)
            db.flush()
        
        # Create User
        user = db.query(User).filter(User.email == "admin@teste.com").first()
        if not user:
            hashed_pw = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user = User(
                id=uuid4(),
                email="admin@teste.com",
                password_hash=hashed_pw,
                name="Administrador Teste",
                role="admin",
                store_id=store.id
            )
            db.add(user)
            
        # Create Client & Pet
        client = db.query(Cliente).first()
        if not client:
            client = Cliente(id=uuid4(), store_id=store.id, name="João Silva", phone="5511999999999")
            db.add(client)
            db.flush()
            
            pet = Pet(id=uuid4(), store_id=store.id, client_id=client.id, name="Bono", species="dog", breed="Golden Retriever", weight="25kg")
            db.add(pet)
            
        # Create Product
        prod = db.query(Product).filter(Product.name == "Ração Golden 15kg").first()
        if not prod:
            prod = Product(
                id=uuid4(), 
                store_id=store.id, 
                name="Ração Golden 15kg", 
                category="Ração", 
                sale_price=150.00, 
                cost_price=100.00, 
                quantity=10,
                min_qty=5
            )
            db.add(prod)
            db.flush()

        # Create Appointments for April 2026
        from datetime import datetime, timedelta
        pet = db.query(Pet).first()
        if pet:
            # Hoje
            now = datetime.now()
            today_appointment = Agendamento(
                id=uuid4(),
                store_id=store.id,
                pet_id=pet.id,
                service_name="Banho e Tosa",
                start_time=now.replace(hour=10, minute=0, second=0),
                end_time=now.replace(hour=11, minute=0, second=0),
                status="pending",
                price=85.00
            )
            db.add(today_appointment)
            
            # Amanhã
            tomorrow = now + timedelta(days=1)
            tomorrow_appointment = Agendamento(
                id=uuid4(),
                store_id=store.id,
                pet_id=pet.id,
                service_name="Consulta Veterinária",
                start_time=tomorrow.replace(hour=14, minute=30, second=0),
                end_time=tomorrow.replace(hour=15, minute=30, second=0),
                status="confirmed",
                price=150.00
            )
            db.add(tomorrow_appointment)

        # Create Sales
        from app.models.venda import Venda, ItemVenda
        sale = Venda(
            id=uuid4(),
            store_id=store.id,
            total_amount=235.00,
            payment_method="pix",
            status="completed",
            created_at=datetime.now()
        )
        db.add(sale)
        db.flush()

        item = ItemVenda(
            id=uuid4(),
            venda_id=sale.id,
            product_id=prod.id,
            quantity=1,
            unit_price=150.00,
            subtotal=150.00
        )
        db.add(item)
            
        db.commit()
        print("Seed finalizado com sucesso! User: admin@teste.com / Pass: admin123")
    except Exception as e:
        db.rollback()
        print(f"Erro no seed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
