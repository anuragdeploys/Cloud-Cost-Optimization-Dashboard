FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data
COPY scripts ./scripts

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/database /app/logs \
    && chown -R appuser:appuser /app/database /app/logs

EXPOSE 5000

USER appuser

CMD ["python", "-m", "app.api"]
