from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.core.config import settings
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_user_or_mfa(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def get_current_user_optional(token: str = Depends(OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False))) -> User:
    """Retorna usuário se token válido, ou None se não fornecido"""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id:
            db = next(get_db())
            return db.query(User).filter(User.id == UUID(user_id)).first()
    except JWTError:
        pass
    return None


def require_mfa_if_enabled(current_user: User = Depends(get_current_user)) -> User:
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=401,
            detail="MFA_REQUIRED",
            headers={"WWW-Authenticate": "MFA"}
        )
    return current_user


def get_any_role(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user


def get_gerente_ou_admin(current_user: User = Depends(get_any_role)) -> User:
    if current_user.role not in ["manager", "owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user


def get_current_store_id(current_user: User = Depends(get_any_role)) -> UUID:
    return current_user.store_id
