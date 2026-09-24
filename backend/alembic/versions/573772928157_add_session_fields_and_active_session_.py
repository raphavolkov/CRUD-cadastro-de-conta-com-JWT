"""add session fields and active session constraint

Revision ID: 573772928157
Revises: dcb2d04744a5
Create Date: 2026-09-24 12:52:12.008791

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "573772928157"
down_revision: Union[str, Sequence[str], None] = "dcb2d04744a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Atualiza o schema legado para o schema atual."""
    import uuid

    op.add_column(
        "access_logs",
        sa.Column("session_id", sa.String(length=36), nullable=True),
    )

    op.add_column(
        "access_logs",
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )

    connection = op.get_bind()

    rows = connection.execute(
        sa.text(
            "SELECT id, login_at, logout_at "
            "FROM access_logs "
            "WHERE session_id IS NULL"
        )
    ).fetchall()

    for row in rows:
        connection.execute(
            sa.text(
                "UPDATE access_logs "
                "SET session_id = :session_id, "
                "expires_at = :expires_at "
                "WHERE id = :id"
            ),
            {
                "session_id": str(uuid.uuid4()),
                "expires_at": row.login_at,
                "id": row.id,
            },
        )

    connection.execute(
        sa.text(
            "UPDATE access_logs " "SET logout_at = login_at " "WHERE logout_at IS NULL"
        )
    )

    connection.execute(
        sa.text(
            "CREATE UNIQUE INDEX ux_access_logs_session_id "
            "ON access_logs(session_id)"
        )
    )

    connection.execute(
        sa.text(
            "CREATE UNIQUE INDEX "
            "ux_access_logs_one_active_session_per_user "
            "ON access_logs(user_id) "
            "WHERE logout_at IS NULL"
        )
    )


def downgrade() -> None:
    """Reverte a atualização do schema."""
    connection = op.get_bind()

    connection.execute(
        sa.text("DROP INDEX IF EXISTS " "ux_access_logs_one_active_session_per_user")
    )

    connection.execute(sa.text("DROP INDEX IF EXISTS ux_access_logs_session_id"))

    op.drop_column("access_logs", "expires_at")
    op.drop_column("access_logs", "session_id")
