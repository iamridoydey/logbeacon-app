# =============================================================
# STAGE 1 — BUILD PYTHON DEPENDENCIES
# =============================================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create an isolated virtual environment
RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies separately so this layer is cached
COPY requirements-prod.txt ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-prod.txt


# =============================================================
# STAGE 2 — PRODUCTION RUNTIME
# =============================================================
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Create non-root application user
RUN groupadd --system logbeacon \
    && useradd \
       --system \
       --gid logbeacon \
       --create-home \
       logbeacon

# Copy the already-built Python environment
COPY --from=builder /opt/venv /opt/venv

# Copy only backend application/runtime files
COPY --chown=logbeacon:logbeacon app ./app
COPY --chown=logbeacon:logbeacon migrations ./migrations
COPY --chown=logbeacon:logbeacon alembic.ini ./
COPY --chown=logbeacon:logbeacon wsgi.py ./

USER logbeacon

EXPOSE 5000

# Kubernetes should handle migrations separately or with an init/job.
# The application container itself only starts Gunicorn.
CMD ["gunicorn","--bind", "0.0.0.0:5000",  "--workers", "2","--threads", "2","--timeout", "120","--access-logfile", "-","--error-logfile", "-","wsgi:app"]