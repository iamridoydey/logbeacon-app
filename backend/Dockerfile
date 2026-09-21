# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Create virtual environment
RUN python -m venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies
COPY requirements-prod.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt


# ==========================================
# STAGE 2: Runner
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Create non-root user
RUN useradd --create-home logbeacon

# Copy application source first
COPY --chown=logbeacon:logbeacon . .

# Copy Docker-built virtual environment LAST
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

USER logbeacon

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]