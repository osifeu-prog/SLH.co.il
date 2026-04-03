FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    aiogram==3.4.0 \
    fastapi==0.115.5 \
    uvicorn[standard]==0.32.0 \
    python-dotenv==1.0.1

COPY . .

CMD ["uvicorn", "app:fastapi_app", "--host", "0.0.0.0", "--port", "8080"]
