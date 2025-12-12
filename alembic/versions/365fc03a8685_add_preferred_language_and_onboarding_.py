"""add preferred language and onboarding completed

Revision ID: 365fc03a8685
Revises: b116b9136b05
Create Date: 2025-12-12 11:20:41.221835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '365fc03a8685'
down_revision: Union[str, None] = 'b116b9136b05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type first
    preferredlanguage_enum = sa.Enum('ENGLISH', 'HAUSA', 'IGBO', 'YORUBA', name='preferredlanguage')
    preferredlanguage_enum.create(op.get_bind(), checkfirst=True)
    
    # Add columns
    op.add_column('patients', sa.Column('preferred_language', sa.Enum('ENGLISH', 'HAUSA', 'IGBO', 'YORUBA', name='preferredlanguage'), nullable=True))
    op.add_column('patients', sa.Column('onboarding_completed', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    # Drop columns
    op.drop_column('patients', 'onboarding_completed')
    op.drop_column('patients', 'preferred_language')
    
    # Drop the enum type
    sa.Enum(name='preferredlanguage').drop(op.get_bind(), checkfirst=True)
