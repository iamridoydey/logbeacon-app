# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

# Set the work directory
WORKDIR /app 

# Create a virtual environment
RUN python -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt .

# Upgrade and install all the dependencies without caching the index to keep the image small
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ==========================================
# STAGE 2: Runner
# ==========================================
FROM  python:3.11-slim AS runner

WORKDIR /app

# Create non root system user for improved security
RUN useradd --create-home logbeacon


# Copy the compiled virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy the application source code
COPY --chown=logbeacon:logbeacon . .

# Force the container to use copied virtual env
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root users
USER logbeacon

# Expose the application port
EXPOSE 5000

# Run the application using WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]