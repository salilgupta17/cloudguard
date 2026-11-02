FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including PostgreSQL client tools for dump/restore operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY pytest.ini /app/pytest.ini

ENV PYTHONPATH=/app
ENV EXECUTION_MODE=LOCAL

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
