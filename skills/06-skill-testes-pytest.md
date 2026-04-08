# Skill: Testes com Pytest

## Objetivo
Escrever testes automatizados para o backend FastAPI usando pytest, garantindo qualidade e evitando regressoes durante o desenvolvimento.

## Dependencias

```txt
# requirements-test.txt
pytest==8.x
httpx==0.27.x          # Cliente async para testar FastAPI
pytest-asyncio==0.23.x
factory-boy==3.x       # Criacao de dados de teste
faker==24.x            # Dados falsos realistas
```

## Regras Fundamentais

1. **Banco de dados separado para testes** - nunca usar o DB de producao
2. **Fixtures para dados comuns** - usuario, store, produto prontos
3. **Testar casos de sucesso e erro** - status 200, 404, 422, 401, 403
4. **Isolar testes** - cada teste deve ser independente
5. **Nomear testes claramente** - `test_criar_produto_sucesso`, `test_criar_produto_sem_auth`

## Configuracao (conftest.py)

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.store import Store
from app.models.usuario import Usuario
from app.core.security import hash_senha, criar_access_token
import uuid

# Banco de testes em memoria
TEST_DATABASE_URL = 'sqlite:///./test.db'

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={'check_same_thread': False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

@pytest.fixture(scope='session', autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)

@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def store(db):
    store = Store(
        id=uuid.uuid4(),
        nome='Pet Shop Teste',
        whatsapp='11999999999',
        is_active=True
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store

@pytest.fixture
def admin_user(db, store):
    user = Usuario(
        id=uuid.uuid4(),
        nome='Admin Teste',
        email='admin@teste.com',
        senha_hash=hash_senha('senha123'),
        role='admin',
        store_id=store.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def funcionario_user(db, store):
    user = Usuario(
        id=uuid.uuid4(),
        nome='Funcionario Teste',
        email='func@teste.com',
        senha_hash=hash_senha('senha123'),
        role='funcionario',
        store_id=store.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def admin_token(admin_user):
    return criar_access_token({
        'sub': str(admin_user.id),
        'store_id': str(admin_user.store_id),
        'role': admin_user.role,
        'nome': admin_user.nome
    })

@pytest.fixture
def funcionario_token(funcionario_user):
    return criar_access_token({
        'sub': str(funcionario_user.id),
        'store_id': str(funcionario_user.store_id),
        'role': funcionario_user.role,
        'nome': funcionario_user.nome
    })

@pytest.fixture
def auth_headers_admin(admin_token):
    return {'Authorization': f'Bearer {admin_token}'}

@pytest.fixture
def auth_headers_func(funcionario_token):
    return {'Authorization': f'Bearer {funcionario_token}'}
```

## Testes de Auth

```python
# tests/test_auth.py
def test_login_sucesso(client, admin_user):
    response = client.post('/api/v1/auth/login', json={
        'email': 'admin@teste.com',
        'senha': 'senha123'
    })
    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'

def test_login_senha_errada(client, admin_user):
    response = client.post('/api/v1/auth/login', json={
        'email': 'admin@teste.com',
        'senha': 'senhaerrada'
    })
    assert response.status_code == 401

def test_login_email_inexistente(client):
    response = client.post('/api/v1/auth/login', json={
        'email': 'naoexiste@teste.com',
        'senha': 'senha123'
    })
    assert response.status_code == 401

def test_rota_sem_token(client):
    response = client.get('/api/v1/produtos')
    assert response.status_code == 401
```

## Testes de Produtos

```python
# tests/test_produtos.py
import pytest

def test_listar_produtos_vazio(client, auth_headers_func):
    response = client.get('/api/v1/produtos', headers=auth_headers_func)
    assert response.status_code == 200
    data = response.json()
    assert data['items'] == []
    assert data['total'] == 0

def test_criar_produto_sucesso(client, auth_headers_admin, db, store):
    # Criar categoria primeiro
    cat_response = client.post('/api/v1/categorias', json={
        'nome': 'Racao'
    }, headers=auth_headers_admin)
    assert cat_response.status_code == 201
    categoria_id = cat_response.json()['id']

    response = client.post('/api/v1/produtos', json={
        'nome': 'Racao Golden',
        'preco': 89.90,
        'categoria_id': categoria_id,
        'estoque_atual': 10,
        'estoque_minimo': 3
    }, headers=auth_headers_admin)

    assert response.status_code == 201
    data = response.json()
    assert data['nome'] == 'Racao Golden'
    assert data['preco'] == 89.90
    assert 'id' in data

def test_criar_produto_sem_permissao(client, auth_headers_func):
    response = client.post('/api/v1/produtos', json={
        'nome': 'Produto Qualquer',
        'preco': 10.0,
        'categoria_id': '00000000-0000-0000-0000-000000000000'
    }, headers=auth_headers_func)
    assert response.status_code == 403

def test_criar_produto_preco_invalido(client, auth_headers_admin):
    response = client.post('/api/v1/produtos', json={
        'nome': 'Produto Invalido',
        'preco': -10.0,
        'categoria_id': '00000000-0000-0000-0000-000000000000'
    }, headers=auth_headers_admin)
    assert response.status_code == 422

def test_buscar_produto_inexistente(client, auth_headers_func):
    response = client.get(
        '/api/v1/produtos/00000000-0000-0000-0000-000000000000',
        headers=auth_headers_func
    )
    assert response.status_code == 404
```

## Testes de Estoque

```python
# tests/test_estoque.py
def test_movimentacao_entrada(client, auth_headers_admin, produto_fixture):
    response = client.post('/api/v1/estoque/movimentacao', json={
        'produto_id': str(produto_fixture.id),
        'tipo': 'entrada',
        'quantidade': 20,
        'motivo': 'Reposicao'
    }, headers=auth_headers_admin)
    assert response.status_code == 201
    assert response.json()['tipo'] == 'entrada'

def test_alerta_estoque_baixo(client, auth_headers_admin, produto_fixture):
    # Produto com estoque abaixo do minimo
    response = client.get('/api/v1/estoque/alertas', headers=auth_headers_admin)
    assert response.status_code == 200
    # Verificar se o produto aparece nos alertas
    alertas = response.json()
    assert isinstance(alertas, list)
```

## Executar Testes

```bash
# Rodar todos os testes
pytest

# Com verbose
pytest -v

# Apenas um arquivo
pytest tests/test_produtos.py -v

# Com coverage
pytest --cov=app --cov-report=html

# Parar no primeiro erro
pytest -x

# Rodar testes marcados
pytest -m 'estoque'
```

## Boas Praticas

1. **Testar a API, nao o service diretamente** - usar o TestClient
2. **Um assert claro por teste** - focar em um comportamento
3. **Fixtures com scope correto** - `session` para dados estaticos, `function` para dados mutaveis
4. **Nomes descritivos** - `test_criar_produto_com_preco_negativo_retorna_422`
5. **Cleanup automatico** - usar `db.rollback()` para isolar cada teste
