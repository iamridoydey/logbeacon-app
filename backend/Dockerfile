# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.11-alpine3.24 AS builder

WORKDIR /app

# Build tools for common native Python dependencies
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    postgresql-dev

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements-prod.txt ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-prod.txt \
    && pip check


# ==========================================
# STAGE 2: Runner
# ==========================================
FROM python:3.11-alpine3.24 AS runner

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Runtime libraries and non-root user
RUN apk add --no-cache libpq libffi libstdc++ \
    && addgroup -S -g 10001 logbeacon \
    && adduser -S -D -u 10001 -G logbeacon logbeacon

COPY --from=builder /opt/venv /opt/venv

COPY --chown=logbeacon:logbeacon . .

USER logbeacon

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]