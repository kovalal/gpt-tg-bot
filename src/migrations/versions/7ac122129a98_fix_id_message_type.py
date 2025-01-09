"""fix id message type

Revision ID: 7ac122129a98
Revises: 55509ee314a0
Create Date: 2024-12-28 17:57:51.501658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ac122129a98'
down_revision: Union[str, None] = '55509ee314a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
