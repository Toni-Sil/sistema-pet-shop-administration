from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException
from typing import List
from decimal import Decimal

from app.models.venda import Venda, ItemVenda
from app.models.produto import Produto
from app.models.estoque import MovimentacaoEstoque
from app.schemas.venda import VendaCreate

MAX_DISCOUNT_PERCENT = 30

def validar_desconto(total: Decimal, discount: Decimal) -> None:
    """Valida que desconto não excede 30%"""
    if discount <= 0:
        return
    discount_percent = (discount / total) * 100
    if discount_percent > MAX_DISCOUNT_PERCENT:
        raise HTTPException(
            status_code=400,
            detail=f"Desconto máximo é {MAX_DISCOUNT_PERCENT}%. Valor atual: {discount_percent:.1f}%"
        )

def realizar_venda(db: Session, dados: VendaCreate, store_id: UUID, user_id: UUID):
    total = Decimal('0.00')
    for item in dados.items:
        total += item.total
    
    validar_desconto(total, dados.discount or Decimal('0.00'))
    subtotal_with_discount = total - (dados.discount or Decimal('0.00'))
    
    venda = Venda(
        store_id=store_id,
        client_id=dados.client_id,
        user_id=user_id,
        total=subtotal_with_discount,
        discount=dados.discount or Decimal('0.00'),
        payment_method=dados.payment_method,
        payment_status='pending' if dados.payment_method == 'pix' else 'paid',
        notes=dados.notes
    )
    db.add(venda)
    db.flush()
    
    for i_data in dados.items:
        produto = db.query(Produto).filter(Produto.id == i_data.product_id, Produto.store_id == store_id).first()
        if not produto:
            raise HTTPException(status_code=404, detail=f"Produto {i_data.product_id} não encontrado.")
        
        qty = i_data.quantity or 0
        weight = i_data.weight
        
        if produto.sale_type == 'WEIGHT' and weight:
            if produto.weight_in_stock is None or produto.weight_in_stock < weight:
                raise HTTPException(status_code=400, detail=f"Peso insuficiente para {produto.name}.")
            produto.weight_in_stock -= weight
        else:
            if qty > 0:
                if produto.quantity is None or produto.quantity < qty:
                    raise HTTPException(status_code=400, detail=f"Estoque insuficiente para {produto.name}.")
                produto.quantity -= qty
        
        item = ItemVenda(
            sale_id=venda.id,
            product_id=i_data.product_id,
            quantity=qty,
            weight=weight,
            unit_price=i_data.unit_price,
            total=i_data.total
        )
        db.add(item)
        
        movimento = MovimentacaoEstoque(
            product_id=produto.id,
            store_id=store_id,
            type='exit',
            quantity=qty,
            weight=weight,
            reason='sale',
            sale_id=venda.id,
            user_id=user_id
        )
        db.add(movimento)
        
    db.commit()
    db.refresh(venda)
    return venda

def listar(db: Session, store_id: UUID, skip: int = 0, limit: int = 50):
    return db.query(Venda).filter(Venda.store_id == store_id).order_by(Venda.created_at.desc()).offset(skip).limit(limit).all()

def buscar_por_id(db: Session, id: UUID, store_id: UUID):
    venda = db.query(Venda).filter(Venda.id == id, Venda.store_id == store_id).first()
    if not venda:
         raise HTTPException(status_code=404, detail="Venda não encontrada")
    return venda
