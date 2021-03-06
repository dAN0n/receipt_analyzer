"""26_12_2017_12_15

Revision ID: a0f2841d4756
Revises: d33477f8bc66
Create Date: 2017-12-26 12:15:59.390250

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0f2841d4756'
down_revision = 'd33477f8bc66'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('temp_username', sa.String(length=64), nullable=True))
        batch_op.create_index(batch_op.f('ix_user_product_temp_username'), ['temp_username'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_product', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_product_temp_username'))
        batch_op.drop_column('temp_username')

    # ### end Alembic commands ###
