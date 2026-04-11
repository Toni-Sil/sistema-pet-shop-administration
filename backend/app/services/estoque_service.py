from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from fastapi import HTTPException
from app.models.estoque import MovimentacaoEstoque
from app.models.produto import Produto
from app.schemas.estoque import EstoqueMovimentacaoCreate

def listar_movimentacoes(db: Session, store_id: UUID, product_id: UUID = None, skip: int = 0, limit: int = 50):
    query = db.query(MovimentacaoEstoque).filter(MovimentacaoEstoque.store_id == store_id)
    if product_id:
        query = query.filter(MovimentacaoEstoque.product_id == product_id)
    return query.order_by(MovimentacaoEstoque.created_at.desc()).offset(skip).limit(limit).all()

def registrar_movimentacao(db: Session, dados: EstoqueMovimentacaoCreate, store_id: UUID, user_id: UUID):
    produto = db.query(Produto).filter(
        Produto.id == dados.product_id,
        Produto.store_id == store_id
    ).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado nesta loja")
    
    qty = dados.quantity or 0
    weight = dados.weight
    
    if produto.sale_type == 'WEIGHT' and weight:
        if dados.type == 'exit':
            if produto.weight_in_stock < weight:
                raise HTTPException(status_code=400, detail="Peso insuficiente no estoque")
            produto.weight_in_stock -= weight
        elif dados.type == 'entry':
            if produto.weight_in_stock is None:
                produto.weight_in_stock = weight
            else:
                produto.weight_in_stock += weight
        dados.quantity = None
    else:
        if dados.type == 'exit':
            if produto.quantity is None or produto.quantity < qty:
                raise HTTPException(status_code=400, detail="Quantidade insuficiente no estoque")
            produto.quantity -= qty
        elif dados.type == 'entry':
            if produto.quantity is None:
                produto.quantity = qty
            else:
                produto.quantity += qty
        dados.weight = None
    
    movimentacao = MovimentacaoEstoque(
        product_id=produto.id,
        store_id=store_id,
        user_id=user_id,
        type=dados.type,
        quantity=qty,
        weight=weight,
        reason=dados.reason,
        cost_price=dados.cost_price,
        supplier=dados.supplier
    )
    
    db.add(movimentacao)
    db.commit()
    db.refresh(movimentacao)
    return movimentacao


def listar_alertas(db: Session, store_id: UUID):
    alertas = []
    
    produtos_unidade = db.query(Produto).filter(
        Produto.store_id == store_id,
        Produto.is_active == True,
        Produto.sale_type == 'UNIT',
        Produto.quantity != None,
        Produto.quantity <= Produto.min_qty
    ).all()
    
    for p in produtos_unidade:
        status = 'critico' if p.quantity <= p.min_qty / 2 else 'baixo'
        alertas.append(AlertaEstoque(
            product_id=p.id,
            name=p.name,
            quantity=p.quantity,
            min_qty=p.min_qty,
            status=status
        ))
    
    produtos_peso = db.query(Produto).filter(
        Produto.store_id == store_id,
        Produto.is_active == True,
        Produto.sale_type == 'WEIGHT',
        Produto.weight_in_stock != None,
        Produto.weight_in_stock <= Produto.min_weight
    ).all()
    
    for p in produtos_peso:
        status = 'critico' if p.weight_in_stock <= p.min_weight / 2 else 'baixo'
        alertas.append(AlertaEstoque(
            product_id=p.id,
            name=p.name,
            weight_in_stock=p.weight_in_stock,
            min_weight=p.min_weight,
            status=status
        ))
    
    return alertas


def listar_vencendo(db: Session, store_id: UUID):
    from datetime import date
    thirty_days = date.today() + timedelta(days=30)
    
    produtos = db.query(Produto).filter(
        Produto.store_id == store_id,
        Produto.is_active == True,
        Produto.expires_at != None,
        Produto.expires_at <= thirty_days
    ).order_by(Produto.expires_at).all()
    
    result = []
    for p in produtos:
        if p.expires_at < date.today():
            status = 'vencido'
        elif p.expires_at <= date.today() + timedelta(days=7):
            status = 'urgente'
        else:
            status = 'aviso'
        result.append(ProdutoVencimento(id=p.id, name=p.name, expires_at=p.expires_at, status=status))
    
    return result


class AlertaEstoque:
    def __init__(self, product_id, name, quantity=None, weight_in_stock=None, min_qty=None, min_weight=None, status='baixo'):
        self.product_id = product_id
        self.name = name
        self.quantity = quantity
        self.weight_in_stock = weight_in_stock
        self.min_qty = min_qty
        self.min_weight = min_weight
        self.status = status


class ProdutoVencimento:
    def __init__(self, id, name, expires_at, status):
        self.id = id
        self.name = name
        self.expires_at = expires_at
        self.status = status
