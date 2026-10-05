import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models

TEST_DATABASE_URL = "sqlite:///./test_database.db"

test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db():
    Base.metadata.drop_all(bind=test_engine)

    Base.metadata.create_all(bind=test_engine)

    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def teste_database_session(db):
    assert db is not None


def teste_criar_usuario(db):
    usuario = models.User(
        name="Raphael", email="raphael@teste.com", password_hash="senha_hash"
    )

    db.add(usuario)
    db.commit()

    assert usuario.id is not None


def teste_buscar_usuario(db):

    usuario = models.User(
        name="Maria", email="maria@teste.com", password_hash="senha_hash"
    )

    db.add(usuario)
    db.commit()

    userEmail = db.query(models.User).filter(models.User.email == usuario.email).first()

    assert userEmail is not None
