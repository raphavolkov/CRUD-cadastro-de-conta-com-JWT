import pytest


from datetime import datetime
from app.models import User
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    MessageResponse,
    AccessLogResponse,
    AccessLogPaginationResponse,
)


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


def test_token_valido():
    token = Token(
        access_token="meu-token-123",
        token_type="bearer",
    )

    assert token.access_token == "meu-token-123"
    assert token.token_type == "bearer"


def test_token_access_token_ausente():
    with pytest.raises(ValueError):
        Token(token_type="bearer")


def test_token_token_type_ausente():
    with pytest.raises(ValueError):
        Token(access_token="meu-token-123")


def test_message_response_valido():
    resposta = MessageResponse(message="Usuario criado com sucesso")

    assert resposta.message == "Usuario criado com sucesso"


def test_message_response_messagem_ausente():
    with pytest.raises(ValueError):
        MessageResponse()


def test_access_log_response_valido():
    resposta = AccessLogResponse(
        name="Raphael",
        email="raphael@email.com",
        login_at=datetime(2026, 10, 8, 10, 30),
        logout_at=datetime(2026, 10, 8, 11, 30),
    )

    assert resposta.name == "Raphael"
    assert resposta.email == "raphael@email.com"
    assert resposta.login_at == datetime(2026, 10, 8, 10, 30)
    assert resposta.logout_at == datetime(2026, 10, 8, 11, 30)


def test_access_log_respose_valido_sem_logout():
    resposta = AccessLogResponse(
        name="Raphael",
        email="raphael@email.com",
        login_at=datetime(2026, 10, 8, 10, 30),
        logout_at=None,
    )

    assert resposta.logout_at is None


def test_access_log_pagination_response_valido():
    resposta = AccessLogPaginationResponse(
        items=[
            AccessLogResponse(
                name="Raphael",
                email="raphael@teste.com",
                login_at=datetime(2026, 10, 8, 10, 30),
                logout_at=datetime(2026, 10, 8, 11, 30),
            )
        ],
        page=1,
        limit=10,
        total=1,
        pages=1,
    )

    assert resposta.items[0].name == "Raphael"
    assert resposta.items[0].email == "raphael@teste.com"
    assert resposta.items[0].login_at == datetime(2026, 10, 8, 10, 30)
    assert resposta.items[0].logout_at == datetime(2026, 10, 8, 11, 30)

    assert resposta.page == 1
    assert resposta.limit == 10
    assert resposta.total == 1
    assert resposta.pages == 1


def test_access_log_pagination_response_valido_lista_vazia():
    resposta = AccessLogPaginationResponse(
        items=[],
        page=1,
        limit=10,
        total=0,
        pages=0,
    )

    assert resposta.items == []

    assert resposta.page == 1
    assert resposta.limit == 10
    assert resposta.total == 0
    assert resposta.pages == 0


def test_access_log_pagination_response_pages_ausente():
    with pytest.raises(ValueError):
        AccessLogPaginationResponse(
            items=[],
            page=1,
            limit=10,
            total=1,
        )


def test_access_log_pagination_response_dado_errado():
    with pytest.raises(ValueError):
        AccessLogPaginationResponse(
            items=[
                AccessLogResponse(
                    name="Raphael",
                    email="raphaeldoemailerrado",
                    login_at=datetime(2026, 10, 8, 10, 30),
                    logout_at=datetime(2026, 10, 8, 11, 30),
                )
            ],
            page=1,
            limit=10,
            total=1,
            pages=1,
        )
