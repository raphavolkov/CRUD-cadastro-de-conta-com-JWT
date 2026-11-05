from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.limiter import limiter
from app.main import app


@pytest.fixture
def db() -> Generator[Session]:
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    test_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    try:
        Base.metadata.create_all(bind=test_engine)
        session = test_session_local()

        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)
    finally:
        test_engine.dispose()


@pytest.fixture
def client(db: Session) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        yield db

    previous_get_db_override = app.dependency_overrides.get(get_db)
    limiter_enabled_original = limiter.enabled

    app.dependency_overrides[get_db] = override_get_db
    limiter.enabled = False

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if previous_get_db_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_get_db_override

        limiter.enabled = limiter_enabled_original
