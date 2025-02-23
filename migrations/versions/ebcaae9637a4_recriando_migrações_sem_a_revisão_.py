"""Recriando migrações sem a revisão corrompida

Revision ID: ebcaae9637a4
Revises: 
Create Date: 2025-02-22 22:50:22.176979

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ebcaae9637a4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('licenca', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email_empresa', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('licenca', schema=None) as batch_op:
        batch_op.drop_column('email_empresa')

    # ### end Alembic commands ###
