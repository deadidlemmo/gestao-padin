"""Add WhatsApp opt-in fields to user

Revision ID: 20260525_whatsapp_optin
Revises: 20260524_appnotif
Create Date: 2026-05-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260525_whatsapp_optin"
down_revision = "20260524_appnotif"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "whatsapp_opt_in",
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("whatsapp_opt_in_at", sa.DateTime(), nullable=True))

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("whatsapp_opt_in", server_default=None)


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("whatsapp_opt_in_at")
        batch_op.drop_column("whatsapp_opt_in")
