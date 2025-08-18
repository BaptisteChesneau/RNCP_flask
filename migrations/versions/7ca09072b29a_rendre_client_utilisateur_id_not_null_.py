"""Rendre client.utilisateur_id NOT NULL manuellement

Revision ID: 7ca09072b29a
Revises: d38d41a05fc4
Create Date: 2025-08-18 15:11:29.334515
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7ca09072b29a'
down_revision = 'd38d41a05fc4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("client", schema=None) as batch_op:
        batch_op.alter_column(
            "utilisateur_id",
            existing_type=sa.Integer(),
            nullable=False
        )


def downgrade():
    with op.batch_alter_table("client", schema=None) as batch_op:
        batch_op.alter_column(
            "utilisateur_id",
            existing_type=sa.Integer(),
            nullable=True
        )
