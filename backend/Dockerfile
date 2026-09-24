# Multi-stage build for Python backend
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Trust the Russian Ministry of Digital Development CA chain used by
# platform-api2.max.ru (see https://dev.max.ru/docs-api). Without this,
# outbound HTTPS calls to the real MAX Bot API fail with
# SSLCertVerificationError: unable to get local issuer certificate.
COPY deploy/ca-certs/*.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

# Python's `requests` ignores the OS trust store and only trusts its
# vendored certifi bundle unless told otherwise - point it at the system
# store we just extended above.
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Copy requirements first for better caching
COPY requirements.txt .

# Development stage
FROM base as development
ARG BUILD_COMMIT_SHA=unknown
ENV BUILD_COMMIT_SHA=${BUILD_COMMIT_SHA}
LABEL org.opencontainers.image.revision=${BUILD_COMMIT_SHA}

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir debugpy watchdog

COPY . .
RUN find . -type f \
      ! -path './.venv/*' \
      ! -path '*/__pycache__/*' \
      ! -path '*/.pytest_cache/*' \
      ! -path './media/*' \
      ! -path './staticfiles/*' \
      ! -name '.env' \
      ! -name 'db.sqlite3*' \
      ! -name '*.pyc' \
      -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d ' ' -f 1 > /app/BUILD_FINGERPRINT

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Builder stage for production
FROM base as builder

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Production stage
FROM python:3.11-slim as production
ARG BUILD_COMMIT_SHA=unknown
ENV BUILD_COMMIT_SHA=${BUILD_COMMIT_SHA}
LABEL org.opencontainers.image.revision=${BUILD_COMMIT_SHA}

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Trust the Russian Ministry of Digital Development CA chain used by
# platform-api2.max.ru (see https://dev.max.ru/docs-api). Without this,
# outbound HTTPS calls to the real MAX Bot API fail with
# SSLCertVerificationError: unable to get local issuer certificate.
COPY deploy/ca-certs/*.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

# Python's `requests` ignores the OS trust store and only trusts its
# vendored certifi bundle unless told otherwise - point it at the system
# store we just extended above.
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Copy Python dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .
RUN find . -type f \
      ! -path './.venv/*' \
      ! -path '*/__pycache__/*' \
      ! -path '*/.pytest_cache/*' \
      ! -path './media/*' \
      ! -path './staticfiles/*' \
      ! -name '.env' \
      ! -name 'db.sqlite3*' \
      ! -name '*.pyc' \
      -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d ' ' -f 1 > /app/BUILD_FINGERPRINT

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
