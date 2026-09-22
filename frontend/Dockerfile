# ==========================================
# STAGE 1: Builder
# ==========================================
FROM node:24-alpine3.24 AS builder

WORKDIR /app

# Support npm dependencies requiring native compilation
RUN apk add --no-cache python3 make g++

COPY package*.json ./

RUN npm ci

COPY . .

# Must finish and exit: do not use --watch
RUN npm run build:css


# ==========================================
# STAGE 2: Production dependencies
# ==========================================
FROM node:24-alpine3.24 AS production-deps

WORKDIR /app

RUN apk add --no-cache python3 make g++

COPY package*.json ./

RUN npm ci --omit=dev


# ==========================================
# STAGE 3: Runner
# ==========================================
FROM node:24-alpine3.24 AS runner

ENV NODE_ENV=production

WORKDIR /app

RUN addgroup -S -g 10001 logbeacon \
    && adduser -S -D -u 10001 -G logbeacon logbeacon

COPY --from=production-deps /app/node_modules ./node_modules
COPY --from=production-deps /app/package*.json ./

COPY --chown=logbeacon:logbeacon --from=builder /app/src ./src
COPY --chown=logbeacon:logbeacon --from=builder /app/views ./views
COPY --chown=logbeacon:logbeacon --from=builder /app/public ./public

USER logbeacon

EXPOSE 3000

CMD ["node", "src/app.js"]