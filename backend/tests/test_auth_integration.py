from unittest.mock import patch

import pytest
from app.main import app
from app.models import User
from app.security import get_current_session
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def test_rota_raiz(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Api no ar"}


def test_cadastrar_usuario(client: TestClient) -> None:

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Raphael",
            "email": "raphael@teste.com",
            "password": "senha123456",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Raphael"
    assert data["email"] == "raphael@teste.com"
    assert "id" in data
    assert "password_hash" not in data


def test_cadastrar_usuario_sem_nome(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "raphael@teste.com", "password": "Senha123456"},
    )

    assert response.status_code == 422


def test_cadastrar_usuario_sem_senha(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"name": "Raphael", "email": "raphael@teste.com"},
    )

    assert response.status_code == 422


def test_cadastrar_usuario_email_duplicado(client: TestClient) -> None:
    payload = {
        "name": "Raphael",
        "email": "raphael@teste.com",
        "password": "teste12345678",
    }

    primeira_resposta = client.post("/api/auth/register", json=payload)
    segunda_resposta = client.post("/api/auth/register", json=payload)

    assert primeira_resposta.status_code == 201
    assert segunda_resposta.status_code == 400


def test_cadastrar_usuario_com_email_invalido(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"name": "Raphael", "email": "email_invalido", "senha": "Senha123456"},
    )

    assert response.status_code == 422


def test_cadastrar_usuario_com_senha_curta(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Raphael",
            "email": "raphael@teste.com",
            "password": "123",
        },
    )

    assert response.status_code == 422


def test_cadastrar_usuario_sem_dados(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={},
    )

    assert response.status_code == 422


def test_login_sem_dados(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={},
    )

    assert response.status_code == 422


def test_login_sucesso(client: TestClient) -> None:
    cadastro = client.post(
        "/api/auth/register",
        json={
            "name": "Raphael",
            "email": "raphael@teste.com",
            "password": "senha123456",
        },
    )

    assert cadastro.status_code == 201

    response = client.post(
        "/api/auth/login",
        json={"email": "raphael@teste.com", "password": "senha123456"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_login_sem_senha(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={
            "email": "raphael@teste.com",
        },
    )

    assert response.status_code == 422


def test_login_senha_invalida(client: TestClient) -> None:
    dados_usuario = {
        "name": "Raphael",
        "email": "raphael@teste.com",
        "password": "senha123456",
    }

    cadastro = client.post("/api/auth/register", json=dados_usuario)

    assert cadastro.status_code == 201

    response = client.post(
        "/api/auth/login",
        json={
            "email": dados_usuario["email"],
            "password": "senha_errada123456",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou senha inválidos"


def test_login_email_invalido(client: TestClient) -> None:
    dados_usuario = {
        "name": "Raphael",
        "email": "raphael@teste.com",
        "password": "senha123456",
    }

    cadastro = client.post("/api/auth/register", json=dados_usuario)

    assert cadastro.status_code == 201

    response = client.post(
        "/api/auth/login",
        json={
            "email": "raphaelemailerrado@teste.com",
            "password": dados_usuario["password"],
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou senha inválidos."


def test_login_com_sessao_ativa(client: TestClient) -> None:
    dados_usuario = {
        "name": "Raphael",
        "email": "raphael@teste.com",
        "password": "senha123456",
    }

    cadastro = client.post("/api/auth/register", json=dados_usuario)

    assert cadastro.status_code == 201

    dados_login = {
        "email": dados_usuario["email"],
        "password": dados_usuario["password"],
    }

    primeiro_login = client.post("/api/auth/login", json=dados_login)

    assert primeiro_login.status_code == 200

    segundo_login = client.post("/api/auth/login", json=dados_login)

    assert segundo_login.status_code == 409
    assert segundo_login.json()["detail"] == ("Essa conta já está conectada")


def test_login_novamente_apos_logout(client: TestClient) -> None:
    payload = {"name": "Teste", "email": "relogin@email.com", "password": "Senha123!"}

    cadastro = client.post("/api/auth/register", json=payload)

    assert cadastro.status_code == 201

    credenciais = {
        "email": payload["email"],
        "password": payload["password"],
    }

    primeiro_login = client.post("/api/auth/login", json=credenciais)
    assert primeiro_login.status_code == 200

    token = primeiro_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200

    segundo_login = client.post("/api/auth/login", json=credenciais)
    assert segundo_login.status_code == 200
    assert "access_token" in segundo_login.json()
    assert segundo_login.json()["token_type"] == "bearer"


def test_login_email_inexistente(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={
            "email": "naoexiste@teste.com",
            "password": "senha123456",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou senha inválidos."


def test_login_sem_email(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"password": "Senha123456"},
    )

    assert response.status_code == 422


def test_login_com_erro_ao_salvar_sessao(client: TestClient) -> None:
    payload = {
        "name": "Raphael",
        "email": "raphael@email.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)

    assert cadastro.status_code == 201

    dados_login = {"email": payload["email"], "password": payload["password"]}

    with patch("app.routers.auth.Session.commit") as mock_commit:
        mock_commit.side_effect = [
            None,
            IntegrityError("INSERT", {}, Exception("Erro Simulado")),
        ]

        response = client.post("/api/auth/login", json=dados_login)

    assert response.status_code == 409
    assert response.json()["detail"] == "Essa conta já está conectada"


def test_logout_sucesso(client: TestClient) -> None:
    payload = {
        "name": "Teste",
        "email": "logout@email.com",
        "password": "Senha123!",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    logout = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert logout.status_code == 200
    assert logout.json()["message"] == "Logout realizado com sucesso"


def test_logout_sem_token(client: TestClient) -> None:
    response = client.post("/api/auth/logout")

    assert response.status_code == 401


def test_logout_com_token_malformado(client: TestClient) -> None:
    response = client.post(
        "/api/auth/logout",
        headers={
            "Authorization": "Bearer token_invalido",
        },
    )

    assert response.status_code == 401


def test_logout_sem_sessao_ativa(client: TestClient) -> None:
    def override_get_current_session():
        return ("usuario-inexistente", "sessao-inexistente")

    app.dependency_overrides[get_current_session] = override_get_current_session

    try:
        response = client.post("/api/auth/logout")
    finally:
        app.dependency_overrides.pop(get_current_session, None)

    assert response.status_code == 404
    assert response.json()["detail"] == "Nenhuma sessão ativa encontrada"


def test_token_invalido_apos_logout(client: TestClient) -> None:
    payload = {
        "name": "Teste",
        "email": "token.logout@email.com",
        "password": "Senha123!",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200

    dados_login = login.json()
    access_token = dados_login["access_token"]
    refresh_token = dados_login["refresh_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200

    resposta = client.post("/api/auth/logout", headers=headers)
    assert resposta.status_code == 401

    resposta_refresh = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert resposta_refresh.status_code == 401


def test_buscar_proprio_usuario(client: TestClient) -> None:
    payload = {"name": "Raphael", "email": "me@teste.com", "password": "Senha123456"}

    cadastro = client.post("/api/auth/register", json=payload)

    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert "id" in data
    assert "password_hash" not in data


def test_buscar_proprio_usuario_sem_token(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_buscar_proprio_usuario_com_token_invalido(client: TestClient) -> None:
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer token_invalido"}
    )

    assert response.status_code == 401


def test_buscar_proprio_usuario_apos_logout(client: TestClient) -> None:
    payload = {
        "name": "Raphael",
        "email": "raphael@email.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)

    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )

    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout = client.post("/api/auth/logout", headers=headers)

    assert logout.status_code == 200

    response = client.get("/api/auth/me", headers=headers)

    assert response.status_code == 401


def test_buscar_proprio_usuario_nao_encontrado(client: TestClient, db: Session) -> None:
    payload = {
        "name": "Raphael",
        "email": "raphael@teste.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    dados_login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert dados_login.status_code == 200

    token = dados_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    usuario = db.query(User).filter(User.email == payload["email"]).first()

    assert usuario is not None

    db.delete(usuario)
    db.commit()

    response = client.get("/api/auth/me", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado."


def test_buscar_logs_sem_token(client: TestClient) -> None:
    response = client.get("/api/auth/logs")

    assert response.status_code == 401


def test_buscar_logs_com_token_invalido(client: TestClient) -> None:
    response = client.get(
        "/api/auth/logs",
        headers={"Authorization": "Bearer token_invalido"},
    )

    assert response.status_code == 401


def test_buscar_logs_com_pagina_invalida(client: TestClient) -> None:
    payload = {
        "name": "Raphael",
        "email": "raphael@email.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)

    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/logs?page=0", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "A página deve ser maior ou igual a 1."


def test_buscar_logs_com_limite_minimo(client: TestClient) -> None:
    payload = {
        "name": "Teste Limite Minimo",
        "email": "limite.minimo@teste.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )
    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.get(
        "/api/auth/logs?limit=1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["limit"] == 1
    assert len(data["items"]) <= 1
    assert data["total"] >= 1


def test_buscar_logs_com_limite_maximo(client: TestClient) -> None:
    payload = {
        "name": "Teste Limite Maximo",
        "email": "testelimitemaximo@teste.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )
    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/logs?limit=100", headers=headers)

    assert response.status_code == 200

    data = response.json()

    assert data["limit"] == 100
    assert len(data["items"]) <= 100


def test_buscar_logs_com_limite_invalido(client: TestClient) -> None:
    payload = {
        "name": "Raphael",
        "email": "raphael@email.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)

    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/logs?limit=0", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == ("O limite deve estar entre 1 e 100.")


def test_buscar_logs_com_limite_acima_do_maximo(client: TestClient) -> None:
    payload = {
        "name": "Raphael",
        "email": "raphael@email.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)

    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/logs?limit=101", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == ("O limite deve estar entre 1 e 100.")


def test_buscar_logs_com_limite_negativo(client: TestClient) -> None:
    payload = {
        "name": "Teste Limite Negativo",
        "email": "teste@email.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/logs?limit=-1", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == ("O limite deve estar entre 1 e 100.")


def test_buscar_logs_sucesso(client: TestClient) -> None:
    payload = {
        "name": "Raphael",
        "email": "raphael@email.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)

    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/logs", headers=headers)

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert data["page"] == 1
    assert data["limit"] == 10
    assert data["total"] >= 1
    assert data["pages"] >= 1

    log = data["items"][0]

    assert log["name"] == payload["name"]
    assert log["email"] == payload["email"]
    assert "login_at" in log
    assert "logout_at" in log


def test_buscar_logs_paginacao(client: TestClient) -> None:
    payload = {
        "name": "Teste Paginacao",
        "email": "paginacao@teste.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    credenciais = {"email": payload["email"], "password": payload["password"]}

    for _ in range(3):
        login = client.post("/api/auth/login", json=credenciais)

        assert login.status_code == 200

        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        logout = client.post("/api/auth/logout", headers=headers)

        assert logout.status_code == 200

    login = client.post("/api/auth/login", json=credenciais)

    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/logs?page=2&limit=2", headers=headers)

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["limit"] == 2
    assert data["total"] == 4
    assert data["pages"] == 2
    assert len(data["items"]) == 2


def test_buscar_logs_pagina_sem_registro(client: TestClient) -> None:
    payload = {
        "name": "Teste Pagina Vazia",
        "email": "pagina.vazia@teste.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )
    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/logs?page=99&limit=10", headers=headers)

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["page"] == 99
    assert data["limit"] == 10
    assert data["total"] >= 1
    assert data["pages"] >= 1


def test_buscar_logs_sem_registro(client: TestClient) -> None:
    payload = {
        "name": "Usuario Sem Logs",
        "email": "sem.logs@teste.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )
    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/logs?page=99&limit=10", headers=headers)

    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["page"] == 99
    assert data["limit"] == 10


def test_buscar_logs_ordenados_por_login_mais_recente(client: TestClient) -> None:
    payload = {
        "name": "Teste ordenacao",
        "email": "ordenacao@teste.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)

    assert cadastro.status_code == 201

    credenciais = {"email": payload["email"], "password": payload["password"]}

    for _ in range(2):
        login = client.post("/api/auth/login", json=credenciais)

        assert login.status_code == 200

        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        logout = client.post("/api/auth/logout", headers=headers)

        assert logout.status_code == 200

    login = client.post("/api/auth/login", json=credenciais)

    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/logs?limit=10", headers=headers)

    assert response.status_code == 200

    logs = response.json()["items"]

    assert len(logs) == 3

    datas = [log["login_at"] for log in logs]

    assert datas == sorted(datas, reverse=True)


def test_buscar_logs_de_multiplos_usuarios(client: TestClient) -> None:
    usuario1 = {
        "name": "Usuario 1",
        "email": "usuario1@teste.com",
        "password": "usuario1senha",
    }

    usuario2 = {
        "name": "Usuario 2",
        "email": "usuario2@teste.com",
        "password": "usuario2senha",
    }

    cadastro1 = client.post("/api/auth/register", json=usuario1)
    assert cadastro1.status_code == 201

    cadastro2 = client.post("/api/auth/register", json=usuario2)
    assert cadastro2.status_code == 201

    login1 = client.post(
        "/api/auth/login",
        json={
            "email": usuario1["email"],
            "password": usuario1["password"],
        },
    )
    assert login1.status_code == 200
    token = login1.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    login2 = client.post(
        "/api/auth/login",
        json={
            "email": usuario2["email"],
            "password": usuario2["password"],
        },
    )
    assert login2.status_code == 200

    response = client.get("/api/auth/logs", headers=headers)
    assert response.status_code == 200

    data = response.json()
    emails = [log["email"] for log in data["items"]]

    assert usuario1["email"] in emails
    assert usuario2["email"] in emails


def test_buscar_logs_com_pagina_negativa(client: TestClient) -> None:
    payload = {
        "name": "Teste pagina negativa",
        "email": "paginanegativa@teste.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/logs?page=-1", headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "A página deve ser maior ou igual a 1."


def test_buscar_logs_calculo_total_paginas(client: TestClient) -> None:
    payload = {
        "name": "Teste Total Paginas",
        "email": "total.paginas@teste.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    credenciais = {
        "email": payload["email"],
        "password": payload["password"],
    }

    for _ in range(5):
        login = client.post("/api/auth/login", json=credenciais)
        assert login.status_code == 200

        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        logout = client.post(
            "/api/auth/logout",
            headers=headers,
        )
        assert logout.status_code == 200

    login = client.post("/api/auth/login", json=credenciais)
    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.get(
        "/api/auth/logs?limit=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 6
    assert data["limit"] == 2
    assert data["pages"] == 3
    assert len(data["items"]) == 2


def test_buscar_logs_ultima_pagina(client: TestClient) -> None:
    payload = {
        "name": "Teste Ultima Pagina",
        "email": "ultima.pagina@teste.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    credenciais = {
        "email": payload["email"],
        "password": payload["password"],
    }

    for _ in range(3):
        login = client.post("/api/auth/login", json=credenciais)
        assert login.status_code == 200

        token = login.json()["access_token"]

        logout = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout.status_code == 200

    login = client.post("/api/auth/login", json=credenciais)
    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        "/api/auth/logs?page=2&limit=2",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["limit"] == 2
    assert data["total"] == 4
    assert data["pages"] == 2
    assert len(data["items"]) == 2


def test_buscar_logs_retorna_apenas_registros_do_limite(client: TestClient) -> None:
    payload = {
        "name": "Teste Limite de Registros",
        "email": "limite.registros@teste.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    credenciais = {
        "email": payload["email"],
        "password": payload["password"],
    }

    for _ in range(4):
        login = client.post("/api/auth/login", json=credenciais)
        assert login.status_code == 200

        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        logout = client.post(
            "/api/auth/logout",
            headers=headers,
        )
        assert logout.status_code == 200

    login = client.post("/api/auth/login", json=credenciais)
    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        "/api/auth/logs?limit=2",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["limit"] == 2
    assert data["total"] == 5
    assert len(data["items"]) == 2


def test_buscar_logs_total_consistente_entre_paginas(client: TestClient) -> None:
    payload = {
        "name": "Teste Total Consistente",
        "email": "total.consistente@teste.com",
        "password": "Senha123456",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    credenciais = {
        "email": payload["email"],
        "password": payload["password"],
    }

    for _ in range(5):
        login = client.post("/api/auth/login", json=credenciais)
        assert login.status_code == 200

        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        logout = client.post(
            "/api/auth/logout",
            headers=headers,
        )
        assert logout.status_code == 200

    login = client.post("/api/auth/login", json=credenciais)
    assert login.status_code == 200
    token = login.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    pagina1 = client.get(
        "/api/auth/logs?page=1&limit=2",
        headers=headers,
    )
    assert pagina1.status_code == 200

    pagina2 = client.get(
        "/api/auth/logs?page=2&limit=2",
        headers=headers,
    )
    assert pagina2.status_code == 200

    pagina3 = client.get(
        "/api/auth/logs?page=3&limit=2",
        headers=headers,
    )
    assert pagina3.status_code == 200

    dados1 = pagina1.json()
    dados2 = pagina2.json()
    dados3 = pagina3.json()

    assert dados1["total"] == 6
    assert dados2["total"] == 6
    assert dados3["total"] == 6

    assert len(dados1["items"]) == 2
    assert len(dados2["items"]) == 2
    assert len(dados3["items"]) == 2


def test_refresh_token_sucesso(client: TestClient) -> None:
    payload = {
        "name": "Raphael",
        "email": "raphael@raphael.com",
        "password": "Raphael123",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200

    refresh_token_original = login.json()["refresh_token"]

    response = client.post(
        "/api/auth/refresh", json={"refresh_token": refresh_token_original}
    )

    print("STATUS:", response.status_code)
    print("RESPOSTA:", response.text)

    assert response.status_code == 200

    dados = response.json()

    assert "access_token" in dados
    assert "refresh_token" in dados
    assert dados["token_type"] == "bearer"
    assert dados["access_token"] != login.json()["access_token"]
    assert dados["refresh_token"] != refresh_token_original


def test_refresh_token_reutilizado_apos_rotacao(client: TestClient) -> None:
    payload = {
        "name": "raphael testudo",
        "email": "raphael@raphael.com",
        "password": "Raphael123",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200

    refresh_token_original = login.json()["refresh_token"]

    primeira_renovacao = client.post(
        "/api/auth/refresh",
        json={
            "refresh_token": refresh_token_original,
        },
    )
    assert primeira_renovacao.status_code == 200

    dados_renovados = primeira_renovacao.json()
    novo_refresh_token = dados_renovados["refresh_token"]

    assert novo_refresh_token != refresh_token_original

    segunda_renovacao = client.post(
        "/api/auth/refresh", json={"refresh_token": refresh_token_original}
    )
    assert segunda_renovacao.status_code == 401

    terceira_renovacao = client.post(
        "/api/auth/refresh", json={"refresh_token": novo_refresh_token}
    )
    assert terceira_renovacao.status_code == 200


def test_refresh_token_invalido(client: TestClient) -> None:
    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": "token_invalido"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token inválido ou expirado"


def test_refresh_token_com_assinatura_invalida(client: TestClient) -> None:
    payload = {
        "name": "Raphao gostosao",
        "email": "raphao@gostosao.com",
        "password": "Gostosa123",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200

    refresh_token = login.json()["refresh_token"]

    partes = refresh_token.split(".")
    assinatura = partes[2]
    caractere = "A" if assinatura[0] != "A" else "B"
    partes[2] = caractere + assinatura[1:]
    token_adulterado = ".".join(partes)

    response = client.post(
        "/api/auth/refresh", json={"refresh_token": token_adulterado}
    )
    assert response.status_code == 401


def test_refresh_token_expirado(client: TestClient) -> None:
    payload = {
        "name": "Teste",
        "email": "refresh.expirado@email.com",
        "password": "Senha123!",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )
    assert login.status_code == 200

    refresh_token = login.json()["refresh_token"]

    with patch("app.routers.auth.decode_refresh_token") as mock_decode:
        mock_decode.side_effect = ValueError("Refresh token inválido ou expirado")

        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token inválido ou expirado"


def test_decode_refresh_token_expirado() -> None:
    from datetime import timedelta

    from app.security import create_refresh_token, decode_refresh_token

    token = create_refresh_token(
        data={
            "sub": "usuario-teste",
            "session_id": "sessao-teste",
        },
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(ValueError, match="Refresh token inválido ou expirado"):
        decode_refresh_token(token)


def test_refresh_token_com_access_token(client: TestClient) -> None:
    payload = {
        "name": "Teste",
        "email": "refresh.access@email.com",
        "password": "Senha123!",
    }

    cadastro = client.post("/api/auth/register", json=payload)
    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )
    assert login.status_code == 200

    access_token = login.json()["access_token"]

    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token inválido ou expirado"


def test_refresh_token_de_outro_usuario(client: TestClient) -> None:
    usuario_a = {
        "name": "Usuario A",
        "email": "usuario.a@email.com",
        "password": "Senha123!",
    }
    usuario_b = {
        "name": "Usuario B",
        "email": "usuario.b@email.com",
        "password": "Senha123!",
    }

    cadastro_a = client.post("/api/auth/register", json=usuario_a)
    cadastro_b = client.post("/api/auth/register", json=usuario_b)

    assert cadastro_a.status_code == 201
    assert cadastro_b.status_code == 201

    login_a = client.post(
        "/api/auth/login",
        json={
            "email": usuario_a["email"],
            "password": usuario_a["password"],
        },
    )
    login_b = client.post(
        "/api/auth/login",
        json={
            "email": usuario_b["email"],
            "password": usuario_b["password"],
        },
    )

    assert login_a.status_code == 200
    assert login_b.status_code == 200

    refresh_token_a = login_a.json()["refresh_token"]

    response = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token_a},
    )

    assert response.status_code == 200

    dados = response.json()
    assert "access_token" in dados
    assert "refresh_token" in dados
    assert dados["refresh_token"] != refresh_token_a
