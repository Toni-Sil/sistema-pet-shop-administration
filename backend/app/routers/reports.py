from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal
import csv
import io

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.models.venda import Venda, ItemVenda
from app.models.financeiro import Despesa
from app.models.produto import Produto
from sqlalchemy import func

router = APIRouter(prefix="/reports", tags=["Reports"])


class DREResponse(BaseModel):
    receita_bruta: float
    despesas: float
    lucro_liquido: float
    margem_percent: float


class DashboardResponse(BaseModel):
    receitaHoje: float
    receitaSemana: float
    receitaMes: float
    despesasMes: float
    lucroMes: float
    vendasHoje: int
    ticketMedio: float
    totalClientes: int


class FinanceiroReportItem(BaseModel):
    categoria: str
    total: float
    quantidade: int

class PaymentMethodReportItem(BaseModel):
    method: str
    total: float
    count: int

class ServiceReportItem(BaseModel):
    service: str
    count: int
    revenue: float


@router.get("/dre", response_model=DREResponse)
def relatorio_dre(
    ano: int = Query(default=None, description="Ano para relatório (padrão: ano atual)"),
    mes: int = Query(default=None, ge=1, le=12, description="Mês específico (opcional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    if ano is None:
        ano = datetime.utcnow().year
    
    query_vendas = db.query(Venda).filter(
        Venda.store_id == store_id,
        Venda.payment_status == 'paid'
    )
    
    query_despesas = db.query(Despesa).filter(
        Despesa.store_id == store_id,
        Despesa.is_paid == True
    )
    
    if mes:
        query_vendas = query_vendas.filter(
            func.extract('month', Venda.created_at) == mes,
            func.extract('year', Venda.created_at) == ano
        )
        query_despesas = query_despesas.filter(
            func.extract('month', Despesa.paid_at) == mes,
            func.extract('year', Despesa.paid_at) == ano
        )
    else:
        query_vendas = query_vendas.filter(
            func.extract('year', Venda.created_at) == ano
        )
        query_despesas = query_despesas.filter(
            func.extract('year', Despesa.paid_at) == ano
        )
    
    receita = query_vendas.with_entities(func.sum(Venda.total)).scalar() or 0
    despesas = query_despesas.with_entities(func.sum(Despesa.amount)).scalar() or 0
    
    lucro = float(receita) - float(despesas)
    margem = (lucro / float(receita) * 100) if receita > 0 else 0
    
    return DREResponse(
        receita_bruta=float(receita),
        despesas=float(despesas),
        lucro_liquido=lucro,
        margem_percent=round(margem, 1)
    )


@router.get("/financial", response_model=DashboardResponse)
def dashboard_financeiro(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    from datetime import timedelta
    from app.models.cliente import Cliente
    
    hoje = datetime.utcnow().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)
    
    vendas = db.query(Venda).filter(
        Venda.store_id == store_id,
        Venda.payment_status == 'paid'
    )
    
    despesas = db.query(Despesa).filter(
        Despesa.store_id == store_id,
        Despesa.is_paid == True
    )
    
    receita_hoje = vendas.filter(
        func.date(Venda.created_at) == hoje
    ).with_entities(func.sum(Venda.total)).scalar() or 0
    
    receita_semana = vendas.filter(
        func.date(Venda.created_at) >= inicio_semana
    ).with_entities(func.sum(Venda.total)).scalar() or 0
    
    receita_mes = vendas.filter(
        func.date(Venda.created_at) >= inicio_mes
    ).with_entities(func.sum(Venda.total)).scalar() or 0
    
    despesas_mes = despesas.filter(
        func.date(Despesa.paid_at) >= inicio_mes
    ).with_entities(func.sum(Despesa.amount)).scalar() or 0
    
    vendas_hoje = vendas.filter(
        func.date(Venda.created_at) == hoje
    ).count()
    
    ticket = float(receita_mes) / vendas.count() if vendas.count() > 0 else 0
    
    lucro_mes = float(receita_mes) - float(despesas_mes)
    
    return DashboardResponse(
        receitaHoje=float(receita_hoje),
        receitaSemana=float(receita_semana),
        receitaMes=float(receita_mes),
        despesasMes=float(despesas_mes),
        lucroMes=lucro_mes,
        vendasHoje=vendas_hoje,
        ticketMedio=round(ticket, 2),
        totalClientes=db.query(Cliente).filter(Cliente.store_id == store_id).count()
    )


@router.get("/expenses-by-category", response_model=List[FinanceiroReportItem])
def despesas_por_categoria(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    from datetime import date
    from datetime import timedelta
    
    inicio_mes = date.today().replace(day=1)
    
    result = db.query(
        Despesa.category,
        func.sum(Despesa.amount).label('total'),
        func.count(Despesa.id).label('quantidade')
    ).filter(
        Despesa.store_id == store_id,
        Despesa.is_paid == True,
        Despesa.paid_at >= inicio_mes
    ).group_by(Despesa.category).all()
    
    return [
        FinanceiroReportItem(
            categoria=r.category,
            total=float(r.total),
            quantidade=r.quantidade
        )
        for r in result
    ]


@router.get("/sales-by-product", response_model=List[FinanceiroReportItem])
def vendas_por_produto(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    from app.models.venda import ItemVenda
    
    result = db.query(
        ItemVenda.product_id,
        func.sum(ItemVenda.total).label('total'),
        func.sum(ItemVenda.quantity).label('quantidade')
    ).join(Venda).filter(
        Venda.store_id == store_id,
        Venda.payment_status == 'paid'
    ).group_by(ItemVenda.product_id).order_by(func.sum(ItemVenda.total).desc()).limit(10).all()
    
    from app.models.produto import Produto
    
    produtos = []
    for r in result:
        produto = db.query(Produto).filter(Produto.id == r.product_id).first()
        if produto:
            produtos.append(FinanceiroReportItem(
                categoria=produto.name,
                total=float(r.total),
                quantidade=r.quantidade
            ))
    
    return produtos

@router.get("/sales-by-payment-method", response_model=List[PaymentMethodReportItem])
def vendas_por_metodo_pagamento(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    result = db.query(
        Venda.payment_method,
        func.sum(Venda.total).label('total'),
        func.count(Venda.id).label('count')
    ).filter(
        Venda.store_id == store_id,
        Venda.payment_status == 'paid'
    ).group_by(Venda.payment_method).all()
    
    return [
        PaymentMethodReportItem(
            method=r.payment_method or "Não informado",
            total=float(r.total),
            count=r.count
        )
        for r in result
    ]

@router.get("/appointments-summary", response_model=List[ServiceReportItem])
def resumo_agendamentos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    from app.models.agendamento import Agendamento
    
    # Normalização básica para evitar duplicatas por causa de case-sensitivity ou underscores
    # Agrupa por service_legacy normalizado
    result = db.query(
        func.lower(func.replace(Agendamento.service_legacy, '_', ' ')).label('service_name'),
        func.count(Agendamento.id).label('count')
    ).filter(
        Agendamento.store_id == store_id
    ).group_by(func.lower(func.replace(Agendamento.service_legacy, '_', ' '))).all()
    
    return [
        ServiceReportItem(
            service=r.service_name.capitalize() if r.service_name else "Outros",
            count=r.count,
            revenue=0.0
        )
        for r in result
    ]


@router.get("/sales/export/csv")
def exportar_vendas_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
    datainicio: Optional[date] = Query(None),
    datafim: Optional[date] = Query(None)
):
    query = db.query(Venda).filter(Venda.store_id == store_id, Venda.payment_status == 'paid')
    
    if datainicio:
        query = query.filter(func.date(Venda.created_at) >= datainicio)
    if datafim:
        query = query.filter(func.date(Venda.created_at) <= datafim)
    
    vendas = query.order_by(Venda.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Data', 'Total', 'Desconto', 'Método', 'Status', 'Notas'])
    
    for v in vendas:
        writer.writerow([
            str(v.id),
            v.created_at.isoformat() if v.created_at else '',
            float(v.total),
            float(v.discount),
            v.payment_method,
            v.payment_status,
            v.notes or ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=vendas.csv"}
    )


@router.get("/expenses/export/csv")
def exportar_despesas_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
    datainicio: Optional[date] = Query(None),
    datafim: Optional[date] = Query(None)
):
    query = db.query(Despesa).filter(Despesa.store_id == store_id)
    
    if datainicio:
        query = query.filter(Despesa.due_date >= datainicio)
    if datafim:
        query = query.filter(Despesa.due_date <= datafim)
    
    despesas = query.order_by(Despesa.due_date.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Descrição', 'Valor', 'Categoria', 'Vencimento', 'Pago em', 'Pago'])
    
    for d in despesas:
        writer.writerow([
            str(d.id),
            d.description,
            float(d.amount),
            d.category,
            d.due_date.isoformat() if d.due_date else '',
            d.paid_at.isoformat() if d.paid_at else '',
            'Sim' if d.is_paid else 'Não'
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=despesas.csv"}
    )


@router.get("/stock/export/csv")
def exportar_estoque_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    produtos = db.query(Produto).filter(Produto.store_id == store_id, Produto.is_active == True).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nome', 'SKU', 'Categoria', 'Preço Custo', 'Preço Venda', 'Qtd', 'Mín', 'Tipo', 'Validade'])
    
    for p in produtos:
        writer.writerow([
            p.name,
            p.sku or '',
            p.category,
            float(p.cost_price),
            float(p.sale_price),
            p.quantity or float(p.weight_in_stock or 0),
            p.min_qty or float(p.min_weight or 0),
            p.sale_type,
            p.expires_at.isoformat() if p.expires_at else ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=estoque.csv"}
    )