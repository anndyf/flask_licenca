"""Alterando prazo_cumprimento para Date

Revision ID: cfb5d97ad4d6
Revises: b249bda13da8
Create Date: 2025-02-23 20:54:42.451159

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cfb5d97ad4d6'
down_revision = 'b249bda13da8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('condicionante', schema=None) as batch_op:
        batch_op.alter_column('prazo_cumprimento',
                              existing_type=sa.VARCHAR(length=100),
                              type_=sa.Date(),
                              existing_nullable=True,
                              # Conversão explícita para evitar erro
                              postgresql_using="prazo_cumprimento::DATE")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('condicionante', schema=None) as batch_op:
        batch_op.alter_column('prazo_cumprimento',
                              existing_type=sa.Date(),
                              type_=sa.VARCHAR(length=100),
                              existing_nullable=True)

    # ### end Alembic commands ###
