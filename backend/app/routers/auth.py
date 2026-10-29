from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..limiter import rate_limit
from ..models import AccessLog, User
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
    get_current_session,
    get_current_user_id,
)
from ..services.auth_service import login_user, logout_user, refresh_user, register_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
CurrentSession = Annotated[tuple[str, str], Depends(get_current_session)]


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@rate_limit("5/minute")
def register(request: Request, user_data: UserCreate, db: DbSession) -> UserResponse:
    return register_user(user_data, db)


@router.post("/login", response_model=Token)
@rate_limit("5/minute")
def login(request: Request, user_data: UserLogin, db: DbSession) -> Token:
    return login_user(user_data, db)


@router.get("/me", response_model=UserResponse)
def get_me(user_id: CurrentUserId, db: DbSession):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
        )

    return user


@router.post("/logout", response_model=MessageResponse)
def logout(session: CurrentSession, db: DbSession) -> MessageResponse:
    user_id, session_id = session
    return logout_user(user_id, session_id, db)


@router.post("/refresh", response_model=Token)
@rate_limit("5/minute")
def refresh_tokens(request: Request, data: RefreshRequest, db: DbSession) -> Token:
    return refresh_user(data, db)


@router.get("/logs", response_model=AccessLogPaginationResponse)
def get_access_logs(
    user_id: CurrentUserId,
    db: DbSession,
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

    query = (
        select(User, AccessLog)
        .join(AccessLog, AccessLog.user_id == User.id)
        .where(AccessLog.user_id == user_id)
    )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    offset = (page - 1) * limit

    logs = db.execute(
        query.order_by(AccessLog.login_at.desc()).offset(offset).limit(limit)
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
        items=items, page=page, limit=limit, total=total, pages=total_pages
    )
