from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app import database, models


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


def test_get_db_retorna_sessao(monkeypatch):
    sessao_falsa = MagicMock()

    monkeypatch.setattr(database, "SessionLocal", lambda: sessao_falsa)

    gerador = database.get_db()
    sessao_recebida = next(gerador)

    assert sessao_recebida is sessao_falsa

    gerador.close()

    sessao_falsa.close.assert_called_once()


def test_get_db_fecha_sessao_apos_excecao(monkeypatch):
    sessao_falsa = MagicMock()

    monkeypatch.setattr(database, "SessionLocal", lambda: sessao_falsa)

    gerador = database.get_db()
    next(gerador)

    try:
        gerador.throw(ValueError("Erro Simulado"))
    except ValueError:
        pass

    sessao_falsa.close.asset_called_once()
