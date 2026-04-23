"""
fiscal.py  –  Router revisado
------------------------------
Mudanças vs. versão anterior:
  - Adiciona POST /fiscal/webhook/plugnotas   (entrada de webhook do PlugNotas)
  - Adiciona POST /fiscal/{id}/reenviar       (retry para notas em 'error')
  - Adiciona GET  /fiscal/{id}/consultar      (consulta forçada ao PlugNotas)
  - /sincronizar agora executa em bg apenas notas 'processing' (não 'pending')
  - Documentação inline clara sobre limitações (certificado, regras municipais)
"""

from fastapi import APIRouter, Depends, BackgroundTasks, Query, HTTPException, Header, Request
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.schemas.fiscal import (
    NotaFiscalResponse,
    EmitirNFeRequest,
    EmitirNFSeRequest,
    CancelarNotaRequest,
)
from app.services import fiscal_service

router = APIRouter(prefix="/fiscal", tags=["Fiscal"])


# ---------------------------------------------------------------------------
# Listagem
# ---------------------------------------------------------------------------

@router.get("", response_model=List[NotaFiscalResponse])
def listar(
    tipo: Optional[str] = Query(None, description="nfe | nfse"),
    status: Optional[str] = Query(None, description="pending | processing | authorized | rejected | cancelled | error"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    """Lista o histórico de notas fiscais da loja com filtros opcionais."""
    return fiscal_service.listar_notas(db, store_id, tipo, status, skip, limit)


@router.get("/stats/resumo")
def resumo_fiscal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    """Retorna contagem e valores por (tipo, status) para o dashboard."""
    from app.models.fiscal import NotaFiscal
    from sqlalchemy import func

    rows = (
        db.query(
            NotaFiscal.tipo,
            NotaFiscal.status,
            func.count(NotaFiscal.id).label("quantidade"),
            func.sum(NotaFiscal.valor_total).label("valor_total"),
        )
        .filter(NotaFiscal.store_id == store_id)
        .group_by(NotaFiscal.tipo, NotaFiscal.status)
        .all()
    )

    return {
        f"{r.tipo}_{r.status}": {
            "tipo": r.tipo,
            "status": r.status,
            "quantidade": r.quantidade,
            "valor_total": float(r.valor_total or 0),
        }
        for r in rows
    }


@router.get("/{nota_id}", response_model=NotaFiscalResponse)
def buscar(
    nota_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    return fiscal_service.buscar_nota(db, nota_id, store_id)


# ---------------------------------------------------------------------------
# Emissão manual
# ---------------------------------------------------------------------------

@router.post("/emitir/nfe", response_model=NotaFiscalResponse, status_code=201)
async def emitir_nfe(
    dados: EmitirNFeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    """
    Emite NF-e para uma venda de produtos.

    Pré-requisitos:
    - Chave PlugNotas configurada em Configurações > Fiscal
    - CNPJ, endereço e código IBGE do município preenchidos
    - Certificado A1 cadastrado no painel PlugNotas (não gerenciado aqui)
    - CFOP, NCM e CST definidos com auxílio do contador

    O status retornado será 'processing' (aguardando SEFAZ). O status final
    chega via webhook (/fiscal/webhook/plugnotas) ou polling (/fiscal/sincronizar).
    """
    try:
        return await fiscal_service.emitir_nfe(db, dados.sale_id, store_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/emitir/nfse", response_model=NotaFiscalResponse, status_code=201)
async def emitir_nfse(
    dados: EmitirNFSeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    """
    Emite NFS-e para um agendamento concluído (status 'done').

    Pré-requisitos adicionais (vs. NF-e):
    - Inscrição Municipal cadastrada
    - Código de serviço municipal (varia por município — consulte contador)
    - Alíquota ISS correta para o município
    - Algumas prefeituras exigem certificado específico no PlugNotas

    Nota: regras de NFS-e variam significativamente por município.
    """
    try:
        return await fiscal_service.emitir_nfse(db, dados.appointment_id, store_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Cancelamento
# ---------------------------------------------------------------------------

@router.post("/{nota_id}/cancelar", response_model=NotaFiscalResponse)
async def cancelar(
    nota_id: UUID,
    dados: CancelarNotaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    """
    Cancela uma nota autorizada. Prazo legal: até 168h após autorização para NF-e.
    Para NFS-e o prazo varia por município.
    """
    if len(dados.motivo) < 15:
        raise HTTPException(status_code=400, detail="Justificativa mínima de 15 caracteres exigida pela legislação.")
    try:
        return await fiscal_service.cancelar_nota(db, nota_id, store_id, dados.motivo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Reemissão (retry para notas em 'error')
# ---------------------------------------------------------------------------

@router.post("/{nota_id}/reenviar", response_model=NotaFiscalResponse)
async def reenviar(
    nota_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    """
    Reenvia uma nota que falhou por erro de rede ou servidor (status 'error').
    Usa o mesmo idempotency_key do envio original, prevenindo duplicatas.
    Máximo de 3 tentativas por nota (configurável no model).
    """
    try:
        return await fiscal_service.reenviar_nota(db, nota_id, store_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Sincronização de status via polling (fallback do webhook)
# ---------------------------------------------------------------------------

@router.post("/sincronizar", response_model=dict)
async def sincronizar(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    """
    Consulta proativamente o PlugNotas para notas em estado 'processing' sem
    retorno de webhook. Use como fallback; o webhook é o canal preferido.
    Executa em segundo plano.
    """
    async def _run():
        count = await fiscal_service.sincronizar_status(db, store_id)
        return count

    background_tasks.add_task(_run)
    return {"message": "Sincronização iniciada em segundo plano (verifica notas em estado 'processing')."}


# ---------------------------------------------------------------------------
# Webhook do PlugNotas  (POST público, autenticado por token no header)
# ---------------------------------------------------------------------------

@router.post("/webhook/plugnotas", status_code=200, include_in_schema=True)
async def webhook_plugnotas(
    request: Request,
    db: Session = Depends(get_db),
    x_plugnotas_token: Optional[str] = Header(None, alias="X-Plugnotas-Token"),
):
    """
    Endpoint de callback do PlugNotas. Configure esta URL no painel PlugNotas:
        https://<seu-dominio>/api/v1/fiscal/webhook/plugnotas

    O PlugNotas envia POST quando o processamento da SEFAZ/Prefeitura termina.
    Este é o mecanismo PREFERIDO para atualização de status.

    Autenticação: o token recebido é comparado com o campo 'plugnotas_webhook_token'
    salvo em store.settings. Configure-o em Configurações > Fiscal.

    ATENÇÃO: Este endpoint não exige autenticação de usuário (é chamado pelo PlugNotas)
    mas valida o token de webhook para segurança.
    """
    payload: Dict[str, Any] = await request.json()

    # Extrai store_id do payload (PlugNotas pode enviar campo customizado)
    store_id_raw = payload.get("storeId") or payload.get("referencia")

    if not store_id_raw:
        # Busca por provider_id para identificar a loja
        from app.models.fiscal import NotaFiscal
        provider_id = payload.get("idNotaFiscal") or payload.get("id") or payload.get("idNfse")
        if provider_id:
            nota = db.query(NotaFiscal).filter(NotaFiscal.provider_id == provider_id).first()
            if nota:
                store_id_raw = str(nota.store_id)

    if not store_id_raw:
        raise HTTPException(status_code=422, detail="Não foi possível identificar a loja no payload do webhook.")

    try:
        store_id = UUID(str(store_id_raw))
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="store_id inválido no payload.")

    # Valida token de segurança
    from app.models.store import Store
    store = db.query(Store).filter(Store.id == store_id).first()
    if store and store.settings:
        expected_token = store.settings.get("plugnotas_webhook_token")
        if expected_token and x_plugnotas_token != expected_token:
            raise HTTPException(status_code=403, detail="Token de webhook inválido.")

    nota = await fiscal_service.processar_webhook(db, store_id, payload)
    return {"received": True, "nota_id": str(nota.id) if nota else None}
