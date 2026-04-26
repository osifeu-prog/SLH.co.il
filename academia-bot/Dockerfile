FROM python:3.11-slim

WORKDIR /app

# Build context is the repo root (see docker-compose.yml academia-bot service).
# This lets us COPY both the bot code AND the shared/ helper modules.
COPY academia-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY academia-bot/ .
COPY shared/ /app/shared/

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/shared

CMD ["python", "bot.py"]
