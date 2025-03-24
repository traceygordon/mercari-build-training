FROM python:3-alpine

WORKDIR /app
RUN addgroup -S mercari && adduser -S trainee -G mercari

# Install dependencies (layer 1)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of code (layer 2)
COPY main.py .
COPY db/items.sql ./db/items.sql

# Configure user (layer 3)
RUN chown -R trainee:mercari /app
USER trainee

# Run our backend
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
