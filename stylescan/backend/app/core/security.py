"""
Barber authentication — JWT tokens + password hashing.

Uses python-jose (JWT) and bcrypt (password hashing), both already in requirements.txt.
"""

from datetime import datetime, timezone, timedelta

import bcrypt
from jose import jwt, JWTError

from app.core.config import settings

_ALG = "HS256"
_EXPIRE_DAYS = 30


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_barber_token(barber_id: str) -> str:
    payload = {
        "sub": barber_id,
        "type": "barber",
        "exp": datetime.now(timezone.utc) + timedelta(days=_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALG)


def decode_barber_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALG])
        if payload.get("type") != "barber":
            return None
        return payload.get("sub")
    except JWTError:
        return None
