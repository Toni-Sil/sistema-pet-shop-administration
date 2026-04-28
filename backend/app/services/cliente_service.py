from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException
from datetime import datetime, timedelta
from sqlalchemy import func
from typing import List

from app.models.cliente import Cliente, Pet
from app.schemas.cliente import ClienteCreate, ClienteUpdate, PetCreate, PetUpdate


# ── Clientes ──────────────────────────────────────────────

def listar(db: Session, store_id: UUID, search: str = None, skip: int = 0, limit: int = 50):
    q = db.query(Cliente).filter(Cliente.store_id == store_id, Cliente.is_active == True)
    if search:
        q = q.filter(Cliente.name.ilike(f"%{search}%") | Cliente.phone.ilike(f"%{search}%"))
    return q.order_by(Cliente.name).offset(skip).limit(limit).all()


def buscar(db: Session, id: UUID, store_id: UUID):
    cliente = db.query(Cliente).filter(Cliente.id == id, Cliente.store_id == store_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente não encontrado")
    
    from app.models.venda import Venda
    total = db.query(func.sum(Venda.total)).filter(
        Venda.client_id == id,
        Venda.payment_status == 'paid'
    ).scalar() or 0
    
    ultima_venda = db.query(Venda).filter(
        Venda.client_id == id,
        Venda.payment_status == 'paid'
    ).order_by(Venda.created_at.desc()).first()
    
    cliente.total_spent = float(total)
    cliente.last_visit = ultima_venda.created_at if ultima_venda else None
    
    return cliente


def listar_inativos(db: Session, store_id: UUID, dias: int = 60) -> List:
    from app.models.venda import Venda
    cutoff = datetime.utcnow() - timedelta(days=dias)
    
    clientes_ativos = db.query(Venda.client_id).filter(
        Venda.store_id == store_id,
        Venda.payment_status == 'paid',
        Venda.created_at >= cutoff
    ).distinct().subquery()
    
    from app.models.cliente import Cliente
    inativos = db.query(Cliente).filter(
        Cliente.store_id == store_id,
        Cliente.is_active == True,
        ~Cliente.id.in_(clientes_ativos)
    ).all()
    
    result = []
    for c in inativos:
        ultima_venda = db.query(Venda).filter(
            Venda.client_id == c.id,
            Venda.payment_status == 'paid'
        ).order_by(Venda.created_at.desc()).first()
        
        total = db.query(func.sum(Venda.total)).filter(
            Venda.client_id == c.id,
            Venda.payment_status == 'paid'
        ).scalar() or 0
        
        if ultima_venda:
            dias_sem = (datetime.utcnow() - ultima_venda.created_at).days
        else:
            dias_sem = dias
        
        if dias_sem >= dias:
            c.last_visit = ultima_venda.created_at if ultima_venda else None
            c.days_without_visit = dias_sem
            c.total_spent = float(total)
            result.append(c)
    
    return result


def criar(db: Session, dados: ClienteCreate, store_id: UUID):
    cliente = Cliente(**dados.model_dump(), store_id=store_id)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def atualizar(db: Session, id: UUID, dados: ClienteUpdate, store_id: UUID):
    cliente = buscar(db, id, store_id)
    for k, v in dados.model_dump(exclude_unset=True).items():
        setattr(cliente, k, v)
    db.commit()
    db.refresh(cliente)
    return cliente


def deletar(db: Session, id: UUID, store_id: UUID):
    cliente = buscar(db, id, store_id)
    cliente.is_active = False
    db.commit()
    return {"message": "Cliente deletado com sucesso"}

def importar_csv(db: Session, rows: list, store_id: UUID):
    count_clients = 0
    count_pets = 0
    for row in rows:
        try:
            # 1. Processar Cliente
            nome = row.get('nome') or row.get('name')
            if not nome: continue
            
            # Tenta encontrar cliente existente pelo telefone ou documento para evitar duplicidade
            telefone = str(row.get('telefone') or row.get('phone') or '').strip()
            documento = str(row.get('cpf') or row.get('documento') or '').strip()
            
            cliente = None
            if telefone:
                cliente = db.query(Cliente).filter(Cliente.store_id == store_id, Cliente.phone == telefone).first()
            if not cliente and documento:
                cliente = db.query(Cliente).filter(Cliente.store_id == store_id, Cliente.document == documento).first()
                
            if not cliente:
                cliente = Cliente(
                    store_id=store_id,
                    name=nome,
                    phone=telefone,
                    email=row.get('email'),
                    document=documento,
                    address=row.get('endereco') or row.get('address')
                )
                db.add(cliente)
                db.flush() # Para pegar o ID do cliente
                count_clients += 1
            
            # 2. Processar Pet (se houver dados de pet na linha)
            pet_nome = row.get('pet_nome') or row.get('pet_name')
            if pet_nome:
                # Verifica se o pet já existe para este cliente
                pet_existente = db.query(Pet).filter(Pet.client_id == cliente.id, Pet.name == pet_nome).first()
                if not pet_existente:
                    pet = Pet(
                        store_id=store_id,
                        client_id=cliente.id,
                        name=pet_nome,
                        species=row.get('pet_especie') or row.get('pet_species') or 'Cão',
                        breed=row.get('pet_raca') or row.get('pet_breed') or 'SRD',
                        gender=row.get('pet_sexo') or row.get('pet_gender'),
                        weight=float(row.get('pet_peso', 0)) if row.get('pet_peso') else None
                    )
                    db.add(pet)
                    count_pets += 1
                    
        except Exception as e:
            print(f"Erro ao importar linha {row}: {e}")
            continue
            
    db.commit()
    return {"message": f"{count_clients} clientes e {count_pets} pets importados com sucesso"}


# ── Pets ──────────────────────────────────────────────────

def criar_pet(db: Session, client_id: UUID, dados: PetCreate, store_id: UUID):
    buscar(db, client_id, store_id)
    pet = Pet(**dados.model_dump(), client_id=client_id, store_id=store_id)
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


def atualizar_pet(db: Session, pet_id: UUID, client_id: UUID, dados: PetUpdate, store_id: UUID):
    buscar(db, client_id, store_id)
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.client_id == client_id, Pet.store_id == store_id).first()
    if not pet:
        raise HTTPException(404, "Pet não encontrado")
    for k, v in dados.model_dump(exclude_unset=True).items():
        setattr(pet, k, v)
    db.commit()
    db.refresh(pet)
    return pet
