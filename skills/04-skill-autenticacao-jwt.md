# Skill: Autenticacao e Autorizacao JWT

## Objetivo
Implementar autenticacao segura com JWT, controle de roles (admin, gerente, funcionario) e middleware de autorizacao no FastAPI.

## Stack de Auth
- `python-jose[cryptography]` - geracao e validacao de JWT
- `passlib[bcrypt]` - hash de senhas
- `FastAPI Security` - dependencias de autenticacao

## Regras Fundamentais

1. **Nunca armazenar senha em texto puro** - sempre usar bcrypt
2. **JWT com expiracao curta** - access token: 8h, refresh token: 7 dias
3. **Store ID sempre no token** - isolar dados por loja automaticamente
4. **Role no token** - evitar consulta ao banco em cada request
5. **Refresh token em httpOnly cookie** - proteger contra XSS

## Roles do Sistema

```
admin      -> acesso total (dono da loja)
gerente    -> acesso a relatorios e configuracoes
funcionario -> acesso operacional (vendas, estoque)
```

## Implementacao

### Config de Auth
```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 horas
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = '.env'

settings = Settings()
```

### Hash de Senha
```python
# app/core/security.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import uuid

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha: str, hash: str) -> bool:
    return pwd_context.verify(senha, hash)
```

### Criacao de Token
```python
def criar_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=480))
    to_encode.update({'exp': expire, 'type': 'access'})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def criar_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({'exp': expire, 'type': 'refresh'})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decodificar_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

### Payload do Token
```python
# Estrutura do payload JWT
{
    'sub': 'user-uuid-aqui',       # ID do usuario
    'store_id': 'store-uuid-aqui', # ID da loja
    'role': 'admin',               # Role do usuario
    'nome': 'Joao Silva',          # Nome para exibicao
    'exp': 1234567890,             # Expiracao
    'type': 'access'               # Tipo do token
}
```

### Dependencias FastAPI
```python
# app/core/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import decodificar_token
from app.database import get_db
from app.models.usuario import Usuario
import uuid

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Credenciais invalidas',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    payload = decodificar_token(token)
    if not payload or payload.get('type') != 'access':
        raise credentials_exception

    user_id = payload.get('sub')
    if not user_id:
        raise credentials_exception

    user = db.query(Usuario).filter(Usuario.id == uuid.UUID(user_id)).first()
    if not user or not user.is_active:
        raise credentials_exception

    return user

async def get_current_store_id(
    current_user: Usuario = Depends(get_current_user)
) -> uuid.UUID:
    return current_user.store_id
```

### Guards por Role
```python
# app/core/deps.py (continuacao)
from functools import wraps

def require_role(*roles: str):
    async def role_checker(
        current_user: Usuario = Depends(get_current_user)
    ) -> Usuario:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Acesso negado. Role necessaria: {roles}'
            )
        return current_user
    return role_checker

# Dependencias prontas para uso nas rotas
get_admin = require_role('admin')
get_gerente_ou_admin = require_role('admin', 'gerente')
get_any_role = require_role('admin', 'gerente', 'funcionario')
```

### Router de Auth
```python
# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import verificar_senha, criar_access_token, criar_refresh_token
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix='/auth', tags=['Autenticacao'])

@router.post('/login', response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(
        Usuario.email == credentials.email,
        Usuario.is_active == True
    ).first()

    if not usuario or not verificar_senha(credentials.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Email ou senha incorretos'
        )

    token_data = {
        'sub': str(usuario.id),
        'store_id': str(usuario.store_id),
        'role': usuario.role,
        'nome': usuario.nome
    }

    access_token = criar_access_token(token_data)
    refresh_token = criar_refresh_token({'sub': str(usuario.id)})

    # Salvar refresh token em httpOnly cookie
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite='strict',
        max_age=7 * 24 * 60 * 60  # 7 dias em segundos
    )

    return TokenResponse(
        access_token=access_token,
        token_type='bearer',
        expires_in=480 * 60
    )

@router.post('/logout')
async def logout(response: Response):
    response.delete_cookie('refresh_token')
    return {'message': 'Logout realizado com sucesso'}
```

### Uso nas Rotas
```python
# Rota publica (sem auth)
@router.get('/health')
async def health_check():
    return {'status': 'ok'}

# Rota para qualquer usuario autenticado
@router.get('/produtos', response_model=ProdutoList)
async def listar_produtos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_any_role),
    store_id: uuid.UUID = Depends(get_current_store_id)
):
    return produto_service.listar(db, store_id)

# Rota apenas para admin ou gerente
@router.post('/produtos', response_model=ProdutoResponse, status_code=201)
async def criar_produto(
    produto: ProdutoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_gerente_ou_admin),
    store_id: uuid.UUID = Depends(get_current_store_id)
):
    return produto_service.criar(db, produto, store_id)

# Rota exclusiva para admin
@router.delete('/usuarios/{id}')
async def deletar_usuario(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_admin)
):
    return usuario_service.deletar(db, id, current_user.store_id)
```

## Variaveis de Ambiente Necessarias

```env
SECRET_KEY=sua-chave-secreta-muito-longa-e-aleatoria-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

## Boas Praticas de Seguranca

1. **SECRET_KEY** com no minimo 32 caracteres aleatorios (`openssl rand -hex 32`)
2. **Nunca logar tokens** em producao
3. **Rate limiting** no endpoint de login para prevenir brute force
4. **Invalidar tokens** ao trocar senha (adicionar campo `password_changed_at`)
5. **HTTPS obrigatorio** em producao para proteger tokens em transit
