# Telegram Autoshop Bot by Djimbo

Telegram bot на `aiogram 3` для магазина с категориями, позициями, товарами, покупками, пополнениями и админкой.

## Быстрый запуск

1. Установи Python `3.11+`.
2. Поставь зависимости:

```bash
python3.11 -m pip install -r requirements.txt
```

3. Создай `.env` по примеру:

```bash
cp .env.example .env
```

4. Заполни минимум:

```env
BOT_TOKEN=
BOT_ADMIN_IDS=
YOOMONEY_CLIENT_ID=
```

Конфигурация читается только из `.env` или переменных окружения.

5. Примени миграции:

```bash
python3 migrate.py up
```

6. Запусти бота:

```bash
python3 main.py
```

## Миграции

Основные команды:

```bash
python3 migrate.py status
python3 migrate.py up
python3 migrate.py down
python3 migrate.py auto "change description"
```

Схема БД теперь живет в `migrations/`, модели — в `tgbot/database/db_*.py`.

## Docker

```bash
docker compose up -d --build
```

Контейнер сам применяет миграции перед запуском.
