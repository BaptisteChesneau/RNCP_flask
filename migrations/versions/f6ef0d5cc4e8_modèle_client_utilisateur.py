"""Modèle Client Utilisateur

Revision ID: f6ef0d5cc4e8
Revises: 50625f812388
Create Date: 2025-08-18 12:43:19.080792

"""
from alembic import op
import sqlalchemy as sa


# Identifiants de révision
revision = 'f6ef0d5cc4e8'
down_revision = '50625f812388'
branch_labels = None
depends_on = None


def upgrade():
    # Étape 1 : Ajouter la colonne en nullable=True
    with op.batch_alter_table('client', schema=None) as batch_op:
        batch_op.add_column(sa.Column('utilisateur_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'utilisateur', ['utilisateur_id'], ['id'])

    # Remarque : après cette migration, exécute une commande SQL dans PostgreSQL :
    #    UPDATE client SET utilisateur_id = 1 WHERE utilisateur_id IS NULL;
    # (remplace 1 par un ID utilisateur réel)

    # Une deuxième migration devra ensuite rendre cette colonne NOT NULL


def downgrade():
    # Supprimer la colonne et la contrainte en cas de rollback
    with op.batch_alter_table('client', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('utilisateur_id')
