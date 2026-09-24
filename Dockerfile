# Multi-stage production-oriented Dockerfile for Namma Clinic Backend
FROM python:3.11-slim as base

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    PORT=8000

# Install system dependencies (libpq-dev for PostgreSQL client compatibility)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and group
RUN groupadd -r appgroup && useradd -r -u 1001 -g appgroup appuser

WORKDIR /app

# Install Python dependencies deterministically
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application source code
COPY backend/ /app/backend/

# Create media, staticfiles, and logs directories and grant ownership to non-root user
RUN mkdir -p /app/backend/staticfiles /app/backend/media && \
    chown -R appuser:appgroup /app

# Switch to non-root runtime user
USER appuser

WORKDIR /app/backend

# Expose default HTTP WSGI port
EXPOSE 8000

# Health check using the lightweight /healthz endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Production WSGI startup command with Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
