"""Начальная схема Телеграм-магазина

Revision ID: 0001_shop_schema
Revises:
Create Date: 2026-05-29 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_shop_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Проверка наличия таблицы
def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = :table_name
            """
        ),
        {"table_name": table_name},
    )

    return result.scalar_one_or_none() is not None


# Проверка наличия колонки
def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(sa.text(f"PRAGMA table_info({table_name})"))

    return column_name in [row.name for row in result]


# Добавление колонки, если ее нет
def _add_column(table_name: str, column_name: str, column_sql: str) -> None:
    if not _column_exists(table_name, column_name):
        op.execute(sa.text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))


# Создание индекса, если его нет
def _create_index(index_name: str, table_name: str, columns: str, *, unique: bool = False) -> None:
    unique_sql = "UNIQUE " if unique else ""
    op.execute(sa.text(f"CREATE {unique_sql}INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})"))


# Нормализация текстовых bool-значений
def _normalize_boolean_text(table_name: str, column_name: str, default_value: str) -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            f"""
            UPDATE {table_name}
            SET {column_name} = CASE LOWER(CAST(COALESCE({column_name}, :default_value) AS TEXT))
                WHEN '1' THEN 'True'
                WHEN 'true' THEN 'True'
                WHEN 'yes' THEN 'True'
                WHEN 'on' THEN 'True'
                WHEN 'да' THEN 'True'
                WHEN '0' THEN 'False'
                WHEN 'false' THEN 'False'
                WHEN 'no' THEN 'False'
                WHEN 'off' THEN 'False'
                WHEN 'нет' THEN 'False'
                ELSE :default_value
            END
            """
        ),
        {"default_value": default_value},
    )


# Сбор SQL для переноса текстовой колонки
def _copy_expr(table_name: str, column_name: str, default_value: str) -> str:
    if _column_exists(table_name, column_name):
        return f"COALESCE({column_name}, '{default_value}')"

    return f"'{default_value}'"


# Сбор SQL для переноса числовой колонки
def _copy_int_expr(table_name: str, column_name: str, default_value: int = 0) -> str:
    if _column_exists(table_name, column_name):
        return f"COALESCE({column_name}, {default_value})"

    return str(default_value)


# Создание или правка таблицы пользователей
def _ensure_users() -> None:
    bind = op.get_bind()

    if not _table_exists("storage_users"):
        op.create_table(
            "storage_users",
            sa.Column("increment", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("user_login", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("user_name", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("user_surname", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("user_fullname", sa.String(length=511), nullable=False, server_default=""),
            sa.Column("user_balance", sa.Float(), nullable=False, server_default="0"),
            sa.Column("user_refill", sa.Float(), nullable=False, server_default="0"),
            sa.Column("user_give", sa.Float(), nullable=False, server_default="0"),
            sa.Column("user_unix", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("increment"),
        )
    else:
        _add_column("storage_users", "user_login", "TEXT NOT NULL DEFAULT ''")
        _add_column("storage_users", "user_name", "TEXT NOT NULL DEFAULT ''")
        _add_column("storage_users", "user_surname", "TEXT NOT NULL DEFAULT ''")
        _add_column("storage_users", "user_fullname", "TEXT NOT NULL DEFAULT ''")
        _add_column("storage_users", "user_balance", "REAL NOT NULL DEFAULT 0")
        _add_column("storage_users", "user_refill", "REAL NOT NULL DEFAULT 0")
        _add_column("storage_users", "user_give", "REAL NOT NULL DEFAULT 0")
        _add_column("storage_users", "user_unix", "INTEGER NOT NULL DEFAULT 0")
        bind.execute(sa.text("UPDATE storage_users SET user_login = COALESCE(user_login, '')"))
        bind.execute(sa.text("UPDATE storage_users SET user_name = COALESCE(user_name, '')"))
        bind.execute(sa.text("UPDATE storage_users SET user_surname = COALESCE(user_surname, '')"))
        bind.execute(
            sa.text(
                """
                UPDATE storage_users
                SET user_fullname = CASE
                    WHEN user_fullname IS NULL OR user_fullname = '' THEN TRIM(user_name || ' ' || user_surname)
                    ELSE user_fullname
                END
                """
            )
        )
        bind.execute(sa.text("UPDATE storage_users SET user_balance = COALESCE(user_balance, 0)"))
        bind.execute(sa.text("UPDATE storage_users SET user_refill = COALESCE(user_refill, 0)"))
        bind.execute(sa.text("UPDATE storage_users SET user_give = COALESCE(user_give, 0)"))
        bind.execute(sa.text("UPDATE storage_users SET user_unix = COALESCE(user_unix, 0)"))
        bind.execute(sa.text("DELETE FROM storage_users WHERE user_id IS NULL"))
        bind.execute(
            sa.text(
                """
                DELETE
                FROM storage_users
                WHERE user_id IS NOT NULL
                  AND rowid NOT IN (
                      SELECT MAX(rowid)
                      FROM storage_users
                      WHERE user_id IS NOT NULL
                      GROUP BY user_id
                  )
                """
            )
        )

    _create_index("ix_storage_users_user_id", "storage_users", "user_id", unique=True)


# Создание или правка таблицы настроек
def _ensure_settings() -> None:
    bind = op.get_bind()

    if not _table_exists("storage_settings"):
        op.create_table(
            "storage_settings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("status_work", sa.String(length=16), nullable=False, server_default="True"),
            sa.Column("status_refill", sa.String(length=16), nullable=False, server_default="False"),
            sa.Column("status_buy", sa.String(length=16), nullable=False, server_default="False"),
            sa.Column("notification_refill", sa.String(length=16), nullable=False, server_default="True"),
            sa.Column("notification_buy", sa.String(length=16), nullable=False, server_default="False"),
            sa.Column("misc_faq", sa.String(), nullable=False, server_default="None"),
            sa.Column("misc_support", sa.String(), nullable=False, server_default="None"),
            sa.Column("misc_bot", sa.String(length=255), nullable=False, server_default="None"),
            sa.Column("misc_hosting_text", sa.String(length=64), nullable=False, server_default="telegraph"),
            sa.Column("misc_token_telegraph", sa.String(), nullable=False, server_default="None"),
            sa.Column("misc_discord_webhook_url", sa.String(), nullable=False, server_default="None"),
            sa.Column("misc_discord_webhook_name", sa.String(length=255), nullable=False, server_default="None"),
            sa.Column("misc_hide_category", sa.String(length=16), nullable=False, server_default="False"),
            sa.Column("misc_hide_position", sa.String(length=16), nullable=False, server_default="False"),
            sa.Column("misc_profit_day", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("misc_profit_week", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("misc_profit_month", sa.Integer(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        bind.execute(sa.text("DROP TABLE IF EXISTS storage_settings_new"))
        op.create_table(
            "storage_settings_new",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("status_work", sa.String(length=16), nullable=False, server_default="True"),
            sa.Column("status_refill", sa.String(length=16), nullable=False, server_default="False"),
            sa.Column("status_buy", sa.String(length=16), nullable=False, server_default="False"),
            sa.Column("notification_refill", sa.String(length=16), nullable=False, server_default="True"),
            sa.Column("notification_buy", sa.String(length=16), nullable=False, server_default="False"),
            sa.Column("misc_faq", sa.String(), nullable=False, server_default="None"),
            sa.Column("misc_support", sa.String(), nullable=False, server_default="None"),
            sa.Column("misc_bot", sa.String(length=255), nullable=False, server_default="None"),
            sa.Column("misc_hosting_text", sa.String(length=64), nullable=False, server_default="telegraph"),
            sa.Column("misc_token_telegraph", sa.String(), nullable=False, server_default="None"),
            sa.Column("misc_discord_webhook_url", sa.String(), nullable=False, server_default="None"),
            sa.Column("misc_discord_webhook_name", sa.String(length=255), nullable=False, server_default="None"),
            sa.Column("misc_hide_category", sa.String(length=16), nullable=False, server_default="False"),
            sa.Column("misc_hide_position", sa.String(length=16), nullable=False, server_default="False"),
            sa.Column("misc_profit_day", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("misc_profit_week", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("misc_profit_month", sa.Integer(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id"),
        )
        bind.execute(
            sa.text(
                f"""
                INSERT INTO storage_settings_new (
                    id,
                    status_work,
                    status_refill,
                    status_buy,
                    notification_refill,
                    notification_buy,
                    misc_faq,
                    misc_support,
                    misc_bot,
                    misc_hosting_text,
                    misc_token_telegraph,
                    misc_discord_webhook_url,
                    misc_discord_webhook_name,
                    misc_hide_category,
                    misc_hide_position,
                    misc_profit_day,
                    misc_profit_week,
                    misc_profit_month
                )
                SELECT
                    1,
                    {_copy_expr("storage_settings", "status_work", "True")},
                    {_copy_expr("storage_settings", "status_refill", "False")},
                    {_copy_expr("storage_settings", "status_buy", "False")},
                    {_copy_expr("storage_settings", "notification_refill", "True")},
                    {_copy_expr("storage_settings", "notification_buy", "False")},
                    {_copy_expr("storage_settings", "misc_faq", "None")},
                    {_copy_expr("storage_settings", "misc_support", "None")},
                    {_copy_expr("storage_settings", "misc_bot", "None")},
                    {_copy_expr("storage_settings", "misc_hosting_text", "telegraph")},
                    {_copy_expr("storage_settings", "misc_token_telegraph", "None")},
                    {_copy_expr("storage_settings", "misc_discord_webhook_url", "None")},
                    {_copy_expr("storage_settings", "misc_discord_webhook_name", "None")},
                    {_copy_expr("storage_settings", "misc_hide_category", "False")},
                    {_copy_expr("storage_settings", "misc_hide_position", "False")},
                    {_copy_int_expr("storage_settings", "misc_profit_day")},
                    {_copy_int_expr("storage_settings", "misc_profit_week")},
                    {_copy_int_expr("storage_settings", "misc_profit_month")}
                FROM storage_settings
                LIMIT 1
                """
            )
        )
        bind.execute(sa.text("DROP TABLE storage_settings"))
        bind.execute(sa.text("ALTER TABLE storage_settings_new RENAME TO storage_settings"))

    bind.execute(
        sa.text(
            """
            INSERT INTO storage_settings (id)
            SELECT 1
            WHERE NOT EXISTS (SELECT 1 FROM storage_settings WHERE id = 1)
            """
        )
    )
    for column, default in (
            ("status_work", "True"),
            ("status_refill", "False"),
            ("status_buy", "False"),
            ("notification_refill", "True"),
            ("notification_buy", "False"),
            ("misc_hide_category", "False"),
            ("misc_hide_position", "False"),
    ):
        _normalize_boolean_text("storage_settings", column, default)

    _create_index("ix_storage_settings_id", "storage_settings", "id", unique=True)


# Создание или правка таблицы платежей
def _ensure_payments() -> None:
    bind = op.get_bind()

    if not _table_exists("storage_payments"):
        op.create_table(
            "storage_payments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("cryptobot_token", sa.String(), nullable=False, server_default="None"),
            sa.Column("yoomoney_token", sa.String(), nullable=False, server_default="None"),
            sa.Column("status_cryptobot", sa.String(length=16), nullable=False, server_default="False"),
            sa.Column("status_yoomoney", sa.String(length=16), nullable=False, server_default="False"),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        bind.execute(sa.text("DROP TABLE IF EXISTS storage_payments_new"))
        op.create_table(
            "storage_payments_new",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("cryptobot_token", sa.String(), nullable=False, server_default="None"),
            sa.Column("yoomoney_token", sa.String(), nullable=False, server_default="None"),
            sa.Column("status_cryptobot", sa.String(length=16), nullable=False, server_default="False"),
            sa.Column("status_yoomoney", sa.String(length=16), nullable=False, server_default="False"),
            sa.PrimaryKeyConstraint("id"),
        )
        bind.execute(
            sa.text(
                f"""
                INSERT INTO storage_payments_new (
                    id,
                    cryptobot_token,
                    yoomoney_token,
                    status_cryptobot,
                    status_yoomoney
                )
                SELECT
                    1,
                    {_copy_expr("storage_payments", "cryptobot_token", "None")},
                    {_copy_expr("storage_payments", "yoomoney_token", "None")},
                    {_copy_expr("storage_payments", "status_cryptobot", "False")},
                    {_copy_expr("storage_payments", "status_yoomoney", "False")}
                FROM storage_payments
                LIMIT 1
                """
            )
        )
        bind.execute(sa.text("DROP TABLE storage_payments"))
        bind.execute(sa.text("ALTER TABLE storage_payments_new RENAME TO storage_payments"))

    bind.execute(
        sa.text(
            """
            INSERT INTO storage_payments (id)
            SELECT 1
            WHERE NOT EXISTS (SELECT 1 FROM storage_payments WHERE id = 1)
            """
        )
    )
    _normalize_boolean_text("storage_payments", "status_cryptobot", "False")
    _normalize_boolean_text("storage_payments", "status_yoomoney", "False")
    _create_index("ix_storage_payments_id", "storage_payments", "id", unique=True)


# Создание или правка таблицы категорий
def _ensure_category() -> None:
    if not _table_exists("storage_category"):
        op.create_table(
            "storage_category",
            sa.Column("increment", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("category_id", sa.BigInteger(), nullable=False),
            sa.Column("category_name", sa.String(length=255), nullable=False),
            sa.Column("category_unix", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("increment"),
        )
    else:
        _add_column("storage_category", "category_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_category", "category_name", "TEXT NOT NULL DEFAULT ''")
        _add_column("storage_category", "category_unix", "INTEGER NOT NULL DEFAULT 0")

    _create_index("ix_storage_category_category_id", "storage_category", "category_id")


# Создание или правка таблицы позиций
def _ensure_position() -> None:
    if not _table_exists("storage_position"):
        op.create_table(
            "storage_position",
            sa.Column("increment", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("category_id", sa.BigInteger(), nullable=False),
            sa.Column("position_id", sa.BigInteger(), nullable=False),
            sa.Column("position_name", sa.String(length=255), nullable=False),
            sa.Column("position_price", sa.Float(), nullable=False, server_default="0"),
            sa.Column("position_desc", sa.Text(), nullable=False, server_default="None"),
            sa.Column("position_photo", sa.Text(), nullable=False, server_default="None"),
            sa.Column("position_unix", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("increment"),
        )
    else:
        _add_column("storage_position", "category_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_position", "position_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_position", "position_name", "TEXT NOT NULL DEFAULT ''")
        _add_column("storage_position", "position_price", "REAL NOT NULL DEFAULT 0")
        _add_column("storage_position", "position_desc", "TEXT NOT NULL DEFAULT 'None'")
        _add_column("storage_position", "position_photo", "TEXT NOT NULL DEFAULT 'None'")
        _add_column("storage_position", "position_unix", "INTEGER NOT NULL DEFAULT 0")

    _create_index("ix_storage_position_category_id", "storage_position", "category_id")
    _create_index("ix_storage_position_position_id", "storage_position", "position_id")


# Создание или правка таблицы товаров
def _ensure_item() -> None:
    if not _table_exists("storage_item"):
        op.create_table(
            "storage_item",
            sa.Column("increment", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("category_id", sa.BigInteger(), nullable=False),
            sa.Column("position_id", sa.BigInteger(), nullable=False),
            sa.Column("item_id", sa.BigInteger(), nullable=False),
            sa.Column("item_unix", sa.Integer(), nullable=False),
            sa.Column("item_data", sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint("increment"),
        )
    else:
        _add_column("storage_item", "user_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_item", "category_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_item", "position_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_item", "item_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_item", "item_unix", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_item", "item_data", "TEXT NOT NULL DEFAULT ''")

    _create_index("ix_storage_item_user_id", "storage_item", "user_id")
    _create_index("ix_storage_item_category_id", "storage_item", "category_id")
    _create_index("ix_storage_item_position_id", "storage_item", "position_id")
    _create_index("ix_storage_item_item_id", "storage_item", "item_id")


# Создание или правка таблицы покупок
def _ensure_purchases() -> None:
    if not _table_exists("storage_purchases"):
        op.create_table(
            "storage_purchases",
            sa.Column("increment", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("user_balance_before", sa.Float(), nullable=False, server_default="0"),
            sa.Column("user_balance_after", sa.Float(), nullable=False, server_default="0"),
            sa.Column("purchase_receipt", sa.BigInteger(), nullable=False),
            sa.Column("purchase_data", sa.Text(), nullable=False),
            sa.Column("purchase_count", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("purchase_price", sa.Float(), nullable=False, server_default="0"),
            sa.Column("purchase_price_one", sa.Float(), nullable=False, server_default="0"),
            sa.Column("purchase_position_id", sa.BigInteger(), nullable=False),
            sa.Column("purchase_position_name", sa.String(length=255), nullable=False),
            sa.Column("purchase_category_id", sa.BigInteger(), nullable=False),
            sa.Column("purchase_category_name", sa.String(length=255), nullable=False),
            sa.Column("purchase_unix", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("increment"),
        )
    else:
        _add_column("storage_purchases", "user_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_purchases", "user_balance_before", "REAL NOT NULL DEFAULT 0")
        _add_column("storage_purchases", "user_balance_after", "REAL NOT NULL DEFAULT 0")
        _add_column("storage_purchases", "purchase_receipt", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_purchases", "purchase_data", "TEXT NOT NULL DEFAULT ''")
        _add_column("storage_purchases", "purchase_count", "INTEGER NOT NULL DEFAULT 1")
        _add_column("storage_purchases", "purchase_price", "REAL NOT NULL DEFAULT 0")
        _add_column("storage_purchases", "purchase_price_one", "REAL NOT NULL DEFAULT 0")
        _add_column("storage_purchases", "purchase_position_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_purchases", "purchase_position_name", "TEXT NOT NULL DEFAULT ''")
        _add_column("storage_purchases", "purchase_category_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_purchases", "purchase_category_name", "TEXT NOT NULL DEFAULT ''")
        _add_column("storage_purchases", "purchase_unix", "INTEGER NOT NULL DEFAULT 0")

    _create_index("ix_storage_purchases_user_id", "storage_purchases", "user_id")
    _create_index("ix_storage_purchases_purchase_receipt", "storage_purchases", "purchase_receipt")
    _create_index("ix_storage_purchases_purchase_position_id", "storage_purchases", "purchase_position_id")
    _create_index("ix_storage_purchases_purchase_category_id", "storage_purchases", "purchase_category_id")


# Создание или правка таблицы пополнений
def _ensure_refill() -> None:
    if not _table_exists("storage_refill"):
        op.create_table(
            "storage_refill",
            sa.Column("increment", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("refill_receipt", sa.BigInteger(), nullable=False),
            sa.Column("refill_comment", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("refill_amount", sa.Float(), nullable=False, server_default="0"),
            sa.Column("refill_method", sa.String(length=64), nullable=False),
            sa.Column("refill_unix", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("increment"),
        )
    else:
        _add_column("storage_refill", "user_id", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_refill", "refill_receipt", "INTEGER NOT NULL DEFAULT 0")
        _add_column("storage_refill", "refill_comment", "TEXT NOT NULL DEFAULT ''")
        _add_column("storage_refill", "refill_amount", "REAL NOT NULL DEFAULT 0")
        _add_column("storage_refill", "refill_method", "TEXT NOT NULL DEFAULT ''")
        _add_column("storage_refill", "refill_unix", "INTEGER NOT NULL DEFAULT 0")

    _create_index("ix_storage_refill_user_id", "storage_refill", "user_id")
    _create_index("ix_storage_refill_refill_receipt", "storage_refill", "refill_receipt")


# Применение начальной схемы магазина
def upgrade() -> None:
    _ensure_users()
    _ensure_settings()
    _ensure_payments()
    _ensure_category()
    _ensure_position()
    _ensure_item()
    _ensure_purchases()
    _ensure_refill()


# Откат начальной схемы магазина
def downgrade() -> None:
    op.drop_table("storage_refill")
    op.drop_table("storage_purchases")
    op.drop_table("storage_item")
    op.drop_table("storage_position")
    op.drop_table("storage_category")
    op.drop_table("storage_payments")
    op.drop_table("storage_settings")
    op.drop_table("storage_users")
