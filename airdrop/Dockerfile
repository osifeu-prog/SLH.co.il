FROM python:3.11-slim

WORKDIR /app

# התקן תלויות מערכת
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# העתק קבצים
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# צור תיקיות
RUN mkdir -p data templates

CMD ["python", "--version"]
