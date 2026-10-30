import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.config import REFRESH_TOKEN_EXPIRE_DAYS
from ..models import AccessLog, RefreshToken, User
from ..repositories.auth_repository import (
    close_expired_sessions,
    close_session,
    create_refresh_token_record,
    create_session_records,
    create_user,
    get_access_logs_paginated,
    get_active_session,
    get_active_session_by_id,
    get_refresh_token,
    get_user_by_email,
    revoke_refresh_token,
    revoke_refresh_tokens,
)
from ..repositories.auth_repository import get_user_by_id as get_user_by_id_repository
from ..schemas import (
    AccessLogPaginationResponse,
    AccessLogResponse,
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
    user = get_user_by_email(db, user_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos."
        )

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos"
        )

    now = datetime.now(UTC)

    close_expired_sessions(db, user.id, now)

    db.commit()

    active_session = get_active_session(db, user.id, now)

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

    try:
        create_session_records(db, access_log, refresh_token_record)
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
    existing_user = get_user_by_email(db, user_data.email)
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

    created_user = create_user(db, new_user)
    db.commit()

    return created_user


def logout_user(user_id: str, session_id: str, db: Session) -> MessageResponse:
    access_log = get_active_session_by_id(db, user_id, session_id)

    if not access_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma sessão ativa encontrada",
        )

    now = datetime.now(UTC)
    close_session(db, access_log, now)

    revoke_refresh_tokens(db, user_id, session_id, now)

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

    stored_token = get_refresh_token(
        db,
        token_hash,
        user_id,
        session_id,
    )

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou revogado.",
        )

    expires_at = stored_token.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expirado",
        )

    active_session = get_active_session_by_id(db, user_id, session_id)

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

    rowcount = revoke_refresh_token(db, stored_token.id, now)

    if rowcount != 1:
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

    try:
        create_refresh_token_record(db, new_refresh_token_record)
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


def get_user_by_id(user_id: str, db: Session) -> User:
    user = get_user_by_id_repository(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
        )

    return user


def get_access_logs(
    user_id: str,
    db: Session,
    page: int = 1,
    limit: int = 10,
) -> AccessLogPaginationResponse:
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A página deve ser maior ou igual a 1.",
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O limite deve estar entre 1 e 100.",
        )

    offset = (page - 1) * limit

    total, logs = get_access_logs_paginated(
        db,
        user_id,
        offset,
        limit,
    )

    items = [
        AccessLogResponse(
            name=user.name,
            email=user.email,
            login_at=access_log.login_at,
            logout_at=access_log.logout_at,
        )
        for user, access_log in logs
    ]

    total_pages = (total + limit - 1) // limit

    return AccessLogPaginationResponse(
        items=items,
        page=page,
        limit=limit,
        total=total,
        pages=total_pages,
    )
