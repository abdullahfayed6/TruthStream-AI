FROM python:3.11-slim

WORKDIR /app

COPY sink/requirements.txt /app/sink/requirements.txt
RUN pip install --no-cache-dir -r /app/sink/requirements.txt

COPY sink /app/sink

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "-m", "sink.mongo_sink"]
