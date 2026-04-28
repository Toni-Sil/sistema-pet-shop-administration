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

def importar_csv(db: Session, rows: list, store_id: UUID):
    from decimal import Decimal
    from datetime import datetime
    count = 0
    for row in rows:
        try:
            desc = row.get('descricao') or row.get('description')
            amount = row.get('valor') or row.get('amount')
            if not desc or not amount: continue
            
            # Parsing da data
            raw_date = row.get('data') or row.get('due_date') or row.get('vencimento')
            due_date = date_type.today()
            if raw_date:
                try:
                    # Tenta formatos comuns: DD/MM/YYYY ou YYYY-MM-DD
                    if '/' in raw_date:
                        due_date = datetime.strptime(raw_date, '%d/%m/%Y').date()
                    else:
                        due_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
                except:
                    pass

            despesa = Despesa(
                store_id=store_id,
                description=desc,
                amount=Decimal(str(amount).replace(',', '.')),
                category=row.get('categoria') or row.get('category') or 'Geral',
                due_date=due_date,
                is_paid=str(row.get('pago', '')).lower() in ['true', '1', 'sim', 'yes', 's']
            )
            db.add(despesa)
            count += 1
        except Exception as e:
            print(f"Erro ao importar despesa: {e}")
            continue
            
    db.commit()
    return {"message": f"{count} despesas importadas com sucesso"}
