import importlib
import sys
from datetime import UTC, datetime, timedelta

import pytest
from app.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from jose import jwt


def test_security_falha_sem_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", "")

    sys.modules.pop("app.security", None)

    with pytest.raises(
        RuntimeError,
        match="SECRET_KEY não configurada",
    ):
        importlib.import_module("app.security")


def test_criar_token_com_validade_personalizada():
    validade = timedelta(minutes=5)

    token = create_access_token(
        data={"sub": "123", "session_id": "abc"}, expires_delta=validade
    )

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    expiracao = datetime.fromtimestamp(
        payload["exp"],
        tz=UTC,
    )

    agora = datetime.now(UTC)

    assert expiracao > agora
    assert expiracao <= agora + validade
    assert payload["sub"] == "123"
    assert payload["session_id"] == "abc"


def test_create_refresh_token():
    token = create_refresh_token(
        data={"sub": "usuario-teste", "session_id": "sessao-teste"}
    )

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert payload["sub"] == "usuario-teste"
    assert payload["session_id"] == "sessao-teste"
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_token_sem_sub():
    token = jwt.encode(
        {"session_id": "abc"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(ValueError, match="Token inválido ou expirado"):
        decode_access_token(token)


def test_decode_token_sem_session_id():
    token = jwt.encode(
        {"sub": "123"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(ValueError, match="Token inválido ou expirado."):
        decode_access_token(token)


def test_decode_access_token_rejeita_refresh_token():
    token = create_refresh_token(
        data={"sub": "usuario-teste", "session_id": "sessao-teste"}
    )

    with pytest.raises(ValueError, match="Token inválido ou expirado"):
        decode_access_token(token)


def test_decode_access_token_com_tipo_incorreto() -> None:
    token = jwt.encode(
        {
            "sub": "usuario-teste",
            "session_id": "sessao-teste",
            "type": "outro",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(
        ValueError,
        match="Token inv",
    ):
        decode_access_token(token)


def test_decode_refresh_token_sem_sub():
    token = jwt.encode(
        {
            "session_id": "sessao-teste",
            "type": "refresh",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    from app.security import decode_refresh_token

    with pytest.raises(ValueError, match="Refresh token"):
        decode_refresh_token(token)


def test_decode_refresh_token_sem_session_id():
    token = jwt.encode(
        {
            "sub": "usuario-teste",
            "type": "refresh",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    from app.security import decode_refresh_token

    with pytest.raises(ValueError, match="Refresh token"):
        decode_refresh_token(token)


def test_decode_access_token_com_session_id_invalido():
    token = jwt.encode(
        {
            "sub": "usuario-teste",
            "session_id": 123,
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with pytest.raises(ValueError, match="Token inv"):
        decode_access_token(token)
