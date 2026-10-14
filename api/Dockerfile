FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code, models, reference data, and reports
COPY src/ ./src/
COPY api/ ./api/
COPY models/ ./models/
COPY data/reference/ ./data/reference/
COPY params.yaml .

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch uvicorn service
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
