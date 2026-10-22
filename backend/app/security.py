import hashlib
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from .database import get_db
from .models import AccessLog

load_dotenv()


secret_key = os.getenv("SECRET_KEY")

if not secret_key:
    raise RuntimeError("SECRET_KEY não configurada")

SECRET_KEY: str = secret_key

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

password_hash = PasswordHash.recommended()

security = HTTPBearer()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, password_hash_value: str) -> bool:
    return password_hash.verify(password, password_hash_value)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()

    expire = (
        datetime.now(UTC) + expires_delta
        if expires_delta
        else datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()

    expire = (
        datetime.now(UTC) + expires_delta
        if expires_delta
        else datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return encoded_jwt


def decode_refresh_token(token: str) -> tuple[str, str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "refresh":
            raise JWTError("Tipo de token inválido")

        user_id = payload.get("sub")
        session_id = payload.get("session_id")

        if not isinstance(user_id, str) or not isinstance(session_id, str):
            raise JWTError("Payload inválido")

        return user_id, session_id

    except JWTError:
        raise ValueError("Refresh token inválido ou expirado") from None


def decode_access_token(token: str) -> tuple[str, str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "access":
            raise JWTError("Tipo de Token inválido")

        user_id = payload.get("sub")
        session_id = payload.get("session_id")

        if not isinstance(user_id, str) or not isinstance(session_id, str):
            raise JWTError("Payload inválido")

        return user_id, session_id

    except JWTError:
        raise ValueError("Token inválido ou expirado.") from None


def get_current_session(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> tuple[str, str]:
    token = credentials.credentials

    try:
        user_id, session_id = decode_access_token(token)

        active_session = (
            db.query(AccessLog)
            .filter(
                AccessLog.session_id == session_id,
                AccessLog.user_id == user_id,
                AccessLog.logout_at.is_(None),
            )
            .first()
        )

        if not active_session:
            raise ValueError("Sessão encerrada.")

        return user_id, session_id

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou sessão encerrada.",
        )


def get_current_user_id(
    session: tuple[str, str] = Depends(get_current_session),
) -> str:
    user_id, _ = session

    return user_id
