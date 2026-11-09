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

Antes de começar, instale:

- **Python 3.14** — versão utilizada no desenvolvimento e nos testes do projeto.
- **Git** — para clonar o repositório.
- **Navegador moderno** — para acessar a aplicação.
- **Visual Studio Code** (opcional) — com a extensão Live Server, caso prefira utilizá-la para servir o frontend.

Confira a versão do Python:

```bash
python --version
```

No Linux e macOS, caso o comando `python` não esteja disponível:

```bash
python3.14 --version
```

### 2. Clonar o repositório

```bash
git clone https://github.com/raphavolkov/CRUD-cadastro-de-conta-com-JWT.git
cd CRUD-cadastro-de-conta-com-JWT
```

### 3. Criar e ativar o ambiente virtual

A partir da raiz do projeto, entre no diretório do backend:

```bash
cd backend
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Caso o PowerShell bloqueie a ativação do ambiente virtual, execute o comando abaixo na mesma janela e tente ativar novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Essa configuração vale somente para o processo atual do PowerShell.

**Linux e macOS:**

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

Após a ativação, o terminal deverá indicar que o ambiente virtual está ativo, normalmente exibindo `(.venv)`.

### 4. Instalar as dependências

Com o ambiente virtual ativo, execute:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

O arquivo `requirements-dev.txt` instala as dependências da aplicação e as ferramentas utilizadas no desenvolvimento e nos testes.

### 5. Configurar as variáveis de ambiente

Crie o arquivo `.env` a partir do modelo disponibilizado.

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
```

**Linux e macOS:**

```bash
cp .env.example .env
```

Gere uma chave secreta com o Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copie o valor gerado e substitua o conteúdo de `SECRET_KEY` no arquivo `.env`.

Exemplo de configuração:

```dotenv
SECRET_KEY=sua_chave_secreta_gerada_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Importante:** não utilize o valor de exemplo como chave secreta. A aplicação exige uma chave válida com pelo menos 32 caracteres. O arquivo `.env` contém informações sensíveis e não deve ser enviado ao repositório.

### 6. Criar e atualizar o banco de dados

Com o ambiente virtual ativo e ainda dentro do diretório `backend`, execute:

```bash
alembic upgrade head
```

O comando aplica as migrações pendentes do Alembic e cria ou atualiza a estrutura do banco de dados.

Outros comandos úteis do Alembic:

```bash
# Consultar a revisão atual do banco
alembic current

# Consultar o histórico de migrações
alembic history

# Criar uma nova migração
alembic revision -m "descricao_da_migration"
```

O projeto utiliza SQLite. O arquivo do banco é armazenado em:

```text
backend/data/database.db
```

O diretório necessário é criado automaticamente quando a aplicação ou as migrações inicializam o banco de dados.

### 7. Iniciar o backend

Ainda no diretório `backend`, execute:

```bash
uvicorn app.main:app --reload
```

Por padrão, a API ficará disponível em:

- **API:** http://127.0.0.1:8000
- **Documentação Swagger:** http://127.0.0.1:8000/docs
- **Documentação ReDoc:** http://127.0.0.1:8000/redoc

Mantenha esse terminal aberto enquanto estiver utilizando a aplicação.

### 8. Iniciar o frontend

O frontend é composto por arquivos estáticos HTML, CSS e JavaScript. Não é necessário instalar Node.js ou utilizar npm.

Abra um **novo terminal na raiz do projeto** e execute:

```bash
python -m http.server 5500 --directory frontend
```

Acesse a aplicação pelo navegador:

http://127.0.0.1:5500/pages/index.html

Como alternativa, é possível utilizar a extensão Live Server do Visual Studio Code, desde que o frontend seja servido na porta `5500` e pela origem `http://127.0.0.1`.

**Observação sobre CORS:** o backend está configurado para aceitar as origens `http://127.0.0.1:5500` e `http://localhost:5500`. Caso utilize outra origem ou porta, será necessário ajustar a configuração de CORS em `backend/app/main.py`. Se alterar o endereço da API, atualize também `API_BASE_URL` em `frontend/scripts/app.js`.

### 9. Acessar a aplicação

Com o backend e o frontend em execução, acesse:

http://127.0.0.1:5500/pages/index.html

A partir dessa página, será possível utilizar as funcionalidades de cadastro, autenticação e gerenciamento disponibilizadas pela aplicação.

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

Os testes utilizam um banco SQLite em memória, isolado por execução, evitando interferência no banco de desenvolvimento.

Para executar os testes:

```bash
pytest -q
```

Para verificar a cobertura:

```bash
pytest --cov=app --cov-report=term-missing
```

Para verificar a qualidade do código:

```bash
ruff check .
```

**Resultado da última execução registrada:** 116 testes aprovados.

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
