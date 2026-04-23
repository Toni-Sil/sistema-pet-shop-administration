import pytest
import respx
import httpx
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.orm import Session

# Importa o app para carregar TODOS os mappers do SQLAlchemy de uma vez
from app.main import app 
from app.database import SessionLocal, Base, engine

# Modelos
from app.models.store import Store
from app.models.venda import Venda
from app.models.fiscal import NotaFiscal
from app.services import fiscal_service

@pytest.fixture(scope="function")
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def mock_store(db: Session):
    store = Store(
        id=uuid4(),
        name="Pet Teste",
        slug="pet-teste-" + str(uuid4())[:8],  # Slug obrigatório
        settings={
            "plugnotas_api_key": "test_key",
            "cnpj": "12345678000199",
            "codigo_municipio": "3550308",
            "nome_fantasia": "Teste Piloto"
        }
    )
    db.add(store)
    db.commit()
    return store

@pytest.fixture
def mock_venda(db: Session, mock_store: Store):
    venda = Venda(
        id=uuid4(),
        store_id=mock_store.id,
        total=Decimal("150.00"),
        payment_method="pix"
    )
    db.add(venda)
    db.commit()
    return venda

@pytest.mark.asyncio
@respx.mock
async def test_emissao_sucesso_ciclo_completo(db: Session, mock_store: Store, mock_venda: Venda):
    provider_id = "pn_" + str(uuid4())[:8]
    respx.post("https://api.plugnotas.com.br/nfe").mock(return_value=httpx.Response(201, json={
        "idNotaFiscal": provider_id,
        "message": "Nota em processamento"
    }))

    nota = await fiscal_service.emitir_nfe(db, mock_venda.id, mock_store.id)
    assert nota.status == "processing"
    assert nota.provider_id == provider_id

    webhook_payload = {
        "idNotaFiscal": provider_id,
        "situacao": "CONCLUIDO",
        "numeroNota": "101",
        "chaveAcesso": "3523" + "1" * 40,
        "linkDanfe": "https://danfe.com/pdf",
        "linkXml": "https://danfe.com/xml"
    }
    
    await fiscal_service.processar_webhook(db, mock_store.id, webhook_payload)
    db.refresh(nota)
    assert nota.status == "authorized"
    assert nota.numero_nota == "101"

@pytest.mark.asyncio
@respx.mock
async def test_rejeicao_dados_invalidos(db: Session, mock_store: Store, mock_venda: Venda):
    respx.post("https://api.plugnotas.com.br/nfe").mock(return_value=httpx.Response(422, json={
        "message": "Dados inválidos: CNPJ"
    }))
    nota = await fiscal_service.emitir_nfe(db, mock_venda.id, mock_store.id)
    assert nota.status == "rejected"
    assert "CNPJ" in nota.motivo_rejeicao

@pytest.mark.asyncio
@respx.mock
async def test_erro_rede_e_retry(db: Session, mock_store: Store, mock_venda: Venda):
    respx.post("https://api.plugnotas.com.br/nfe").mock(side_effect=httpx.ConnectError("Network Down"))
    nota = await fiscal_service.emitir_nfe(db, mock_venda.id, mock_store.id)
    assert nota.status == "error"

    respx.post("https://api.plugnotas.com.br/nfe").mock(return_value=httpx.Response(201, json={"idNotaFiscal": "ret_ok"}))
    await fiscal_service.reenviar_nota(db, nota.id, mock_store.id)
    db.refresh(nota)
    assert nota.status == "processing"
    assert nota.provider_id == "ret_ok"

@pytest.mark.asyncio
async def test_idempotencia_webhook(db: Session, mock_store: Store):
    pid = "dup_" + str(uuid4())[:8]
    nota = NotaFiscal(
        id=uuid4(), store_id=mock_store.id, tipo="nfe", status="processing",
        provider_id=pid, valor_total=Decimal("10.00"),
        idempotency_key=str(uuid4())
    )
    db.add(nota)
    db.commit()

    payload = {"idNotaFiscal": pid, "situacao": "CONCLUIDO", "numeroNota": "777", "chaveAcesso": "CHAVE_TESTE"}
    
    # Simula 2 webhooks iguais chegando quase juntos
    await fiscal_service.processar_webhook(db, mock_store.id, payload)
    await fiscal_service.processar_webhook(db, mock_store.id, payload)
    
    db.refresh(nota)
    assert nota.status == "authorized"
    assert nota.numero_nota == "777"
