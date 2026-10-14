from sqlalchemy.orm import Session
from app import models


def test_database_session(db: Session):
    assert db is not None


def test_criar_usuario(db: Session):
    usuario = models.User(
        name="Raphael",
        email="raphael@teste.com",
        password_hash="senha_hash",
    )

    db.add(usuario)
    db.commit()

    assert usuario.id is not None


def test_buscar_usuario(db: Session):
    usuario = models.User(
        name="Maria",
        email="maria@teste.com",
        password_hash="senha_hash",
    )

    db.add(usuario)
    db.commit()

    user_email = (
        db.query(models.User).filter(models.User.email == usuario.email).first()
    )

    assert user_email is not None

    email_encontrado: str = user_email.email
    assert email_encontrado == "maria@teste.com"
