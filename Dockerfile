# Use Python 3.11 official image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY python-api/requirements.txt .

# Install dependencies with increased timeout and retry
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=300 --retries 5 -r requirements.txt

# Copy application code
COPY python-api/ .

# Expose port
EXPOSE 5000

# Start command
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120"]
