"""Adicionando campo observacoes na Licenca

Revision ID: 9a611238e0c5
Revises: b5a9bbfab532
Create Date: 2025-02-23 21:58:04.500929

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a611238e0c5'
down_revision = 'b5a9bbfab532'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('licenca', schema=None) as batch_op:
        batch_op.add_column(sa.Column('observacoes', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('licenca', schema=None) as batch_op:
        batch_op.drop_column('observacoes')

    # ### end Alembic commands ###
