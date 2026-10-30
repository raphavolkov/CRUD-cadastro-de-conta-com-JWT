from datetime import datetime
from typing import Any, cast

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult, Result
from sqlalchemy.orm import Session

from ..models import AccessLog, RefreshToken, User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def close_expired_sessions(db: Session, user_id: str, now: datetime) -> None:
    db.query(AccessLog).filter(
        AccessLog.user_id == user_id,
        AccessLog.logout_at.is_(None),
        AccessLog.expires_at <= now,
    ).update({AccessLog.logout_at: now}, synchronize_session=False)


def get_active_session(db: Session, user_id: str, now: datetime) -> AccessLog | None:
    return (
        db.query(AccessLog)
        .filter(
            AccessLog.user_id == user_id,
            AccessLog.logout_at.is_(None),
            AccessLog.expires_at > now,
        )
        .first()
    )


def get_active_session_by_id(
    db: Session,
    user_id: str,
    session_id: str,
) -> AccessLog | None:
    return (
        db.query(AccessLog)
        .filter(
            AccessLog.session_id == session_id,
            AccessLog.user_id == user_id,
            AccessLog.logout_at.is_(None),
        )
        .first()
    )


def revoke_refresh_token(
    db: Session,
    token_id: str,
    now: datetime,
) -> int:
    result = cast(
        CursorResult[Any],
        db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.id == token_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
            .execution_options(synchronize_session=False)
        ),
    )

    return result.rowcount


def revoke_refresh_tokens(
    db: Session,
    user_id: str,
    session_id: str,
    now: datetime,
) -> None:
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.session_id == session_id,
        RefreshToken.revoked_at.is_(None),
    ).update({RefreshToken.revoked_at: now}, synchronize_session=False)


def get_refresh_token(
    db: Session,
    token_hash: str,
    user_id: str,
    session_id: str,
) -> RefreshToken | None:
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
            RefreshToken.session_id == session_id,
            RefreshToken.revoked_at.is_(None),
        )
        .first()
    )


def get_access_logs_paginated(
    db: Session, user_id: str, offset: int, limit: int
) -> tuple[int, Result[tuple[User, AccessLog]]]:
    query = (
        select(User, AccessLog)
        .join(AccessLog, AccessLog.user_id == User.id)
        .where(AccessLog.user_id == user_id)
    )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    logs = db.execute(
        query.order_by(AccessLog.login_at.desc()).offset(offset).limit(limit)
    )

    return total, logs


def create_user(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    db.refresh(user)

    return user


def close_session(db: Session, access_log: AccessLog, now: datetime) -> None:
    access_log.logout_at = now


def create_session_records(
    db: Session,
    access_log: AccessLog,
    refresh_token: RefreshToken,
) -> None:
    db.add(access_log)
    db.add(refresh_token)
    db.flush()


def create_refresh_token_record(db: Session, refresh_token: RefreshToken) -> None:
    db.add(refresh_token)
    db.flush()
