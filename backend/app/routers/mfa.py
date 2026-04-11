from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pyotp
import io
import base64

from app.database import get_db
from app.core import security
from app.core.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/auth/mfa", tags=["MFA"])


class MFASetupResponse(BaseModel):
    secret: str
    qr_code_base64: str
    message: str


class MFAVerifyRequest(BaseModel):
    code: str


class MFAResponse(BaseModel):
    access_token: str
    token_type: str


def generate_secret() -> str:
    return pyotp.random_base32()


def get_totp(secret: str) -> pyotp.TOTP:
    return pyotp.TOTP(secret)


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Gera configuração inicial do MFA"""
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA já está habilitado")
    
    secret = generate_secret()
    totp = get_totp(secret)
    
    provisioning_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name="SFCPPC-PetShop"
    )
    
    import qrcode
    qr = qrcode.QRCode(box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    user.mfa_secret = secret
    db.commit()
    
    return MFASetupResponse(
        secret=secret,
        qr_code_base64=qr_base64,
        message="Escaneie o QR Code no app Google Authenticator"
    )


@router.post("/enable", response_model=MFAResponse)
async def enable_mfa(
    dados: MFAVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Ativa o MFA após verificação do código"""
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if not user.mfa_secret:
        raise HTTPException(status_code=400, detail="Execute setup primeiro")
    
    totp = get_totp(user.mfa_secret)
    if not totp.verify(dados.code):
        raise HTTPException(status_code=400, detail="Código inválido")
    
    user.mfa_enabled = True
    db.commit()
    
    from datetime import timedelta
    from app.core.config import settings
    
    access_token = security.create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    return MFAResponse(access_token=access_token, token_type="bearer")


@router.post("/disable", response_model=MFAResponse)
async def disable_mfa(
    dados: MFAVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Desativa o MFA"""
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if not user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA não está ativo")
    
    if not user.mfa_secret:
        raise HTTPException(status_code=400, detail="Configure primeiro")
    
    totp = get_totp(user.mfa_secret)
    if not totp.verify(dados.code):
        raise HTTPException(status_code=400, detail="Código inválido")
    
    user.mfa_enabled = False
    user.mfa_secret = None
    db.commit()
    
    from datetime import timedelta
    from app.core.config import settings
    
    access_token = security.create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    return MFAResponse(access_token=access_token, token_type="bearer")


@router.post("/verify", response_model=MFAResponse)
async def verify_mfa(
    dados: MFAVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Verifica código MFA e retorna token"""
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA não está configurado")
    
    totp = get_totp(user.mfa_secret)
    if not totp.verify(dados.code):
        raise HTTPException(status_code=400, detail="Código inválido")
    
    from datetime import timedelta
    from app.core.config import settings
    
    access_token = security.create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    return MFAResponse(access_token=access_token, token_type="bearer")