# CRUD de Cadastro e Autenticação com FastAPI

API REST para cadastro e autenticação de usuários, desenvolvida com Python e FastAPI.

O projeto implementa autenticação JWT com Access Token e Refresh Token, gerenciamento de sessões, histórico de acessos e mecanismos de proteção contra tentativas excessivas de autenticação.

## Tecnologias utilizadas

### Backend

- **Python 3.14** — linguagem de programação.
- **FastAPI** — construção da API REST.
- **SQLAlchemy** — ORM e persistência de dados.
- **SQLite** — banco de dados.
- **Alembic** — gerenciamento de migrations.
- **Pydantic** — validação e serialização de dados.
- **Python-JOSE** — criação e validação de tokens JWT.
- **pwdlib + Argon2** — hash e verificação de senhas.
- **SlowAPI** — rate limiting.

### Frontend

- HTML5
- CSS3
- JavaScript
- Tailwind CSS

### Testes e qualidade

- Pytest
- Pytest-Cov
- Ruff

## Funcionalidades

- Cadastro de usuários.
- Autenticação com e-mail e senha.
- Hash de senhas utilizando Argon2.
- Autenticação baseada em JWT.
- Separação entre Access Token e Refresh Token.
- Renovação e rotação de tokens.
- Armazenamento dos Refresh Tokens em formato hash SHA-256.
- Identificação de tokens por meio de JTI.
- Controle de sessões ativas.
- Restrição de uma sessão ativa por usuário.
- Logout com encerramento da sessão.
- Validação da sessão durante requisições autenticadas.
- Consulta dos dados do usuário autenticado.
- Histórico de acessos com paginação.
- Rate limiting nos endpoints de cadastro, login e renovação de tokens.
- Validação de dados com Pydantic.
- Gerenciamento de estrutura do banco por meio de migrations com Alembic.

## Arquitetura do projeto

O backend utiliza uma separação de responsabilidades entre rotas, serviços e repositórios, facilitando a manutenção, organização e evolução da aplicação.

```text
Projeto Login/
│
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   ├── 573772928157_add_session_fields_and_active_session_.py
│   │   │   ├── 6c82caf2057c_add_refresh_tokens_table.py
│   │   │   ├── 814b28e6e84f_torna_expiracao_da_sessao_obrigatoria.py
│   │   │   ├── ad373fe7fd17_corrige_restricoes_e_indice_de_usuarios.py
│   │   │   └── dcb2d04744a5_initial_schema.py
│   │   ├── README
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── app/
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── auth_repository.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── auth.py
│   │   ├── services/
│   │   │   └── auth_service.py
│   │   ├── database.py
│   │   ├── limiter.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── security.py
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth_integration.py
│   │   ├── test_engine.py
│   │   ├── test_schemas.py
│   │   └── test_security.py
│   │
│   ├── .env.example
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── pytest.ini
│   ├── requirements-dev.txt
│   └── requirements.txt
│
├── frontend/
│   ├── css/
│   │   └── style.css
│   ├── pages/
│   │   ├── dashboard.html
│   │   ├── index.html
│   │   ├── login.html
│   │   └── register.html
│   ├── scripts/
│   │   └── app.js
│   └── .prettierrc
│
├── .gitignore
└── README.md
```

### Organização do backend

| Camada       | Responsabilidade                                       |
| ------------ | ------------------------------------------------------ |
| Routers      | Recebem as requisições HTTP e direcionam as operações. |
| Services     | Contêm as regras de negócio.                           |
| Repositories | Centralizam as operações de persistência.              |
| Models       | Definem as entidades e o mapeamento do banco.          |
| Schemas      | Validam os dados de entrada e saída.                   |
| Security     | Gerencia senhas, JWT e autenticação das sessões.       |
| Core         | Centraliza as configurações da aplicação.              |

## Configuração e instalação

### 1. Pré-requisitos

- Python 3.14.
- Git.
- Navegador web moderno.

**Opcional:** Visual Studio Code e extensão Live Server para facilitar a execução do frontend durante o desenvolvimento.

### 2. Clonar o repositório

```powershell
git clone https://github.com/raphavolkov/CRUD-cadastro-de-conta-com-JWT.git
cd CRUD-cadastro-de-conta-com-JWT
```

### 3. Criar o ambiente virtual

No Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Instalar as dependências

Dentro da pasta `backend`, execute:

```powershell
pip install -r requirements-dev.txt
```

Esse comando instala as dependências da aplicação e as ferramentas necessárias para desenvolvimento, testes e análise de código.

### 5. Configurar as variáveis de ambiente

Crie um arquivo `.env` dentro da pasta `backend`, utilizando o `.env.example` como referência.

```powershell
Copy-Item .env.example .env
```

O arquivo deverá conter:

```dotenv
SECRET_KEY=sua_chave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Gere uma chave secreta forte utilizando:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copie o valor gerado para a variável `SECRET_KEY`.

**Importante:** nunca compartilhe ou versione o arquivo `.env` com credenciais reais.

### 6. Executar as migrations

Ainda dentro da pasta `backend`, execute:

```powershell
alembic upgrade head
```

Esse comando aplica todas as migrations pendentes e atualiza a estrutura do banco de dados.

Outros comandos úteis do Alembic:

```powershell
# Consultar a revisão atual do banco
alembic current

# Consultar o histórico de migrations
alembic history

# Criar uma nova migration
alembic revision -m "descricao_da_migration"

# Aplicar todas as migrations pendentes
alembic upgrade head
```

O banco SQLite será utilizado em:

`backend/data/database.db`

O diretório e o banco são criados automaticamente quando necessário.

### 7. Iniciar o backend

Ainda dentro da pasta `backend`, execute:

```powershell
uvicorn app.main:app --reload
```

A API estará disponível em:

[http://127.0.0.1:8000](http://127.0.0.1:8000)

Documentação interativa:

- [Swagger UI](http://127.0.0.1:8000/docs)
- [ReDoc](http://127.0.0.1:8000/redoc)

### 8. Iniciar o frontend

Uma opção para executar o frontend durante o desenvolvimento é utilizar o Visual Studio Code com a extensão Live Server.

Abra o arquivo:

`frontend/pages/index.html`

Com o Live Server, o frontend será servido em:

[http://127.0.0.1:5500](http://127.0.0.1:5500)

O frontend utiliza a API disponível em [http://127.0.0.1:8000](http://127.0.0.1:8000) para realizar as requisições HTTP.

**Observação:** o Live Server é uma ferramenta opcional de desenvolvimento. A configuração atual de comunicação e CORS utiliza endereços locais. Caso altere a porta do Live Server, será necessário atualizar as configurações correspondentes.

## Endpoints da API

Prefixo: `/api/auth`

| Método | Endpoint    | Descrição                                | Autenticação  |
| ------ | ----------- | ---------------------------------------- | ------------- |
| POST   | `/register` | Cadastra um usuário.                     | Não           |
| POST   | `/login`    | Autentica um usuário.                    | Não           |
| GET    | `/me`       | Retorna os dados do usuário autenticado. | Sim           |
| POST   | `/logout`   | Encerra a sessão atual.                  | Sim           |
| POST   | `/refresh`  | Renova os tokens de autenticação.        | Refresh Token |
| GET    | `/logs`     | Consulta o histórico de acessos.         | Sim           |

### Exemplos de requisições

**Cadastro — POST `/api/auth/register`**

```json
{
  "name": "Usuario Teste",
  "email": "teste@example.com",
  "password": "senha_segura_123"
}
```

**Login — POST `/api/auth/login`**

```json
{
  "email": "teste@example.com",
  "password": "senha_segura_123"
}
```

**Renovação de tokens — POST `/api/auth/refresh`**

```json
{
  "refresh_token": "seu_refresh_token"
}
```

**Histórico de acessos — GET `/api/auth/logs?page=1&limit=10`**

Os endpoints protegidos utilizam o cabeçalho:

```http
Authorization: Bearer SEU_ACCESS_TOKEN
```

## Segurança

O projeto implementa diferentes mecanismos para proteger a autenticação e o gerenciamento de sessões:

- **Argon2:** armazenamento seguro de senhas por meio de hash.
- **JWT:** tokens assinados para autenticação.
- **Separação de tokens:** Access Token e Refresh Token possuem finalidades distintas e são validados conforme seu tipo.
- **JTI:** identificador único para cada token.
- **SHA-256:** os Refresh Tokens são armazenados em formato hash.
- **Rotação de tokens:** a renovação gera novos tokens e atualiza o registro correspondente.
- **Controle de sessão:** as requisições autenticadas verificam a existência de uma sessão ativa no banco.
- **Restrição de sessão:** impede a manutenção de múltiplas sessões ativas para o mesmo usuário.
- **Logout:** encerra a sessão atual e impede sua reutilização.
- **Rate limiting:** limita tentativas de cadastro, login e renovação de tokens.

## Testes automatizados

O projeto utiliza Pytest para testar as funcionalidades e os mecanismos de segurança.

Os testes utilizam um banco SQLite separado (`test_database.db`), evitando interferência no banco de desenvolvimento.

Para executar os testes:

```powershell
pytest
```

Para verificar a cobertura:

```powershell
pytest --cov=app --cov-report=term-missing
```

A cobertura atual dos testes é de 99% do código da aplicação.

Para verificar a qualidade do código:

```powershell
ruff check .
```

**Resultado da última execução registrada:** 115 testes aprovados.

## Observações

Este projeto foi desenvolvido com finalidade de aprendizado e demonstração de práticas de desenvolvimento backend, organização de código, autenticação e testes automatizados.

Apesar dos mecanismos de segurança implementados, antes de utilizar a aplicação em produção é necessário revisar aspectos como:

- Armazenamento de tokens no frontend, atualmente realizado com `localStorage`.
- Estratégia de proteção contra ataques XSS e CSRF, conforme o mecanismo de armazenamento escolhido.
- Configuração de CORS para os domínios autorizados.
- Gerenciamento e armazenamento de segredos.
- Configuração de infraestrutura, monitoramento e logs.
- Estratégia de backup e recuperação do banco de dados.

---

Desenvolvido com Python, FastAPI e JavaScript.
