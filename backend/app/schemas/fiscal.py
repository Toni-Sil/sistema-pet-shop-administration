from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal


class NotaFiscalResponse(BaseModel):
    id: UUID
    store_id: UUID
    tipo: str

    sale_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None

    destinatario_nome: Optional[str] = None
    destinatario_cpf_cnpj: Optional[str] = None
    destinatario_email: Optional[str] = None

    valor_total: Decimal
    valor_servicos: Optional[Decimal] = None
    aliquota_iss: Optional[Decimal] = None

    # Ciclo de vida
    # pending | processing | authorized | rejected | cancelled | error
    status: str
    motivo_rejeicao: Optional[str] = None
    explicacao_ai: Optional[str] = None
    ultimo_erro: Optional[str] = None

    # Dados do provedor
    provider: Optional[str] = None
    provider_id: Optional[str] = None
    numero_nota: Optional[str] = None
    chave_acesso: Optional[str] = None
    serie: Optional[str] = None
    protocolo: Optional[str] = None
    danfe_url: Optional[str] = None
    xml_url: Optional[str] = None

    # Retry
    tentativas: Optional[int] = None
    max_tentativas: Optional[int] = None

    descricao: Optional[str] = None
    created_at: datetime
    authorized_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    webhook_recebido_em: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmitirNFeRequest(BaseModel):
    sale_id: UUID


class EmitirNFSeRequest(BaseModel):
    appointment_id: UUID


class CancelarNotaRequest(BaseModel):
    motivo: str
