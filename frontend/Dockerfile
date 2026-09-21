# =============================================================
# STAGE 1 — BUILD
# =============================================================
FROM node:22-slim AS builder

WORKDIR /app

# Copy dependency manifests first for Docker layer caching
COPY package.json package-lock.json ./

# Install dependencies exactly from package-lock.json
RUN npm ci

# Your package.json currently uses @tailwindcss/cli through npx
# but does not declare it as a dependency.
# Install a pinned CLI version only in the build stage.
RUN npm install --no-save @tailwindcss/cli@4.3.3

# Copy application source
COPY src ./src
COPY views ./views
COPY public ./public
COPY postcss.config.js ./

# Build Tailwind CSS ONCE.
# Do not use your build:css script here because it currently uses --watch.
RUN npx @tailwindcss/cli \
    -i ./public/css/input.css \
    -o ./public/css/style.css \
    --minify


# =============================================================
# STAGE 2 — PRODUCTION RUNTIME
# =============================================================
FROM node:22-slim AS runner

ENV NODE_ENV=production

WORKDIR /app

# Create an unprivileged application user
RUN groupadd --system logbeacon \
    && useradd \
       --system \
       --gid logbeacon \
       --create-home \
       logbeacon

# Install production dependencies only
COPY package.json package-lock.json ./

RUN npm ci --omit=dev \
    && npm cache clean --force

# Copy only what the application needs at runtime
COPY --from=builder --chown=logbeacon:logbeacon /app/src ./src
COPY --from=builder --chown=logbeacon:logbeacon /app/views ./views
COPY --from=builder --chown=logbeacon:logbeacon /app/public ./public

USER logbeacon

EXPOSE 3000

CMD ["node", "src/app.js"]