"""
fiscal_service.py  –  revisado
-------------------------------

Melhorias aplicadas vs. versão anterior:
  1.  Status 'processing' introduzido: nota enviada ao PlugNotas mas ainda sem
      retorno final da SEFAZ/Prefeitura. Só muda para authorized/rejected via
      webhook ou polling.
  2.  Status 'error' introduzido: falha de rede/config; nota é reemissível
      (enquanto tentativas < max_tentativas).
  3.  provider_id salvo imediatamente quando PlugNotas responde 200/201, antes
      do commit final. É o campo mais crítico para consultas e cancelamentos.
  4.  Idempotência: toda chamada usa o campo nota.idempotency_key como
      X-Idempotency-Key no header, evitando duplicatas em retries.
  5.  Mapeamento de status ampliado com todos os códigos documentados pelo
      PlugNotas (numerico e string).
  6.  reenviar_nota() para notas em estado 'error' (retry controlado).
  7.  processar_webhook() para receber callbacks do PlugNotas sem depender
      apenas de polling.
  8.  Nota sobre certificado A1: o sistema assume que o certificado foi
      cadastrado diretamente na conta PlugNotas (painel deles). Não gerenciamos
      o arquivo .pfx localmente. Para NFS-e em prefeituras que exigem certificado
      específico, o operador deve configurar isso no painel PlugNotas.

Fluxo completo:
  Venda          → emitir_nfe()
  Serviço done   → emitir_nfse()
  PlugNotas POST → processar_webhook()     ← principal caminho de retorno
  Fallback       → sincronizar_status()    ← polling para notas sem webhook
  Reemissão      → reenviar_nota()         ← notas em 'error'
"""

import httpx
import logging
import uuid as uuid_lib
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.fiscal import NotaFiscal
from app.models.venda import Venda
from app.models.agendamento import Agendamento
from app.models.cliente import Cliente
from app.models.store import Store

logger = logging.getLogger(__name__)

PLUGNOTAS_BASE_URL = "https://api.plugnotas.com.br"

# Mapeamento completo de status PlugNotas → status interno
# Fonte: https://docs.plugnotas.com.br  (códigos numéricos e strings)
PLUGNOTAS_STATUS_AUTHORIZED = {
    "autorizado", "authorized", "4", "100",
    "concluido", "concluído", "emitido",
}
PLUGNOTAS_STATUS_REJECTED = {
    "rejeitado", "rejected", "3", "denegado", "denegada",
    "erro_sefaz", "erro", "invalido", "inválido",
}
PLUGNOTAS_STATUS_CANCELLED = {
    "cancelado", "cancelled", "5", "cancelada",
}
PLUGNOTAS_STATUS_PROCESSING = {
    "processando", "processing", "em_processamento", "1", "2",
    "aguardando", "em_fila", "enviado", "pendente",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_plugnotas_key(store: Store) -> Optional[str]:
    if store.settings and isinstance(store.settings, dict):
        return store.settings.get("plugnotas_api_key") or store.settings.get("fiscal_api_key")
    return None


def _headers(api_key: str, idempotency_key: Optional[str] = None) -> Dict[str, str]:
    h = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }
    if idempotency_key:
        h["X-Idempotency-Key"] = idempotency_key
    return h


def _cpf_cnpj_limpo(valor: Optional[str]) -> str:
    if not valor:
        return ""
    return "".join(c for c in valor if c.isdigit())


def _endereco_cliente(cliente: Optional[Cliente]) -> str:
    return cliente.address or "" if cliente else ""


def _map_payment(method: str) -> str:
    """Códigos SEFAZ para meios de pagamento (Tabela 1 – Forma de Pagamento)."""
    mapping = {
        "pix": "17",
        "credit_card": "03",
        "debit_card": "04",
        "cash": "01",
        "boleto": "15",
        "other": "99",
    }
    return mapping.get(method, "99")


def _normalizar_status_plugnotas(raw: str) -> str:
    """
    Converte qualquer string de status do PlugNotas para o status interno.
    Retorna 'processing' quando o estado ainda não é final.
    """
    s = str(raw).lower().strip()
    if s in PLUGNOTAS_STATUS_AUTHORIZED:
        return "authorized"
    if s in PLUGNOTAS_STATUS_REJECTED:
        return "rejected"
    if s in PLUGNOTAS_STATUS_CANCELLED:
        return "cancelled"
    if s in PLUGNOTAS_STATUS_PROCESSING:
        return "processing"
    # Estado desconhecido → mantém como processing (não descarta a nota)
    logger.warning(f"[Fiscal] Status PlugNotas desconhecido: '{raw}', mantendo 'processing'")
    return "processing"


def _aplicar_dados_autorizacao(nota: NotaFiscal, data: Dict[str, Any]) -> None:
    """Preenche todos os campos de retorno quando a nota é autorizada."""
    nota.status = "authorized"
    nota.authorized_at = datetime.utcnow()
    nota.last_sync_at = datetime.utcnow()
    nota.numero_nota = str(data.get("numeroNota") or data.get("numero") or "")
    nota.chave_acesso = data.get("chaveAcesso") or data.get("chave") or ""
    nota.serie = str(data.get("serie") or "")
    nota.protocolo = data.get("protocolo") or data.get("nProtocolo") or ""
    nota.danfe_url = data.get("linkDanfe") or data.get("danfeUrl") or data.get("urlDanfe") or ""
    nota.xml_url = data.get("linkXml") or data.get("xmlUrl") or data.get("urlXml") or ""
    nota.provider_response = data


def _aplicar_dados_rejeicao(nota: NotaFiscal, data: Dict[str, Any], motivo_extra: str = "") -> None:
    nota.status = "rejected"
    nota.last_sync_at = datetime.utcnow()
    import asyncio
    asyncio.create_task(_gerar_explicacao_ai_rejeicao(db, nota))
    nota.motivo_rejeicao = (
        data.get("mensagemRetorno")
        or data.get("motivo")
        or data.get("descricao")
        or motivo_extra
        or str(data)
    )
    nota.provider_response = data


# ---------------------------------------------------------------------------
# Builders de payload
# ---------------------------------------------------------------------------

def _build_nfe_payload(venda: Venda, store: Store, cliente: Optional[Cliente]) -> Dict[str, Any]:
    """
    Monta o payload para NF-e modelo 55 conforme spec PlugNotas.
    Documentação: https://docs.plugnotas.com.br/nfe

    IMPORTANTE: Este payload usa os parâmetros fiscais salvos em store.settings.
    Valores como CFOP, NCM, CST e regime tributário DEVEM ser validados com
    o contador do cliente antes de ir à produção.

    O certificado A1 deve estar cadastrado diretamente no painel PlugNotas.
    """
    S = store.settings or {}
    cnpj = _cpf_cnpj_limpo(S.get("cnpj", ""))
    ie = S.get("inscricao_estadual", "ISENTO")
    regime = str(S.get("regime_tributario", "1"))

    itens = []
    for item in (venda.items or []):
        cfop = S.get("cfop_padrao", "5102")
        ncm = S.get("ncm_padrao", "98010000")
        cst = S.get("cst_padrao", "500")

        itens.append({
            "codigo": str(item.product_id)[:20],
            "descricao": "Produto Pet Shop",
            "cfop": cfop,
            "ncm": ncm,
            "cst": cst,
            "quantidade": float(item.quantity or 1),
            "unidade": "UN",
            "valorUnitario": float(item.unit_price),
            "valorTotal": float(item.total),
            "origem": 0,
        })

    return {
        "emitente": {
            "cpfCnpj": cnpj,
            "razaoSocial": store.name,
            "nomeFantasia": S.get("nome_fantasia", store.name),
            "inscricaoEstadual": ie,
            "regimeTributario": regime,
            "endereco": {
                "logradouro": S.get("logradouro", store.address or ""),
                "numero": S.get("numero", "S/N"),
                "bairro": S.get("bairro", ""),
                "codigoMunicipio": S.get("codigo_municipio", ""),
                "uf": S.get("uf", "SP"),
                "cep": S.get("cep", ""),
            },
        },
        "destinatario": {
            "cpfCnpj": _cpf_cnpj_limpo(cliente.cpf if cliente else ""),
            "nome": cliente.name if cliente else "Consumidor Final",
            "email": cliente.email if cliente else "",
            "endereco": {
                "logradouro": _endereco_cliente(cliente),
                "numero": "",
                "bairro": "",
                "codigoMunicipio": S.get("codigo_municipio", ""),
                "uf": S.get("uf", "SP"),
                "cep": "",
            },
        },
        "naturezaOperacao": "VENDA DE MERCADORIAS",
        "tipoOperacao": 1,
        "finalidade": 1,
        "indicadorPresenca": 1,
        "pagamentos": [{"meio": _map_payment(venda.payment_method), "valor": float(venda.total)}],
        "itens": itens,
        "informacoesAdicionais": f"Pet Shop — Ref: {str(venda.id)[:8]}",
    }


def _build_nfse_payload(ag: Agendamento, store: Store, cliente: Optional[Cliente]) -> Dict[str, Any]:
    """
    Monta o payload para NFS-e conforme spec PlugNotas.
    Documentação: https://docs.plugnotas.com.br/nfse

    IMPORTANTE:
      - `codigoServico` é obrigatório e varia por município. Deve ser obtido
        com o contador e configurado em Configurações > Fiscal.
      - `aliquotaIss` também é municipal; o valor padrão 5% é apenas um exemplo.
      - Certificado A1: gerenciado pelo PlugNotas. Para NFS-e, algumas
        prefeituras aceitam apenas o parâmetro RPS; outras exigem certificado.
    """
    S = store.settings or {}
    cnpj = _cpf_cnpj_limpo(S.get("cnpj", ""))
    im = S.get("inscricao_municipal", "")
    aliquota_iss = float(S.get("aliquota_iss", "0.05"))
    codigo_servico = S.get("codigo_servico_municipal", "")
    cnae = S.get("cnae_servico", "9609208")

    servico_nome = ag.service_legacy or (ag.service_rel.name if ag.service_rel else "Serviço Pet Shop")
    valor_bruto = float(ag.price or "0") if ag.price else 0.0
    valor_base = valor_bruto
    valor_iss = round(valor_base * aliquota_iss, 2)

    return {
        "emitente": {
            "cpfCnpj": cnpj,
            "razaoSocial": store.name,
            "inscricaoMunicipal": im,
            "endereco": {
                "logradouro": S.get("logradouro", store.address or ""),
                "numero": S.get("numero", "S/N"),
                "bairro": S.get("bairro", ""),
                "codigoMunicipio": S.get("codigo_municipio", ""),
                "uf": S.get("uf", "SP"),
                "cep": S.get("cep", ""),
            },
        },
        "tomador": {
            "cpfCnpj": _cpf_cnpj_limpo(cliente.cpf if cliente else ""),
            "nome": cliente.name if cliente else "Tomador não identificado",
            "email": cliente.email if cliente else "",
            "endereco": {
                "logradouro": _endereco_cliente(cliente),
                "numero": "",
                "bairro": "",
                "codigoMunicipio": S.get("codigo_municipio_tomador", S.get("codigo_municipio", "")),
                "uf": S.get("uf", "SP"),
                "cep": "",
            },
        },
        "servico": {
            "descricao": f"{servico_nome} — Pet Shop",
            "codigoServico": codigo_servico,
            "cnae": cnae,
            "aliquotaIss": aliquota_iss,
            "issRetido": False,
            "valorServicos": valor_bruto,
            "valorDeducoes": 0.0,
            "valorBaseCalculo": valor_base,
            "valorIss": valor_iss,
        },
        "competencia": ag.date.strftime("%Y-%m-%d") if ag.date else datetime.utcnow().strftime("%Y-%m-%d"),
        "naturezaOperacao": str(S.get("nfse_natureza", "1")),
        "regimeEspecialTributacao": None,
        "optanteSimplesMunicipal": S.get("optante_simples_municipal", True),
        "incentivadorCultural": False,
        "informacoesAdicionais": f"Pet Shop — Agend.: {str(ag.id)[:8]}",
    }


# ---------------------------------------------------------------------------
# Validação mínima antes de enviar
# ---------------------------------------------------------------------------

def _validar_config_fiscal(store: Store, tipo: str) -> Optional[str]:
    """
    Retorna uma string de erro se a configuração estiver incompleta,
    ou None se estiver apta para emissão.
    """
    S = store.settings or {}
    cnpj = _cpf_cnpj_limpo(S.get("cnpj", ""))
    if len(cnpj) not in (11, 14):
        return "CNPJ/CPF do emitente inválido ou não cadastrado em Configurações > Fiscal."
    if not S.get("codigo_municipio"):
        return "Código IBGE do município não configurado em Configurações > Fiscal."
    if tipo == "nfse" and not S.get("inscricao_municipal"):
        return "Inscrição Municipal obrigatória para NFS-e. Configure em Configurações > Fiscal."
    if tipo == "nfse" and not S.get("codigo_servico_municipal"):
        return "Código de serviço municipal obrigatório para NFS-e. Consulte seu contador."
    return None


# ---------------------------------------------------------------------------
# Emissão
# ---------------------------------------------------------------------------

async def emitir_nfe(db: Session, sale_id: UUID, store_id: UUID) -> NotaFiscal:
    """
    Emite NF-e para uma venda. Cria registro 'pending', envia ao PlugNotas
    usando idempotency_key, salva provider_id imediatamente e muda para
    'processing'. O status final chega via webhook ou polling.
    """
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise ValueError("Loja não encontrada")

    api_key = _get_plugnotas_key(store)
    if not api_key:
        raise ValueError("Chave PlugNotas não configurada. Acesse Configurações > Fiscal.")

    erro_config = _validar_config_fiscal(store, "nfe")
    if erro_config:
        raise ValueError(erro_config)

    venda = db.query(Venda).filter(Venda.id == sale_id, Venda.store_id == store_id).first()
    if not venda:
        raise ValueError("Venda não encontrada")

    # Idempotência: não emite segunda vez para a mesma venda (exceto se error)
    existente = db.query(NotaFiscal).filter(
        NotaFiscal.sale_id == sale_id,
        NotaFiscal.status.notin_(["rejected", "cancelled", "error"]),
    ).first()
    if existente:
        return existente

    cliente = db.query(Cliente).filter(Cliente.id == venda.client_id).first() if venda.client_id else None
    payload = _build_nfe_payload(venda, store, cliente)

    idempotency_key = str(uuid_lib.uuid4())
    nota = NotaFiscal(
        store_id=store_id,
        tipo="nfe",
        sale_id=sale_id,
        destinatario_nome=cliente.name if cliente else "Consumidor Final",
        destinatario_cpf_cnpj=_cpf_cnpj_limpo(cliente.cpf if cliente else ""),
        destinatario_email=cliente.email if cliente else "",
        destinatario_endereco=_endereco_cliente(cliente),
        valor_total=venda.total,
        status="pending",
        provider="plugnotas",
        idempotency_key=idempotency_key,
        descricao=f"Venda #{str(sale_id)[:8]} — {len(venda.items or [])} item(s)",
        tentativas=0,
    )
    db.add(nota)
    db.flush()

    await _enviar_ao_plugnotas(db, nota, api_key, "nfe", payload)

    db.commit()
    db.refresh(nota)
    return nota


async def emitir_nfse(db: Session, appointment_id: UUID, store_id: UUID) -> NotaFiscal:
    """
    Emite NFS-e para um agendamento concluído. Regras iguais ao emitir_nfe:
    idempotência, validação prévia, provider_id salvo imediatamente.
    """
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise ValueError("Loja não encontrada")

    api_key = _get_plugnotas_key(store)
    if not api_key:
        raise ValueError("Chave PlugNotas não configurada. Acesse Configurações > Fiscal.")

    erro_config = _validar_config_fiscal(store, "nfse")
    if erro_config:
        raise ValueError(erro_config)

    ag = db.query(Agendamento).filter(
        Agendamento.id == appointment_id,
        Agendamento.store_id == store_id,
    ).first()
    if not ag:
        raise ValueError("Agendamento não encontrado")

    if ag.status not in ("done", "completed"):
        raise ValueError(
            f"NFS-e só pode ser emitida para serviços concluídos. Status atual: '{ag.status}'."
        )

    existente = db.query(NotaFiscal).filter(
        NotaFiscal.appointment_id == appointment_id,
        NotaFiscal.status.notin_(["rejected", "cancelled", "error"]),
    ).first()
    if existente:
        return existente

    cliente = ag.pet.client if (ag.pet and ag.pet.client) else None
    S = store.settings or {}
    aliquota_iss = Decimal(str(S.get("aliquota_iss", "0.05")))
    valor = Decimal(str(ag.price or "0")) if ag.price else Decimal("0")

    payload = _build_nfse_payload(ag, store, cliente)
    idempotency_key = str(uuid_lib.uuid4())

    nota = NotaFiscal(
        store_id=store_id,
        tipo="nfse",
        appointment_id=appointment_id,
        destinatario_nome=cliente.name if cliente else "Tomador não identificado",
        destinatario_cpf_cnpj=_cpf_cnpj_limpo(cliente.cpf if cliente else ""),
        destinatario_email=cliente.email if cliente else "",
        destinatario_endereco=_endereco_cliente(cliente),
        valor_total=valor,
        valor_servicos=valor,
        aliquota_iss=aliquota_iss,
        status="pending",
        provider="plugnotas",
        idempotency_key=idempotency_key,
        descricao=f"Serviço: {ag.service_legacy or 'Serviço Pet Shop'} — {ag.pet.name if ag.pet else ''}",
        tentativas=0,
    )
    db.add(nota)
    db.flush()

    await _enviar_ao_plugnotas(db, nota, api_key, "nfse", payload)

    db.commit()
    db.refresh(nota)
    return nota


async def _enviar_ao_plugnotas(
    db: Session,
    nota: NotaFiscal,
    api_key: str,
    tipo: str,
    payload: Dict[str, Any],
) -> None:
    """
    Envia a nota ao PlugNotas com idempotency_key e trata a resposta.

    Casos:
      200/201 → provider_id salvo; status → 'processing'
      4xx     → configuração ou dados incorretos; status → 'rejected'
      5xx/rede→ falha temporária; status → 'error' (reemissível)
    """
    nota.tentativas = (nota.tentativas or 0) + 1

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{PLUGNOTAS_BASE_URL}/{tipo}",
                headers=_headers(api_key, nota.idempotency_key),
                json=payload,
            )

            resp_data = resp.json() if resp.content else {}
            nota.provider_response = resp_data

            if resp.status_code in (200, 201):
                # provider_id é crítico: salva imediatamente
                pid = (
                    resp_data.get("idNotaFiscal")
                    or resp_data.get("id")
                    or resp_data.get("idNfse")
                )
                nota.provider_id = pid
                nota.status = "processing"
                logger.info(f"[Fiscal] {tipo.upper()} enviada. provider_id={pid}")

            elif resp.status_code == 422:
                # Erro de validação de dados – não é reemissível sem correção
                nota.status = "rejected"
                nota.motivo_rejeicao = (
                    resp_data.get("message")
                    or resp_data.get("mensagem")
                    or str(resp_data)
                )
                logger.error(f"[Fiscal] {tipo.upper()} rejeitada (422): {nota.motivo_rejeicao}")

            elif 400 <= resp.status_code < 500:
                # Outros erros do cliente (401, 403, 404...)
                nota.status = "error"
                nota.ultimo_erro = f"HTTP {resp.status_code}: {resp.text[:500]}"
                logger.error(f"[Fiscal] Erro {resp.status_code} ao emitir {tipo}: {resp.text[:200]}")

            else:
                # 5xx → erro temporário do servidor; deixa como reemissível
                nota.status = "error"
                nota.ultimo_erro = f"HTTP {resp.status_code}: {resp.text[:500]}"
                logger.error(f"[Fiscal] Erro servidor {resp.status_code} ao emitir {tipo}")

    except httpx.TimeoutException:
        nota.status = "error"
        nota.ultimo_erro = "Timeout na comunicação com PlugNotas (>30s)"
        logger.error(f"[Fiscal] Timeout ao emitir {tipo}: nota.id={nota.id}")

    except httpx.RequestError as exc:
        nota.status = "error"
        nota.ultimo_erro = f"Erro de rede: {str(exc)}"
        logger.exception(f"[Fiscal] Erro de rede ao emitir {tipo}: {exc}")


# ---------------------------------------------------------------------------
# Reemissão (retry para notas em 'error')
# ---------------------------------------------------------------------------

async def reenviar_nota(db: Session, nota_id: UUID, store_id: UUID) -> NotaFiscal:
    """
    Reenvia uma nota que está no estado 'error', respeitando o limite de tentativas.
    Não altera o idempotency_key existente para manter idempotência.
    """
    nota = db.query(NotaFiscal).filter(
        NotaFiscal.id == nota_id,
        NotaFiscal.store_id == store_id,
    ).first()
    if not nota:
        raise ValueError("Nota fiscal não encontrada")
    if nota.status != "error":
        raise ValueError(f"Reemissão só é permitida para notas com status 'error'. Status atual: '{nota.status}'")
    if (nota.tentativas or 0) >= (nota.max_tentativas or 3):
        raise ValueError(
            f"Limite de {nota.max_tentativas} tentativas atingido. "
            "Verifique e corrija os dados fiscais antes de tentar novamente."
        )

    store = db.query(Store).filter(Store.id == store_id).first()
    api_key = _get_plugnotas_key(store)
    if not api_key:
        raise ValueError("Chave PlugNotas não configurada.")

    # Reconstrói o payload a partir dos dados de origem
    if nota.tipo == "nfe" and nota.sale_id:
        venda = db.query(Venda).filter(Venda.id == nota.sale_id).first()
        cliente = db.query(Cliente).filter(Cliente.id == venda.client_id).first() if venda and venda.client_id else None
        payload = _build_nfe_payload(venda, store, cliente)
    elif nota.tipo == "nfse" and nota.appointment_id:
        ag = db.query(Agendamento).filter(Agendamento.id == nota.appointment_id).first()
        cliente = ag.pet.client if (ag and ag.pet and ag.pet.client) else None
        payload = _build_nfse_payload(ag, store, cliente)
    else:
        raise ValueError("Não foi possível reconstruir o payload: origem não encontrada.")

    await _enviar_ao_plugnotas(db, nota, api_key, nota.tipo, payload)
    db.commit()
    db.refresh(nota)
    return nota


# ---------------------------------------------------------------------------
# Cancelamentoasync def _gerar_explicacao_ai_rejeicao(db: Session, nota: NotaFiscal):
    """
    Usa o Agente Fiscal AI para traduzir o erro técnico da SEFAZ.
    """
    if not nota.motivo_rejeicao:
        return

    try:
        prompt = f"""
        Você é o Agente Fiscal AI do sistema Pet Shop Administration.
        Um documento fiscal ({nota.tipo.upper()}) foi REJEITADO pela SEFAZ/Prefeitura.
        
        ERRO TÉCNICO: "{nota.motivo_rejeicao}"
        
        DADOS DA NOTA:
        - Cliente: {nota.destinatario_nome}
        - CPF/CNPJ: {nota.destinatario_cpf_cnpj}
        - Valor: R$ {nota.valor_total}
        
        SUA TAREFA:
        1. Explique em PORTUGUÊS SIMPLES o que esse erro significa para um dono de pet shop.
        2. Diga exatamente o que ele deve fazer para corrigir (ex: "Complete o endereço do cliente", "O NCM do produto 'X' está errado").
        3. Seja curto e direto (máximo 3 frases).
        
        Não use juridiquês. Se o erro for sobre falta de dados, aponte quais dados.
        """
        
        # Chama o serviço de IA configurado para o agente 'fiscal'
        explicacao = await ai_service.executar_agente(db, nota.store_id, "fiscal", prompt)
        
        if explicacao:
            # Atualiza a nota com a explicação amigável
            nota.explicacao_ai = explicacao
            db.commit()
            logger.info(f"Explicação AI gerada para nota {nota.id}")
            
    except Exception as e:
        logger.error(f"Erro ao gerar explicação AI fiscal: {e}")

# ---------------------------------------------------------------------------

async def cancelar_nota(db: Session, nota_id: UUID, store_id: UUID, motivo: str) -> NotaFiscal:
    """
    Cancela uma nota autorizada via PlugNotas.
    Prazo: NF-e até 168h após autorização; NFS-e varia por município.
    """
    store = db.query(Store).filter(Store.id == store_id).first()
    api_key = _get_plugnotas_key(store)
    if not api_key:
        raise ValueError("Chave PlugNotas não configurada.")

    nota = db.query(NotaFiscal).filter(
        NotaFiscal.id == nota_id,
        NotaFiscal.store_id == store_id,
    ).first()
    if not nota:
        raise ValueError("Nota fiscal não encontrada")
    if nota.status != "authorized":
        raise ValueError("Somente notas com status 'authorized' podem ser canceladas.")
    if not nota.provider_id:
        raise ValueError("provider_id ausente; não é possível cancelar sem o ID do provedor.")

    endpoint = f"{PLUGNOTAS_BASE_URL}/{nota.tipo}/{nota.provider_id}/cancel"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                endpoint,
                headers=_headers(api_key),
                json={"justificativa": motivo},
            )
            resp_data = resp.json() if resp.content else {}
            if resp.status_code in (200, 201):
                nota.status = "cancelled"
                nota.cancelled_at = datetime.utcnow()
                nota.provider_response = resp_data
            else:
                raise ValueError(f"PlugNotas recusou o cancelamento: HTTP {resp.status_code} – {resp.text[:300]}")
    except httpx.RequestError as exc:
        raise ValueError(f"Erro de conexão ao cancelar: {str(exc)}")

    db.commit()
    db.refresh(nota)
    return nota


# ---------------------------------------------------------------------------
# Webhook (caminho principal de retorno do PlugNotas)
# ---------------------------------------------------------------------------

async def processar_webhook(
    db: Session,
    store_id: UUID,
    payload: Dict[str, Any],
) -> Optional[NotaFiscal]:
    """
    Processa notificação webhook enviada pelo PlugNotas após processamento
    na SEFAZ/Prefeitura. Este é o mecanismo PREFERIDO; polling é o fallback.

    O PlugNotas envia POST para a URL configurada no painel deles.
    Endpoint: POST /api/v1/fiscal/webhook/plugnotas

    Campos esperados no payload:
        idNotaFiscal  – provider_id da nota
        tipo          – "nfe" | "nfse"
        situacao / status – string ou código numérico
        (demais campos conforme documentação PlugNotas)
    """
    provider_id = (
        payload.get("idNotaFiscal")
        or payload.get("id")
        or payload.get("idNfse")
    )
    if not provider_id:
        logger.warning(f"[Webhook] Payload sem idNotaFiscal: {str(payload)[:200]}")
        return None

    # Busca com trava de registro (FOR UPDATE) para evitar concorrência entre webhook e polling
    nota = db.query(NotaFiscal).filter(
        NotaFiscal.provider_id == provider_id,
        NotaFiscal.store_id == store_id,
    ).with_for_update().first()

    if not nota:
        logger.warning(f"[Webhook] Nota não encontrada para provider_id={provider_id}")
        return None

    raw_status = payload.get("situacao") or payload.get("status") or ""
    status_interno = _normalizar_status_plugnotas(str(raw_status))

    # Idempotência: Se a nota já está no status reportado ou em estado final imutável, ignora
    if nota.status == status_interno:
        logger.debug(f"[Webhook] Nota {nota.id} já possui status '{status_interno}'. Ignorando duplicata.")
        return nota

    if nota.status in ("authorized", "cancelled") and status_interno not in ("cancelled"):
        logger.info(f"[Webhook] Nota {nota.id} já está em estado final '{nota.status}'. Bloqueando reversão para '{status_interno}'.")
        return nota

    nota.webhook_recebido_em = datetime.utcnow()
    nota.last_sync_at = datetime.utcnow()

    if status_interno == "authorized":
        _aplicar_dados_autorizacao(nota, payload)
        logger.info(f"[Webhook] Nota {nota.id} AUTORIZADA via webhook. Chave: {nota.chave_acesso}")
    elif status_interno == "rejected":
        _aplicar_dados_rejeicao(nota, payload)
        logger.warning(f"[Webhook] Nota {nota.id} REJEITADA via webhook: {nota.motivo_rejeicao}")
    elif status_interno == "cancelled":
        nota.status = "cancelled"
        nota.cancelled_at = datetime.utcnow()
        nota.provider_response = payload
    else:
        nota.status = "processing"
        nota.provider_response = payload

    db.commit()
    db.refresh(nota)
    return nota


# ---------------------------------------------------------------------------
# Polling de status (fallback quando webhook não retornou)
# ---------------------------------------------------------------------------

async def sincronizar_status(db: Session, store_id: UUID) -> int:
    """
    Consulta o PlugNotas para notas em 'processing' que não receberam webhook.
    Use apenas como fallback — o webhook é o canal principal.
    """
    store = db.query(Store).filter(Store.id == store_id).first()
    api_key = _get_plugnotas_key(store) if store else None
    if not api_key:
        return 0

    # Sincroniza notas processing (ainda aguardando SEFAZ)
    # e error sem provider_id (tentar sincronizar mesmo assim)
    pendentes = db.query(NotaFiscal).filter(
        NotaFiscal.store_id == store_id,
        NotaFiscal.status == "processing",
        NotaFiscal.provider_id.isnot(None),
    ).all()

    atualizadas = 0
    async with httpx.AsyncClient(timeout=20.0) as client:
        for nota_ref in pendentes:
            # Re-busca cada nota com lock para garantir que o webhook não esteja processando-a agora
            nota = db.query(NotaFiscal).filter(NotaFiscal.id == nota_ref.id).with_for_update().first()
            if not nota or nota.status != "processing":
                continue

            try:
                endpoint = f"{PLUGNOTAS_BASE_URL}/{nota.tipo}/{nota.provider_id}"
                resp = await client.get(endpoint, headers=_headers(api_key))
                nota.last_sync_at = datetime.utcnow()

                if resp.status_code != 200:
                    logger.warning(f"[Polling] {resp.status_code} ao consultar nota {nota.provider_id}")
                    continue

                data = resp.json()
                raw = str(data.get("situacao") or data.get("status") or "")
                status_interno = _normalizar_status_plugnotas(raw)

                if status_interno == "authorized":
                    _aplicar_dados_autorizacao(nota, data)
                    atualizadas += 1
                elif status_interno == "rejected":
                    _aplicar_dados_rejeicao(nota, data)
                    atualizadas += 1
                elif status_interno == "cancelled":
                    nota.status = "cancelled"
                    nota.cancelled_at = datetime.utcnow()
                    nota.provider_response = data
                    atualizadas += 1
                # 'processing' → não atualiza; aguarda próximo ciclo

            except Exception as exc:
                logger.warning(f"[Polling] Erro ao consultar nota {nota.id}: {exc}")

    db.commit()
    return atualizadas


# ---------------------------------------------------------------------------
# Consultas
# ---------------------------------------------------------------------------

def listar_notas(
    db: Session,
    store_id: UUID,
    tipo: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    query = db.query(NotaFiscal).filter(NotaFiscal.store_id == store_id)
    if tipo:
        query = query.filter(NotaFiscal.tipo == tipo)
    if status:
        query = query.filter(NotaFiscal.status == status)
    return query.order_by(NotaFiscal.created_at.desc()).offset(skip).limit(limit).all()


def buscar_nota(db: Session, nota_id: UUID, store_id: UUID) -> NotaFiscal:
    from fastapi import HTTPException
    nota = db.query(NotaFiscal).filter(
        NotaFiscal.id == nota_id,
        NotaFiscal.store_id == store_id,
    ).first()
    if not nota:
        raise HTTPException(status_code=404, detail="Nota fiscal não encontrada")
    return nota
