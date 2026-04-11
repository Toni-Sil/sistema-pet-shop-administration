from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException
from datetime import date as date_type

from app.models.financeiro import Despesa
from app.schemas.despesa import DespesaCreate, DespesaUpdate


def listar(db: Session, store_id: UUID, apenas_pendentes: bool = False, skip: int = 0, limit: int = 50):
    q = db.query(Despesa).filter(Despesa.store_id == store_id)
    if apenas_pendentes:
        q = q.filter(Despesa.is_paid == False)
    return q.order_by(Despesa.due_date).offset(skip).limit(limit).all()


def criar(db: Session, dados: DespesaCreate, store_id: UUID):
    despesa = Despesa(**dados.model_dump(), store_id=store_id)
    db.add(despesa)
    db.commit()
    db.refresh(despesa)
    return despesa


def atualizar(db: Session, id: UUID, dados: DespesaUpdate, store_id: UUID):
    d = db.query(Despesa).filter(Despesa.id == id, Despesa.store_id == store_id).first()
    if not d:
        raise HTTPException(404, "Despesa não encontrada")
    for k, v in dados.model_dump(exclude_unset=True).items():
        setattr(d, k, v)
    db.commit()
    db.refresh(d)
    return d


def marcar_paga(db: Session, id: UUID, store_id: UUID):
    d = db.query(Despesa).filter(Despesa.id == id, Despesa.store_id == store_id).first()
    if not d:
        raise HTTPException(404, "Despesa não encontrada")
    d.is_paid = True
    d.paid_at = date_type.today()
    db.commit()
    db.refresh(d)
    return d


def deletar(db: Session, id: UUID, store_id: UUID):
    d = db.query(Despesa).filter(Despesa.id == id, Despesa.store_id == store_id).first()
    if not d:
        raise HTTPException(404, "Despesa não encontrada")
    db.delete(d)
    db.commit()
    return {"message": "Despesa removida com sucesso"}
