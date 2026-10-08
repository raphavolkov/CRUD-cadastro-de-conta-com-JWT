import pytest


from datetime import datetime
from app.models import User
from app.schemas import UserCreate, UserLogin, UserResponse


def test_user_create_valido():
    usuario = UserCreate(name="Raphael", email="raphael@email.com", password="12345678")

    assert usuario.name == "Raphael"
    assert usuario.email == "raphael@email.com"
    assert usuario.password == "12345678"


def test_user_create_senha_curta():
    with pytest.raises(ValueError):
        UserCreate(name="Raphael", email="raphael@email.com", password="1234567")


def test_user_create_email_invalido():
    with pytest.raises(ValueError):
        UserCreate(name="Raphael", email="raphaeldemais", password="12345678")


def test_user_create_sem_nome():
    with pytest.raises(ValueError):
        UserCreate(email="raphael@teste.com", password="12345678")


def test_user_login_valido():
    usuario = UserLogin(email="raphael@email.com", password="12345678")

    assert usuario.email == "raphael@email.com"
    assert usuario.password == "12345678"


def test_user_login_email_invalido():
    with pytest.raises(ValueError):
        UserLogin(email="raphaelemailerrado", password="12345678")


def test_user_login_senha_curta():
    with pytest.raises(ValueError):
        UserLogin(email="raphael@email.com", password="1234567")


def test_user_login_email_ausente():
    with pytest.raises(ValueError):
        UserLogin(password="12345678")


def test_user_login_senha_ausente():
    with pytest.raises(ValueError):
        UserLogin(email="raphael@email.com")


def test_user_response_valido():
    usuario = User(
        id="123",
        name="Raphael",
        email="raphael@teste.com",
        password_hash="hash-da-senha",
        created_at=datetime(2026, 10, 8, 10, 30),
    )

    resposta = UserResponse.model_validate(usuario)

    assert resposta.id == "123"
    assert resposta.name == "Raphael"
    assert resposta.email == "raphael@teste.com"
    assert resposta.created_at == datetime(2026, 10, 8, 10, 30)


def test_user_response_nao_expoe_senha():
    usuario = User(
        id="123",
        name="Raphael",
        email="raphael@teste.com",
        password_hash="senha-super-secreta",
        created_at=datetime(2026, 10, 8, 10, 30),
    )

    resposta = UserResponse.model_validate(usuario)

    assert not hasattr(resposta, "password_hash")


def test_user_response_email_ausente():
    with pytest.raises(ValueError):
        UserResponse(
            id="123",
            name="Raphael",
            created_at=datetime(2026, 10, 8, 10, 30),
        )
