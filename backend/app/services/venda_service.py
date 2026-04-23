from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException
from typing import List
from decimal import Decimal

from app.models.venda import Venda, ItemVenda, VendaPagamento
from app.models.produto import Produto
from app.models.estoque import MovimentacaoEstoque
from app.models.store import Store
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

from app.models.financeiro import CaixaSession

def realizar_venda(db: Session, dados: VendaCreate, store_id: UUID, user_id: UUID):
    # Busca caixa aberto
    session = db.query(CaixaSession).filter(
        CaixaSession.store_id == store_id,
        CaixaSession.closed_at == None
    ).first()
    
    total = Decimal('0.00')
    for item in dados.items:
        total += item.total
    
    validar_desconto(total, dados.discount or Decimal('0.00'))
    subtotal_with_discount = total - (dados.discount or Decimal('0.00'))
    
    venda = Venda(
        store_id=store_id,
        client_id=dados.client_id,
        user_id=user_id,
        cashier_id=session.id if session else None,
        total=subtotal_with_discount,
        discount=dados.discount or Decimal('0.00'),

        payment_method=dados.payment_method or (dados.payments[0].method if dados.payments else 'outro'),
        payment_status='paid', # Por padrão pago no multi-pagamento local
        notes=dados.notes
    )
    db.add(venda)
    db.flush()
    
    # Processa Pagamentos
    store = db.query(Store).filter(Store.id == store_id).first()
    settings = store.settings or {}
    fees = settings.get("payment_fees", {
        "pix": 0,
        "cash": 0,
        "credit_card": 2.99,
        "debit_card": 1.50
    })

    if dados.payments:
        for p_data in dados.payments:
            fee_percent = Decimal(str(fees.get(p_data.method, 0)))
            fee_amount = (p_data.amount * fee_percent / 100).quantize(Decimal('0.01'))
            
            pagamento = VendaPagamento(
                sale_id=venda.id,
                method=p_data.method,
                amount=p_data.amount,
                fee_amount=fee_amount,
                net_amount=p_data.amount - fee_amount
            )
            db.add(pagamento)
    elif dados.payment_method:
        # Fallback para método único (retrocompatibilidade)
        fee_percent = Decimal(str(fees.get(dados.payment_method, 0)))
        fee_amount = (venda.total * fee_percent / 100).quantize(Decimal('0.01'))
        pagamento = VendaPagamento(
            sale_id=venda.id,
            method=dados.payment_method,
            amount=venda.total,
            fee_amount=fee_amount,
            net_amount=venda.total - fee_amount
        )
        db.add(pagamento)
    
    for i_data in dados.items:
        qty = i_data.quantity or 0
        weight = i_data.weight

        if i_data.pacote_id:
            from app.models.pacote import Pacote, ClientePacote
            pacote = db.query(Pacote).filter(Pacote.id == i_data.pacote_id, Pacote.store_id == store_id).first()
            if not pacote:
                raise HTTPException(status_code=404, detail="Pacote não encontrado")
            
            # Credita o cliente se identificado
            if dados.client_id:
                for p_item in pacote.items:
                    saldo = db.query(ClientePacote).filter(
                        ClientePacote.client_id == dados.client_id,
                        ClientePacote.service_id == p_item.service_id,
                        ClientePacote.store_id == store_id
                    ).first()
                    
                    if not saldo:
                        saldo = ClientePacote(
                            store_id=store_id,
                            client_id=dados.client_id,
                            service_id=p_item.service_id,
                            balance=0
                        )
                        db.add(saldo)
                    
                    saldo.balance += (p_item.quantity * qty)
            
            item = ItemVenda(
                sale_id=venda.id,
                pacote_id=i_data.pacote_id,
                quantity=qty,
                unit_price=i_data.unit_price,
                total=i_data.total
            )
            db.add(item)
            continue

        produto = db.query(Produto).filter(Produto.id == i_data.product_id, Produto.store_id == store_id).first()
        if not produto:
            raise HTTPException(status_code=404, detail=f"Produto {i_data.product_id} não encontrado.")
        
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

def listar(db: Session, store_id: UUID, skip: int = 0, limit: int = 50, cashier_id: UUID = None):
    query = db.query(Venda).filter(Venda.store_id == store_id)
    if cashier_id:
        query = query.filter(Venda.cashier_id == cashier_id)
    return query.order_by(Venda.created_at.desc()).offset(skip).limit(limit).all()

def buscar_por_id(db: Session, id: UUID, store_id: UUID):
    venda = db.query(Venda).filter(Venda.id == id, Venda.store_id == store_id).first()
    if not venda:
         raise HTTPException(status_code=404, detail="Venda não encontrada")
    return venda
