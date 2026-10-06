import pytest

from app.schemas import UserCreate, UserLogin


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
