# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

"""metadata.

Revision ID: 0002
Revises: 0002
Create Date: 2023-08-01 11:15:46.579742
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('metadata_id', sa.UUID(), nullable=True),
        sa.Column('kg_instance_id', sa.UUID(), nullable=True),
        sa.Column('uploaded_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='kg_integration',
    )


def downgrade():
    op.drop_table('metadata', schema='kg_integration')
