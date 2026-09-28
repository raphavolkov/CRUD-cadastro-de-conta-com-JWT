import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Index, text
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), nullable=True)
    user_id = Column(String(36), nullable=False)
    login_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    logout_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ux_access_logs_session_id", "session_id", unique=True),
        Index(
            "ux_access_logs_one_active_session_per_user",
            "user_id",
            unique=True,
            sqlite_where=text("logout_at IS NULL"),
        ),
    )
