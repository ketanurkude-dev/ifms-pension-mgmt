from datetime import datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Pensioner

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(subject: str, purpose: str, expires_minutes: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "purpose": purpose, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_purpose: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("purpose") != expected_purpose:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token purpose")

    return payload["sub"]


def get_current_pensioner(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Pensioner:
    ppo_number = decode_token(token, expected_purpose="access")
    pensioner = (
        db.query(Pensioner)
        .filter(Pensioner.ppo_number == ppo_number, Pensioner.is_deleted.is_(False))
        .first()
    )
    if not pensioner or not pensioner.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Pensioner not found")
    return pensioner


def require_approver(pensioner: Pensioner = Depends(get_current_pensioner)) -> Pensioner:
    """Use as a dependency on any endpoint only a pension officer may call."""
    if pensioner.role != "pension_officer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Approver role required")
    return pensioner
