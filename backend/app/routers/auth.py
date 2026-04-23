from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr
import re, uuid

from app.database import get_db
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.store import Store
from app.schemas.auth import LoginRequest, Token

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    store_name: str
    name: str
    email: EmailStr
    password: str


@router.post("/register", status_code=201)
async def register(dados: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == dados.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

    # Gera slug único a partir do nome da loja
    slug_base = re.sub(r"[^a-z0-9]+", "-", dados.store_name.lower()).strip("-")
    slug = slug_base
    count = 1
    while db.query(Store).filter(Store.slug == slug).first():
        slug = f"{slug_base}-{count}"
        count += 1

    store = Store(name=dados.store_name, slug=slug)
    db.add(store)
    db.flush()

    user = User(
        store_id=store.id,
        name=dados.name,
        email=dados.email,
        password_hash=security.get_password_hash(dados.password),
        role="owner",
    )
    db.add(user)
    db.commit()
    return {"message": "Loja e administrador criados com sucesso!", "store_id": str(store.id)}


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    import time
    
    # Hash dummy (bcrypt) pré-calculado para evitar erro de timing caso o usuário não exista
    dummy_hash = "$2b$12$D2MvRjL/8rR.0s5Yt1/M1OCwE.K9X4o.DqM.8A9E2P9rN8Qo4/eGi"
    
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # Previne ataque de temporização: sempre executa a função de hash
    valid_password = False
    if user:
        valid_password = security.verify_password(credentials.password, user.password_hash)
    else:
        security.verify_password(credentials.password, dummy_hash)
        
    if not user or not valid_password:
        time.sleep(1.5)  # Atraso anti-bruteforce (Throttling simples)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo.")

    access_token = security.create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}
