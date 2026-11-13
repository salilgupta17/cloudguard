FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY cloudguard-api/requirements.txt ./requirements/api.txt
COPY validation-engine/requirements.txt ./requirements/validation.txt
COPY report-service/requirements.txt ./requirements/reports.txt
RUN pip install --no-cache-dir \
    -r requirements/api.txt \
    -r requirements/validation.txt \
    -r requirements/reports.txt \
    boto3

COPY cloudguard-api/app/ ./app/
COPY cloudguard-api/alembic/ ./alembic/
COPY cloudguard-api/alembic.ini .
COPY validation-engine/validation_engine/ ./validation_engine/
COPY report-service/report_service/ ./report_service/

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
