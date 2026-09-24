from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "dcb2d04744a5"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria o schema legado caso as tabelas ainda não existam."""
    connection = op.get_bind()

    connection.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR NOT NULL,
                email VARCHAR NOT NULL UNIQUE,
                password_hash VARCHAR NOT NULL,
                created_at DATETIME NOT NULL
            )
            """))

    connection.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS access_logs (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                login_at DATETIME NOT NULL,
                logout_at DATETIME
            )
            """))

    connection.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS ix_users_email
            ON users(email)
            """))


def downgrade() -> None:
    """Remove o schema legado."""
    connection = op.get_bind()

    connection.execute(sa.text("DROP TABLE IF EXISTS access_logs"))

    connection.execute(sa.text("DROP TABLE IF EXISTS users"))
