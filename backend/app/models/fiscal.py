import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Text, JSON, Integer, Boolean
from sqlalchemy import UUID
from app.database import Base


class NotaFiscal(Base):
    """
    Registra cada nota fiscal emitida (NF-e para produtos, NFS-e para serviços).
    Emissão via API PlugNotas. O ciclo de vida completo é:

        pending  → processing → authorized
                             → rejected     (SEFAZ rejeitou)
                → error      (falha de envio – reemissível)
        authorized → cancelled

    O campo `provider_id` é o ID retornado pelo PlugNotas no envio e é
    OBRIGATÓRIO para consultas, cancelamentos e suporte. Deve ser salvo assim
    que o provedor responde com 200/201.

    O campo `idempotency_key` garante que não enviamos a mesma nota duas vezes
    mesmo em caso de retry — enviamos como cabeçalho X-Idempotency-Key.
    """
    __tablename__ = "notas_fiscais"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"), nullable=False, index=True)

    # Tipo: 'nfe' (produtos – NF-e/NFC-e) | 'nfse' (serviços)
    tipo = Column(String(10), nullable=False, index=True)

    # Origem: qual venda ou agendamento gerou a nota
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="SET NULL"), nullable=True)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)

    # Dados do destinatário (snapshot no momento da emissão)
    destinatario_nome = Column(String(255))
    destinatario_cpf_cnpj = Column(String(20))
    destinatario_email = Column(String(255))
    destinatario_endereco = Column(Text)

    # Valores
    valor_total = Column(Numeric(10, 2), nullable=False)
    valor_servicos = Column(Numeric(10, 2), default=0)
    valor_deducoes = Column(Numeric(10, 2), default=0)
    aliquota_iss = Column(Numeric(5, 4), default=0)

    # Ciclo de vida da nota
    # pending    – criada; aguardando envio ao PlugNotas
    # processing – enviada ao PlugNotas; aguardando retorno da SEFAZ/Prefeitura
    # authorized – autorizada; chave de acesso e DANFE disponíveis
    # rejected   – rejeitada pela SEFAZ/Prefeitura (com motivo)
    # cancelled  – cancelada com sucesso após autorização
    # error      – falha de comunicação ou configuração; pode ser reenviada
    status = Column(String(20), default="pending", nullable=False, index=True)
    motivo_rejeicao = Column(Text)          # texto retornado pela SEFAZ ou PlugNotas
    explicacao_ai = Column(Text)            # Tradução amigável da IA para o erro técnico

    # Idempotência – garante que retries não duplicam a nota no provedor
    idempotency_key = Column(String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # Dados do provedor
    provider = Column(String(50), default="plugnotas")
    provider_id = Column(String(255), index=True)   # ID da nota no PlugNotas (salvo imediatamente no 201)
    lote_id = Column(String(255))                   # ID do lote (quando enviado em batch)
    numero_nota = Column(String(20))                # Número da NF emitida
    chave_acesso = Column(String(60))               # Chave de 44 dígitos (NF-e)
    serie = Column(String(5))
    protocolo = Column(String(60))
    danfe_url = Column(Text)                        # Link para PDF/DANFE
    xml_url = Column(Text)                          # Link para XML assinado
    provider_response = Column(JSON)                # Última resposta completa do provedor

    # Retry
    tentativas = Column(Integer, default=0)         # número de tentativas de envio
    max_tentativas = Column(Integer, default=3)     # limite configurável
    ultimo_erro = Column(Text)                      # último erro de rede/API

    # Webhook
    webhook_recebido_em = Column(DateTime)          # quando o retorno chegou via webhook

    # Descrição legível (exibição na UI)
    descricao = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    authorized_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    last_sync_at = Column(DateTime)                 # última consulta de status via polling
