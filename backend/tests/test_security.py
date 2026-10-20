import importlib
import sys
from datetime import UTC, datetime, timedelta

import pytest
from app.security import ALGORITHM, SECRET_KEY, create_access_token, decode_access_token
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
