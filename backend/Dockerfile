# Multi-stage build for Python backend
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Development stage
FROM base as development

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir debugpy watchdog

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Builder stage for production
FROM base as builder

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Production stage
FROM python:3.11-slim as production

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Health check endpoint should be added to Django app
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

CMD ["sh", "-c", "python manage.py migrate --noinput && if [ \"$AUTO_SEED_DEMO\" = \"true\" ]; then python manage.py seed_demo; fi && gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 config.wsgi:application"]
