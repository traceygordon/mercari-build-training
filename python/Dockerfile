FROM python:3-alpine

WORKDIR /app
RUN addgroup -S mercari && adduser -S trainee -G mercari

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY db/items.sql ./db/items.sql

RUN chown -R trainee:mercari /app
USER trainee

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]