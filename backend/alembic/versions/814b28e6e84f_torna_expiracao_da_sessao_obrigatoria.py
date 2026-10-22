"""torna expiracao da sessao obrigatoria

Revision ID: 814b28e6e84f
Revises: 6c82caf2057c
Create Date: 2026-10-22 10:19:57.109531

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "814b28e6e84f"
down_revision: Union[str, Sequence[str], None] = "6c82caf2057c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Torna expires_at obrigatório."""
    with op.batch_alter_table("access_logs") as batch_op:
        batch_op.alter_column(
            "expires_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Permite novamente expires_at nulo."""
    with op.batch_alter_table("access_logs") as batch_op:
        batch_op.alter_column(
            "expires_at",
            existing_type=sa.DateTime(),
            nullable=True,
        )
    # ### end Alembic commands ###
