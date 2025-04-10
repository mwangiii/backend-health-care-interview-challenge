"""Add patient image column

Revision ID: 9171362e9839
Revises: 391dba40e7e5
Create Date: 2025-04-10 03:28:59.565640

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9171362e9839'
down_revision = '391dba40e7e5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('patients', schema=None) as batch_op:
        batch_op.alter_column('image',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.Text(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('patients', schema=None) as batch_op:
        batch_op.alter_column('image',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)

    # ### end Alembic commands ###
