def test_rota_raiz(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Api no ar"}


def test_cadastrar_usuario(client):

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


def test_cadastrar_usuario_sem_nome(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "raphael@teste.com", "password": "Senha123456"},
    )

    assert response.status_code == 422


def test_cadastrar_usuario_sem_senha(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Raphael", "email": "raphael@teste.com"},
    )

    assert response.status_code == 422


def test_cadastrar_usuario_email_duplicado(client):
    payload = {
        "name": "Raphael",
        "email": "raphael@teste.com",
        "password": "teste12345678",
    }

    primeira_resposta = client.post("/api/auth/register", json=payload)
    segunda_resposta = client.post("/api/auth/register", json=payload)

    assert primeira_resposta.status_code == 201
    assert segunda_resposta.status_code == 400


def test_cadastrar_usuario_com_email_invalido(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Raphael", "email": "email_invalido", "senha": "Senha123456"},
    )

    assert response.status_code == 422


def test_cadastrar_usuario_com_senha_curta(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Raphael",
            "email": "raphael@teste.com",
            "password": "123",
        },
    )

    assert response.status_code == 422


def test_cadastrar_usuario_sem_dados(client):
    response = client.post(
        "/api/auth/register",
        json={},
    )

    assert response.status_code == 422


def test_login_sem_dados(client):
    response = client.post(
        "/api/auth/login",
        json={},
    )

    assert response.status_code == 422


def test_login_sucesso(client):
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


def test_login_sem_senha(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "raphael@teste.com",
        },
    )

    assert response.status_code == 422


def test_login_senha_invalida(client):
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


def test_login_email_invalido(client):
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


def test_login_com_sessao_ativa(client):
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

    primeiro_login = client.post("/api/auth/login", json=dados_usuario)

    assert primeiro_login.status_code == 200

    segundo_login = client.post("/api/auth/login", json=dados_usuario)

    assert segundo_login.status_code == 409
    assert segundo_login.json()["detail"] == ("Essa conta já está conectada")


def test_login_novamente_apos_logout(client):
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


def test_login_email_inexistente(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "naoexiste@teste.com",
            "password": "senha123456",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou senha inválidos."


def test_login_sem_email(client):
    response = client.post(
        "/api/auth/login",
        json={"password": "Senha123456"},
    )

    assert response.status_code == 422


def test_logout_sucesso(client):
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


def test_logout_sem_token(client):
    response = client.post("/api/auth/logout")

    assert response.status_code == 401


def test_logout_com_token_malformado(client):
    response = client.post(
        "/api/auth/logout",
        headers={
            "Authorization": "Bearer token_invalido",
        },
    )

    assert response.status_code == 401


def test_token_invalido_apos_logout(client):
    payload = {
        "name": "Teste",
        "email": "token.logout@email.com",
        "password": "Senha123!",
    }

    cadastro = client.post("/api/auth/register", json=payload)

    assert cadastro.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={"email": "token.logout@email.com", "password": "Senha123!"},
    )

    assert login.status_code == 200

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout = client.post("/api/auth/logout", headers=headers)

    assert logout.status_code == 200

    resposta = client.post("/api/auth/logout", headers=headers)

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "Token inválido ou sessão encerrada."


def test_buscar_proprio_usuario(client):
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


def test_buscar_proprio_usuario_sem_token(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_buscar_proprio_usuario_com_token_invalido(client):
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer token_invalido"}
    )

    assert response.status_code == 401


def test_buscar_proprio_usuario_apos_logout(client):
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


def test_buscar_logs_sem_token(client):
    response = client.get("/api/auth/logs")

    assert response.status_code == 401


def test_buscar_logs_com_token_invalido(client):
    response = client.get(
        "/api/auth/logs",
        headers={"Authorization": "Bearer token_invalido"},
    )

    assert response.status_code == 401


def test_buscar_logs_com_pagina_invalida(client):
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


def test_buscar_logs_com_limite_invalido(client):
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


def test_buscar_logs_com_limite_acima_do_maximo(client):
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


def test_buscar_logs_sucesso(client):
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


def test_buscar_logs_paginacao(client):
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


def test_buscar_logs_pagina_sem_registro(client):
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


def test_buscar_logs_ordenados_por_login_mais_recente(client):
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
