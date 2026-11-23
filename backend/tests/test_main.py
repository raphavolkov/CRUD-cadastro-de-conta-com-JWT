import pytest


def test_rate_limit_handler_repassa_excecao_desconhecida() -> None:
    from starlette.requests import Request

    from app.main import rate_limit_exceeded_handler

    request = Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
    )
    erro = RuntimeError("erro inesperado")

    with pytest.raises(RuntimeError, match="erro inesperado"):
        rate_limit_exceeded_handler(request, erro)
