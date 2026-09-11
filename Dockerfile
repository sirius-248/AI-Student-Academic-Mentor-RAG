# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    FAISS_INDEX_PATH=/app/data/index.faiss \
    FAISS_METADATA_PATH=/app/data/metadata.pkl \
    UPLOAD_DIR=/app/data/uploads

WORKDIR /app

RUN mkdir -p /app/data/uploads

COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
