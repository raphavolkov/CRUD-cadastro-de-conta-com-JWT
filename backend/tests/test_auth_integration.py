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


def test_login_email_ou_senha_invalidos(client):
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
