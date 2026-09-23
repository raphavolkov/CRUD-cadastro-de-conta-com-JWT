import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..limiter import limiter
from ..database import get_db
from ..models import User, AccessLog
from ..schemas import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    MessageResponse,
    AccessLogResponse,
    AccessLogPaginationResponse,
)
from ..security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_session,
    get_current_user_id,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado"
        )

    hashed_password = hash_password(user_data.password)

    new_user = User(
        name=user_data.name, email=user_data.email, password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos."
        )

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos"
        )

    now = datetime.utcnow()

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
            status_code=status.HTTP_409_CONFLICT, detail="Essa conta já está conectada"
        )

    session_id = str(uuid.uuid4())

    expires_at = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={
            "sub": user.id,
            "session_id": session_id,
        }
    )

    access_log = AccessLog(
        id=session_id, session_id=session_id, user_id=user.id, expires_at=expires_at
    )

    db.add(access_log)
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
        )

    return user


@router.post("/logout", response_model=MessageResponse)
def logout(
    session: tuple[str, str] = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    user_id, session_id = session

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

    access_log.logout_at = datetime.utcnow()

    db.commit()

    return {"message": "Logout realizado com sucesso"}


@router.get("/logs", response_model=AccessLogPaginationResponse)
def get_access_logs(
    page: int = 1,
    limit: int = 10,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
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

    query = db.query(
        User.name, User.email, AccessLog.login_at, AccessLog.logout_at
    ).join(AccessLog, AccessLog.user_id == User.id)

    total = query.count()

    offset = (page - 1) * limit

    logs = query.order_by(AccessLog.login_at.desc()).offset(offset).limit(limit).all()

    total_pages = (total + limit - 1) // limit

    return {
        "items": logs,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": total_pages,
    }
