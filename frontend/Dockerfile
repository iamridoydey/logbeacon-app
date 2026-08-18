# ==========================================
# STAGE 1: Builder
# ==========================================
FROM node:slim AS builder

WORKDIR /app

# Copy package files first to leverage Docker layer caching
COPY package*.json .

# Install ALL dependencies here — including devDependencies —
# because tailwindcss/postcss (needed for build:css) live there
RUN npm ci

# Copy the rest of the source
COPY . .

RUN npm run build:css


# ==========================================
# STAGE 2: Runner
# ==========================================
FROM node:slim AS runner

WORKDIR /app

# Create non-root system user for improved security
RUN useradd --create-home logbeacon

# Install ONLY production dependencies here — separate, fresh install
COPY package*.json .
RUN npm ci --omit=dev

# Copy the application code + the already-built CSS from the builder stage
COPY --chown=logbeacon:logbeacon --from=builder /app/src ./src
COPY --chown=logbeacon:logbeacon --from=builder /app/views ./views
COPY --chown=logbeacon:logbeacon --from=builder /app/public ./public

# Switch to non-root user
USER logbeacon

EXPOSE 3000

CMD ["node", "src/app.js"]