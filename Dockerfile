FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN useradd --create-home --shell /usr/sbin/nologin bot

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=bot:bot . .
RUN mkdir -p /app/tgbot/data && chown -R bot:bot /app

USER bot

CMD ["sh", "-c", "python migrate.py up && python main.py"]
