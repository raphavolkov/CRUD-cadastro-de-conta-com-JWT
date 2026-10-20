import sys
import importlib
import pytest

from datetime import datetime, timedelta, timezone
from jose import jwt
from app.security import SECRET_KEY, ALGORITHM, create_access_token, decode_access_token


def test_security_falha_sem_secret_key(monkeypatch):
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
        tz=timezone.utc,
    )

    agora = datetime.now(timezone.utc)

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
