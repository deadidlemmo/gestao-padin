"""Add app notification table

Revision ID: 20260524_appnotif
Revises: 4998fb41208b
Create Date: 2026-05-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260524_appnotif"
down_revision = "4998fb41208b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "app_notification",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("level", sa.String(length=20), server_default="info", nullable=False),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("kind", sa.String(length=40), server_default="system", nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "is_cleared", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("cleared_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_app_notification_user_id", "app_notification", ["user_id"])
    op.create_index("ix_app_notification_level", "app_notification", ["level"])
    op.create_index("ix_app_notification_kind", "app_notification", ["kind"])
    op.create_index(
        "ix_app_notification_entity_type", "app_notification", ["entity_type"]
    )
    op.create_index("ix_app_notification_entity_id", "app_notification", ["entity_id"])
    op.create_index("ix_app_notification_is_read", "app_notification", ["is_read"])
    op.create_index(
        "ix_app_notification_is_cleared", "app_notification", ["is_cleared"]
    )
    op.create_index(
        "ix_app_notification_created_at", "app_notification", ["created_at"]
    )
    op.create_index(
        "ix_app_notification_user_unread",
        "app_notification",
        ["user_id", "is_read", "is_cleared"],
    )
    op.create_index(
        "ix_app_notification_entity",
        "app_notification",
        ["entity_type", "entity_id"],
    )


def downgrade():
    op.drop_index("ix_app_notification_entity", table_name="app_notification")
    op.drop_index("ix_app_notification_user_unread", table_name="app_notification")
    op.drop_index("ix_app_notification_created_at", table_name="app_notification")
    op.drop_index("ix_app_notification_is_cleared", table_name="app_notification")
    op.drop_index("ix_app_notification_is_read", table_name="app_notification")
    op.drop_index("ix_app_notification_entity_id", table_name="app_notification")
    op.drop_index("ix_app_notification_entity_type", table_name="app_notification")
    op.drop_index("ix_app_notification_kind", table_name="app_notification")
    op.drop_index("ix_app_notification_level", table_name="app_notification")
    op.drop_index("ix_app_notification_user_id", table_name="app_notification")
    op.drop_table("app_notification")
