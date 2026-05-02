FROM python:3.11-slim

WORKDIR /app

COPY ingestion/requirements.txt /app/ingestion/requirements.txt
RUN pip install --no-cache-dir -r /app/ingestion/requirements.txt

COPY ingestion /app/ingestion

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "-m", "ingestion.newsapi_producer"]
