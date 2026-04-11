from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from pydantic import BaseModel
from decimal import Decimal

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.models.venda import Venda
from app.models.store import Store
from app.services import asaas_service
import app.jobs

router = APIRouter(prefix="/payments", tags=["Payments"])


class CreatePixRequest(BaseModel):
    sale_id: UUID


class PixResponse(BaseModel):
    charge_id: str
    pix_qr_code: str
    pix_code: str
    status: str
    value: float
    url: str


class WebhookAsaasRequest(BaseModel):
    payment_id: str
    status: str


@router.post("/pix", response_model=PixResponse)
async def criar_pix(
    dados: CreatePixRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    """Gera QR Code Pix para uma venda"""
    venda = db.query(Venda).filter(
        Venda.id == dados.sale_id,
        Venda.store_id == store_id
    ).first()
    
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada")
    
    if venda.payment_method != 'pix':
        raise HTTPException(status_code=400, detail="Método de pagamento deve ser 'pix'")
    
    if venda.payment_status != 'pending':
        raise HTTPException(status_code=400, detail="Venda não está pendente")
    
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store or not store.asaas_customer_id:
        raise HTTPException(status_code=400, detail="Loja não configurada para Pix")
    
    try:
        result = await asaas_service.criar_cobranca_pix(
            customer_id=store.asaas_customer_id,
            amount=venda.total,
            description=f"Venda #{venda.id.hex[:8]}",
            due_date=None
        )
        
        venda.asaas_charge_id = result["id"]
        venda.pix_qr_code = result.get("pix_qr_code") or result.get("pix_code", "")
        db.commit()
        
        return PixResponse(
            charge_id=result["id"],
            pix_qr_code=result.get("pix_qr_code", ""),
            pix_code=result.get("pix_code", ""),
            status=result["status"],
            value=float(result["value"]),
            url=result.get("url", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar Pix: {str(e)}")


@router.post("/pix/{charge_id}/status")
async def verificar_status(
    charge_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    """Verifica status de uma cobrança Pix"""
    try:
        status = await asaas_service.verificar_status_cobranca(charge_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def webhook_asaas(
    dados: WebhookAsaasRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Webhook do Asaas para receber notificações de pagamento"""
    try:
        venda = db.query(Venda).filter(
            Venda.asaas_charge_id == dados.payment_id
        ).first()
        
        if not venda:
            return {"message": "Venda não encontrada"}
        
        if dados.status == "CONFIRMED" or dados.status == "RECEIVED":
            venda.payment_status = 'paid'
            from datetime import datetime
            venda.paid_at = datetime.utcnow()
            
            from app.models.estoque import MovimentacaoEstoque
            for item in venda.items:
                produto = item.product
                if produto.sale_type == 'WEIGHT':
                    if item.weight:
                        produto.weight_in_stock = (produto.weight_in_stock or 0) - item.weight
                else:
                    if item.quantity:
                        produto.quantity = (produto.quantity or 0) - item.quantity
                
                mov = MovimentacaoEstoque(
                    product_id=produto.id,
                    store_id=venda.store_id,
                    type='exit',
                    quantity=item.quantity,
                    weight=item.weight,
                    reason='sale',
                    sale_id=venda.id,
                    user_id=venda.user_id
                )
                db.add(mov)
            
            db.commit()
            return {"message": "Pagamento confirmado"}
        
        elif dados.status == "REJECTED" or dados.status == "OVERDUE":
            venda.payment_status = 'cancelled'
            db.commit()
            return {"message": "Pagamento cancelado/vencido"}
        
        return {"message": "Status processado"}
    
    except Exception as e:
        return {"error": str(e)}


@router.get("/pending-check")
async def verificar_pendentes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    """Job manual para verificar pagamentos pendentes"""
    background_tasks.add_task(app.jobs.check_pending_payments, db, store_id)
    return {"message": "Verificação iniciada em background"}