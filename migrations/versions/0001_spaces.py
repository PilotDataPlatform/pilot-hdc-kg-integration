# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""spaces.

Revision ID: 0001
Revises:
Create Date: 2023-08-01 11:01:54.208499
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'spaces',
        sa.Column('name', sa.VARCHAR(), nullable=False),
        sa.Column('creator', sa.VARCHAR(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('name'),
        schema='kg_integration',
    )


def downgrade():
    op.drop_table('spaces', schema='kg_integration')
