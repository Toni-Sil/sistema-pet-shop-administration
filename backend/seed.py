import uuid
import sys
import os
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.store import Store
from app.models.cliente import Cliente, Pet
from app.models.produto import Produto
from app.models.hotel import Quarto, Hospedagem, QuartoStatus, HospedagemStatus
from app.models.agendamento import Agendamento
from app.models.service import Service

def seed_db():
    db = SessionLocal()
    try:
        # Pega a primeira loja ou cria uma
        store = db.query(Store).first()
        if not store:
            store = Store(name="Pet Shop Demo", slug="pet-shop-demo", phone="11999999999")
            db.add(store)
            db.commit()
            db.refresh(store)

        print(f"Usando Store: {store.name} ({store.id})")

        # 1. Serviços Fictícios
        services = []
        for s_name, price in [("Banho Especial", 50.0), ("Tosa Completa", 70.0), ("Consulta Vet", 150.0)]:
            srv = db.query(Service).filter_by(store_id=store.id, name=s_name).first()
            if not srv:
                srv = Service(store_id=store.id, name=s_name, price=price, duration=60)
                db.add(srv)
            services.append(srv)
        db.commit()

        # 2. Clientes Fictícios
        clientes_data = [
            {"name": "João Silva", "phone": "11988887777", "email": "joao@email.com"},
            {"name": "Maria Oliveira", "phone": "11977776666", "email": "maria@email.com"},
            {"name": "Carlos Souza", "phone": "11966665555", "email": "carlos@email.com"}
        ]
        clientes = []
        for cd in clientes_data:
            cli = db.query(Cliente).filter_by(store_id=store.id, name=cd["name"]).first()
            if not cli:
                cli = Cliente(store_id=store.id, **cd)
                db.add(cli)
            clientes.append(cli)
        db.commit()

        # 3. Pets Fictícios
        pets_data = [
            {"name": "Rex", "species": "dog", "breed": "Golden Retriever", "client_idx": 0},
            {"name": "Mia", "species": "cat", "breed": "Siamês", "client_idx": 0},
            {"name": "Thor", "species": "dog", "breed": "Bulldog", "client_idx": 1},
            {"name": "Bolinha", "species": "dog", "breed": "Poodle", "client_idx": 2}
        ]
        pets = []
        for pd in pets_data:
            c_idx = pd.pop("client_idx")
            cli = clientes[c_idx]
            pet = db.query(Pet).filter_by(store_id=store.id, name=pd["name"], client_id=cli.id).first()
            if not pet:
                pet = Pet(store_id=store.id, client_id=cli.id, **pd)
                db.add(pet)
            pets.append(pet)
        db.commit()

        # 4. Produtos Fictícios
        produtos_data = [
            {"name": "Ração Premium 15kg", "category": "Ração", "sale_price": 200.0, "cost_price": 150.0, "quantity": 10},
            {"name": "Shampoo Antipulgas", "category": "Higiene", "sale_price": 45.0, "cost_price": 20.0, "quantity": 25},
            {"name": "Brinquedo Osso Borracha", "category": "Acessório", "sale_price": 25.0, "cost_price": 10.0, "quantity": 50},
            {"name": "Coleira Peitoral G", "category": "Acessório", "sale_price": 60.0, "cost_price": 30.0, "quantity": 15}
        ]
        for prd in produtos_data:
            prod = db.query(Produto).filter_by(store_id=store.id, name=prd["name"]).first()
            if not prod:
                prod = Produto(store_id=store.id, **prd)
                db.add(prod)
        db.commit()

        # 5. Hotel - Quartos
        quartos_data = [
            {"name": "Canil VIP 1", "tipo": "Cachorro Grande", "preco_diaria": 80.0},
            {"name": "Gatil Conforto", "tipo": "Gato", "preco_diaria": 60.0},
            {"name": "Canil Standard", "tipo": "Cachorro Médio", "preco_diaria": 50.0}
        ]
        quartos = []
        for qd in quartos_data:
            q = db.query(Quarto).filter_by(store_id=store.id, name=qd["name"]).first()
            if not q:
                q = Quarto(store_id=store.id, **qd)
                db.add(q)
            quartos.append(q)
        db.commit()

        # 6. Agendamentos Fictícios (Hoje e Amanhã)
        hoje = date.today()
        amanha = hoje + timedelta(days=1)
        agendamentos_data = [
            {"pet": pets[0], "service": services[0], "date": hoje, "time": "10:00"},
            {"pet": pets[2], "service": services[1], "date": hoje, "time": "14:30"},
            {"pet": pets[3], "service": services[2], "date": amanha, "time": "09:00"}
        ]
        for ad in agendamentos_data:
            ag = db.query(Agendamento).filter_by(store_id=store.id, pet_id=ad["pet"].id, date=ad["date"], time=ad["time"]).first()
            if not ag:
                ag = Agendamento(
                    store_id=store.id,
                    pet_id=ad["pet"].id,
                    service_id=ad["service"].id,
                    service_legacy=ad["service"].name,
                    date=ad["date"],
                    time=ad["time"],
                    price=str(ad["service"].price),
                    status="scheduled"
                )
                db.add(ag)
        db.commit()

        # 7. Hospedagem (Hotel)
        # Check-in ontem, checkout amanhã
        h = db.query(Hospedagem).filter_by(store_id=store.id, pet_id=pets[1].id).first()
        if not h:
            h = Hospedagem(
                store_id=store.id,
                pet_id=pets[1].id,
                quarto_id=quartos[1].id, # Gatil
                check_in_previsto=datetime.now() - timedelta(days=1),
                check_out_previsto=datetime.now() + timedelta(days=1),
                check_in_real=datetime.now() - timedelta(days=1),
                status=HospedagemStatus.CHECKED_IN,
                valor_diaria=60.0,
                valor_total=120.0,
                alimentacao="Ração própria",
                observacoes="Pet super calmo"
            )
            db.add(h)
        db.commit()

        print("Banco de dados populado com dados fictícios com sucesso!")

    except Exception as e:
        print(f"Erro ao popular banco de dados: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
