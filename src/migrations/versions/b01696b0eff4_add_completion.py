"""Add Completion

Revision ID: b01696b0eff4
Revises: 9348baeddf2b
Create Date: 2024-12-29 22:06:25.365865

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b01696b0eff4'
down_revision: Union[str, None] = '9348baeddf2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('completions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('system_fingerprint', sa.String(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('model', sa.String(), nullable=False),
    sa.Column('prompt_tokens', sa.Integer(), nullable=False),
    sa.Column('completion_tokens', sa.Integer(), nullable=False),
    sa.Column('total_tokens', sa.Integer(), nullable=False),
    sa.Column('completion_tokens_details', sa.JSON(), nullable=True),
    sa.Column('cost', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('messages', sa.Column('completion_id', sa.String(), nullable=True))
    op.create_foreign_key(None, 'messages', 'completions', ['completion_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'messages', type_='foreignkey')
    op.drop_column('messages', 'completion_id')
    op.drop_table('completions')
    # ### end Alembic commands ###
