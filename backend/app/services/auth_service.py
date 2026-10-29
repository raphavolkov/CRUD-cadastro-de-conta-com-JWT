import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.config import REFRESH_TOKEN_EXPIRE_DAYS
from ..models import AccessLog, RefreshToken, User
from ..schemas import (
    MessageResponse,
    RefreshRequest,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from ..security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def login_user(user_data: UserLogin, db: Session) -> Token:
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos."
        )

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos"
        )

    now = datetime.now(UTC)

    db.query(AccessLog).filter(
        AccessLog.user_id == user.id,
        AccessLog.logout_at.is_(None),
        AccessLog.expires_at <= now,
    ).update({AccessLog.logout_at: now}, synchronize_session=False)

    db.commit()

    active_session = (
        db.query(AccessLog)
        .filter(
            AccessLog.user_id == user.id,
            AccessLog.logout_at.is_(None),
            AccessLog.expires_at > now,
        )
        .first()
    )

    if active_session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Essa conta já está conectada",
        )

    session_id = str(uuid.uuid4())
    expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(data={"sub": user.id, "session_id": session_id})
    refresh_token = create_refresh_token(
        data={"sub": user.id, "session_id": session_id}
    )

    refresh_expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_token_record = RefreshToken(
        user_id=user.id,
        session_id=session_id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=refresh_expires_at,
    )

    access_log = AccessLog(
        id=session_id,
        session_id=session_id,
        user_id=user.id,
        expires_at=expires_at,
    )

    db.add(access_log)
    db.add(refresh_token_record)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Essa conta já está conectada",
        )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


def register_user(user_data: UserCreate, db: Session) -> UserResponse:
    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado",
        )

    hashed_password = hash_password(user_data.password)

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def logout_user(user_id: str, session_id: str, db: Session) -> MessageResponse:
    access_log = (
        db.query(AccessLog)
        .filter(
            AccessLog.session_id == session_id,
            AccessLog.user_id == user_id,
            AccessLog.logout_at.is_(None),
        )
        .first()
    )

    if not access_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma sessão ativa encontrada",
        )

    now = datetime.now(UTC)
    access_log.logout_at = now

    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.session_id == session_id,
        RefreshToken.revoked_at.is_(None),
    ).update({RefreshToken.revoked_at: now}, synchronize_session=False)

    db.commit()

    return MessageResponse(message="Logout realizado com sucesso")


def refresh_user(data: RefreshRequest, db: Session) -> Token:
    try:
        user_id, session_id = decode_refresh_token(data.refresh_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        ) from None

    now = datetime.now(UTC)
    token_hash = hash_refresh_token(data.refresh_token)

    refresh_token_record = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
            RefreshToken.session_id == session_id,
            RefreshToken.revoked_at.is_(None),
        )
        .first()
    )

    if not refresh_token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou revogado.",
        )

    expires_at = refresh_token_record.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expirado",
        )

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão encerrada ou inválida",
        )

    session_expires_at = active_session.expires_at

    if session_expires_at.tzinfo is None:
        session_expires_at = session_expires_at.replace(tzinfo=UTC)

    if session_expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada",
        )

    new_access_token = create_access_token(
        data={"sub": user_id, "session_id": session_id}
    )

    new_refresh_token = create_refresh_token(
        data={"sub": user_id, "session_id": session_id}
    )

    new_refresh_expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    result = cast(
        CursorResult[Any],
        db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.id == refresh_token_record.id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
            .execution_options(synchronize_session=False)
        ),
    )

    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou revogado.",
        )

    new_refresh_token_record = RefreshToken(
        user_id=user_id,
        session_id=session_id,
        token_hash=hash_refresh_token(new_refresh_token),
        expires_at=new_refresh_expires_at,
    )

    db.add(new_refresh_token_record)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao renovar os tokens.",
        ) from None

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )
