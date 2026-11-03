"""Corrige restricoes e indice de usuarios.

Revision ID: ad373fe7fd17
Revises: 814b28e6e84f
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ad373fe7fd17"
down_revision: str | Sequence[str] | None = "814b28e6e84f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Corrige as restricoes das tabelas."""

    op.drop_index("ix_users_email", table_name="users")

    op.drop_index(
        "ux_access_logs_session_id",
        table_name="access_logs",
    )
    op.drop_index(
        "ux_access_logs_one_active_session_per_user",
        table_name="access_logs",
    )

    with op.batch_alter_table(
        "users",
        naming_convention={
            "uq": "uq_%(table_name)s_%(column_0_name)s",
        },
    ) as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=sa.String(length=36),
            nullable=False,
        )
        batch_op.drop_constraint(
            "uq_users_email",
            type_="unique",
        )
        batch_op.create_unique_constraint(
            "uq_users_email",
            ["email"],
        )

    with op.batch_alter_table("access_logs") as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=sa.String(length=36),
            nullable=False,
        )

    op.create_index(
        "ux_access_logs_session_id",
        "access_logs",
        ["session_id"],
        unique=True,
    )
    op.create_index(
        "ux_access_logs_one_active_session_per_user",
        "access_logs",
        ["user_id"],
        unique=True,
        sqlite_where=sa.text("logout_at IS NULL"),
    )


def downgrade() -> None:
    """Reverte as alteracoes desta migracao."""

    op.drop_index(
        "ux_access_logs_one_active_session_per_user",
        table_name="access_logs",
    )
    op.drop_index(
        "ux_access_logs_session_id",
        table_name="access_logs",
    )

    with op.batch_alter_table("access_logs") as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=sa.String(length=36),
            nullable=True,
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=sa.String(length=36),
            nullable=True,
        )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=False,
    )

    op.create_index(
        "ux_access_logs_session_id",
        "access_logs",
        ["session_id"],
        unique=True,
    )
    op.create_index(
        "ux_access_logs_one_active_session_per_user",
        "access_logs",
        ["user_id"],
        unique=True,
        sqlite_where=sa.text("logout_at IS NULL"),
    )
