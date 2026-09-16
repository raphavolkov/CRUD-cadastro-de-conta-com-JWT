from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..models import User, AccessLog
from ..schemas import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    MessageResponse,
    AccessLogResponse,
)
from ..security import (
    create_access_token,
    get_current_user_id,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
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
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos."
        )

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos"
        )

    access_token = create_access_token(data={"sub": user.id})

    access_log = AccessLog(user_id=user.id)

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
def logout(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    access_log = (
        db.query(AccessLog)
        .filter(AccessLog.user_id == user_id, AccessLog.logout_at.is_(None))
        .order_by(AccessLog.login_at.desc())
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


@router.get("/logs", response_model=list[AccessLogResponse])
def get_access_logs(
    user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    logs = (
        db.query(User.name, User.email, AccessLog.login_at, AccessLog.logout_at)
        .join(AccessLog, AccessLog.user_id == User.id)
        .order_by(AccessLog.login_at.desc())
        .all()
    )

    return logs
