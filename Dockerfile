FROM python:3.11-slim

# ???? UTF-8
ENV PYTHONUTF8=1
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

WORKDIR /app
COPY bot.py /app/

RUN pip install --no-cache-dir aiogram asyncpg python-dotenv httpx groq google-generativeai

CMD ["python", "bot.py"]
