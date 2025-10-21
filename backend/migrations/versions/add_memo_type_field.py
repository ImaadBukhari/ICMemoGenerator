"""Add memo_type field to MemoRequest

Revision ID: add_memo_type_field
Revises: bacb40cfc0cf
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_memo_type_field'
down_revision = 'bacb40cfc0cf'
branch_labels = None
depends_on = None


def upgrade():
    # Add memo_type column to memo_requests table
    op.add_column('memo_requests', sa.Column('memo_type', sa.String(), nullable=True, default='full'))


def downgrade():
    # Remove memo_type column from memo_requests table
    op.drop_column('memo_requests', 'memo_type')
