from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..limiter import rate_limit
from ..schemas import (
    AccessLogPaginationResponse,
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
from ..services.auth_service import (
    get_access_logs as get_access_logs_service,
)
from ..services.auth_service import (
    get_user_by_id,
    login_user,
    logout_user,
    refresh_user,
    register_user,
)

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
    return get_user_by_id(user_id, db)


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
    return get_access_logs_service(user_id, db, page, limit)
