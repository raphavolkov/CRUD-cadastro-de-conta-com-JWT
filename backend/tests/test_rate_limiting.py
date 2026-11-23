from fastapi.testclient import TestClient

from app.limiter import limiter


def test_login_bloqueia_apos_cinco_requisicoes(client: TestClient) -> None:
    limiter_enabled_original = limiter.enabled
    limiter.reset()
    limiter.enabled = True

    try:
        respostas = [
            client.post(
                "/api/auth/login",
                json={"email": "inexistente@teste.com", "password": "senha123456"},
            )
            for _ in range(6)
        ]

        assert all(resposta.status_code == 401 for resposta in respostas[:5])
        assert respostas[5].status_code == 429

    finally:
        limiter.enabled = limiter_enabled_original
        limiter.reset()


def test_register_bloqueia_apos_cinco_requisicoes(client: TestClient) -> None:
    limiter_enabled_original = limiter.enabled
    limiter.reset()
    limiter.enabled = True

    try:
        respostas = [
            client.post(
                "/api/auth/register",
                json={
                    "name": "Teste",
                    "email": f"teste{i}@exemplo.com",
                    "password": "senha123456",
                },
            )
            for i in range(6)
        ]

        assert all(resposta.status_code == 201 for resposta in respostas[:5])
        assert respostas[5].status_code == 429

    finally:
        limiter.enabled = limiter_enabled_original
        limiter.reset()


def test_refresh_bloqueia_apos_cinco_requisicoes(client: TestClient) -> None:
    limiter_enabled_original = limiter.enabled
    limiter.reset()
    limiter.enabled = True

    try:
        respostas = [
            client.post(
                "/api/auth/refresh",
                json={"refresh_token": "token-invalido"},
            )
            for _ in range(6)
        ]

        assert all(resposta.status_code == 401 for resposta in respostas[:5])
        assert respostas[5].status_code == 429

    finally:
        limiter.enabled = limiter_enabled_original
        limiter.reset()
