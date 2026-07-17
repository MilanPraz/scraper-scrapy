"""add pg trigram search indexes

Revision ID: a3c04a0d0da3
Revises: 3652a0091596
Create Date: 2026-07-17 10:31:58.635406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3c04a0d0da3'
down_revision: Union[str, Sequence[str], None] = '3652a0091596'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_products_brand_trgm "
        "ON products USING gin (brand gin_trgm_ops);"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_products_model_name_trgm "
        "ON products USING gin (model_name gin_trgm_ops);"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_products_category_trgm "
        "ON products USING gin (category gin_trgm_ops);"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_products_ram_trgm "
        "ON products USING gin (ram gin_trgm_ops);"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_products_storage_trgm "
        "ON products USING gin (storage gin_trgm_ops);"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_products_storage_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_products_ram_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_products_category_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_products_model_name_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_products_brand_trgm;")