# LogBeacon — Application

LogBeacon helps developers understand error logs and stack traces. Submit an error through the web interface or REST API, and the Flask backend asks a Groq-hosted language model for an explanation and a practical fix. Each analysis is saved with its input/output token counts, response latency, and estimated cost so users can review their history and usage.

This repository contains the Express/EJS frontend, Flask API, database migrations, background-job code, container definitions, and application CI workflows.

## The LogBeacon repositories

| Repository | Responsibility |
| --- | --- |
| **[logbeacon-app](https://github.com/iamridoydey/logbeacon-app)** | Application code, tests, Docker images, and image publishing to ECR. |
| [logbeacon-aws-infra](https://github.com/iamridoydey/logbeacon-aws-infra) | Terraform and Ansible for AWS networking, EKS, ECR, IAM, secrets, and the admin host. |
| [logbeacon-aws-k8s](https://github.com/iamridoydey/logbeacon-aws-k8s) | Argo CD applications, Helm values, Kubernetes resources, and canary deployments. |

**For local application development, start here. AWS and Kubernetes are not required.** For an AWS deployment, provision the infrastructure, publish the application images, and then follow the Kubernetes repository's bootstrap instructions.

## Contents

- [Features and architecture](#features-and-architecture)
- [Prerequisites](#prerequisites)
- [Run locally with Docker Compose](#run-locally-with-docker-compose)
- [Run the application directly on your machine](#run-the-application-directly-on-your-machine)
- [Configuration](#configuration)
- [API](#api)
- [Background cleanup and email](#background-cleanup-and-email)
- [Tests and development commands](#tests-and-development-commands)
- [CI and image releases](#ci-and-image-releases)
- [Troubleshooting and current limitations](#troubleshooting-and-current-limitations)

## Features and architecture

- Account registration and password-based sign-in.
- A personal API key returned during registration; the database stores its hash.
- Error analysis through Groq, with Markdown solutions displayed in the web UI.
- A history/dashboard with saved errors, solutions, token usage, and estimated cost.
- PostgreSQL persistence through SQLAlchemy and Alembic migrations.
- Redis/RQ job code for emailing expired logs and removing them after successful delivery.

```mermaid
flowchart TD
    Browser[Browser] --> Frontend[Express and EJS]
    Frontend --> API[Flask API]
    Client[API client] --> API
    API --> Groq[Groq]
    API --> DB[PostgreSQL]
    Cleanup[Cleanup command] --> DB
    Cleanup --> Redis[Redis queue]
    Redis --> Worker[RQ worker]
    Worker --> SMTP[SMTP server]
    Worker --> DB
```

Analysis requests call Groq and save the log and metrics synchronously. RQ is used by the cleanup/email code; it does not process the main analysis request. Cleanup needs a separately started worker and a scheduled invocation.

| Component | Implementation |
| --- | --- |
| Frontend | Node.js 24, Express 5, EJS, Tailwind CSS 4, `express-session`, `marked`. |
| Backend | Python, Flask, Flask-SQLAlchemy, Groq SDK, Gunicorn in the runtime image. |
| Data | PostgreSQL; Alembic owns schema migrations. |
| Background jobs | Redis and RQ, queue name `logbeacon`. |
| Validation | Node test runner, ESLint, pytest, Ruff, Trivy, Checkov, SonarQube. |

### Repository layout

| Path | Purpose |
| --- | --- |
| `frontend/src/` | Express routes, configuration, and Flask API client. |
| `frontend/views/` | EJS layouts and pages. |
| `frontend/public/` | Browser JavaScript and Tailwind input/output CSS. |
| `frontend/tests/` | Frontend API-client tests. |
| `backend/app/routes/` | Authentication, analysis, log, and health endpoints. |
| `backend/app/services/` | Business logic, Groq integration, and cost calculation. |
| `backend/app/repositories/` | Database access. |
| `backend/app/models/` | `User`, `Log`, and `Analysis` models. |
| `backend/app/jobs/` | Cleanup and expiry-email jobs. |
| `backend/migrations/` | Alembic schema migrations. |
| `backend/tests/` | Unit and integration tests. |
| `compose/` | Shared Compose services and development/production definitions. |
| `.github/workflows/` | Pull-request checks and main-branch image releases. |

## Prerequisites

- Git, Docker Engine/Desktop, and the Docker Compose plugin.
- A Groq API key and a model ID available to that account.
- Available local ports `3000`, `5000`, `5434` and `6379` for the Compose setup.
- SMTP credentials if you want to exercise expiry emails.

For host-based development, also install Node.js 24, npm, and Python with `venv` support. The Dockerfile uses Python 3.11; backend CI uses Python 3.12. Dependencies are pinned in `backend/requirements*.txt` and the frontend lockfile.

## Run locally with Docker Compose

### 1. Clone and configure

```bash
git clone https://github.com/iamridoydey/logbeacon-app.git
cd logbeacon-app
cp compose/.env.example compose/.env
```

Edit `compose/.env`. Replace the secret placeholders and Groq credentials. A development example is:

```dotenv
PORT=3000
SESSION_SECRET=replace-with-a-random-session-secret
SECRET_KEY=replace-with-a-different-random-flask-secret
POSTGRES_USER=logbeacon
POSTGRES_PASSWORD=replace-with-a-local-db-password
POSTGRES_DB=logbeacon_db
SQLALCHEMY_TRACK_MODIFICATIONS=False
GROQ_API_KEY=replace-with-your-groq-api-key
GROQ_MODEL=replace-with-a-model-id-available-to-your-account
LOG_RETENTION_DAYS=7
MAX_ERROR_LENGTH=2000
PRICE_PER_MILLION_TOKENS=0.05
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=replace-with-your-smtp-user
SMTP_PASSWORD=replace-with-your-smtp-password
FROM_EMAIL=you@example.com
```

### 2. Create a local Compose override

The checked-in `compose.dev.yaml` uses `include` while redefining the same services. Compose includes do not merge conflicting service definitions. For this snapshot, create the following **new local file**, `compose/compose.local.yaml`, and use it with the shared base file instead:

```yaml
services:
  frontend:
    build:
      context: ../frontend
      target: builder
    command: npm run dev
    volumes:
      - ../frontend:/app
      - /app/node_modules

  backend:
    build:
      context: ../backend
      target: builder
    command: python -m flask --app wsgi:app run --host=0.0.0.0 --debug
    environment:
      LOG_RETENTION_DAYS: ${LOG_RETENTION_DAYS:-7}
      ALLOWED_ORIGINS: http://localhost:3000
    volumes:
      - ../backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

networks:
  logbeacon:
    driver: bridge
```

This is a development configuration. It mounts source code for reloads and intentionally uses development servers. The backend builder's virtual environment is at `/opt/venv`; mounting `/app` does not hide it.

### 3. Build, migrate, and start

Run from the repository root in Bash. Define this helper in each terminal where you use the following Compose commands:

```bash
dc() {
  docker compose --env-file compose/.env \
    -f compose/compose.app.yaml \
    -f compose/compose.local.yaml "$@"
}

dc config --quiet
dc build
dc up -d --wait db redis
dc run --rm --no-deps backend alembic upgrade head
dc run --rm --no-deps frontend npm run build:css
dc up -d backend frontend
dc ps
```

The development backend command does not run migrations automatically, so the migration step is required for a new database.

### 4. Use the application

Open [http://localhost:3000](http://localhost:3000), register at `/auth/register`, save your API key, and then sign in at `/auth/signin`. Submit a short error at `/analyze` and inspect the saved entry at `/dashboard`.

Check database connectivity through the API:

```bash
curl --fail http://localhost:5000/health
```

Expected response:

```json
{"database":"connected","status":"ok"}
```

This endpoint checks PostgreSQL connectivity. It does not test Groq, SMTP, Redis, or whether migrations have created the application tables.

### 5. Develop and stop

```bash
dc logs -f backend frontend
```

For Tailwind changes, run `dc exec frontend npm run watch:css` in another terminal. Source reloads do not rebuild CSS automatically.

```bash
dc down
```

Named PostgreSQL and Redis volumes remain after `down`. Use `dc down --volumes` only when you intend to delete local database and queue data.

## Run the application directly on your machine

Use this route if you prefer Node/Python processes in your editor. It is an alternative to the full Compose setup; do not run both frontends/backends on the same ports.

### Start local data services

```bash
docker run -d --name logbeacon-local-postgres \
  -e POSTGRES_USER=logbeacon \
  -e POSTGRES_PASSWORD=logbeacon \
  -e POSTGRES_DB=logbeacon_db \
  -p 127.0.0.1:5432:5432 \
  -v logbeacon-local-pgdata:/var/lib/postgresql/data \
  postgres:17-alpine

docker run -d --name logbeacon-local-redis \
  -p 127.0.0.1:6379:6379 redis:8.0-alpine

docker exec logbeacon-local-postgres pg_isready -U logbeacon -d logbeacon_db
```

Wait until `pg_isready` reports that PostgreSQL accepts connections. The credentials above are for a local development database.

### Start Flask

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env`: replace every descriptive placeholder, set the Groq credentials and secrets, and use these local connection/configuration values:

```dotenv
DATABASE_URL=postgresql://logbeacon:logbeacon@localhost:5432/logbeacon_db
REDIS_URL=redis://localhost:6379/0
ALLOWED_ORIGINS=http://localhost:3000
SQLALCHEMY_TRACK_MODIFICATIONS=False
LOG_RETENTION_DAYS=7
MAX_ERROR_LENGTH=2000
PRICE_PER_MILLION_TOKENS=0.05
SMTP_PORT=587
```

The example file contains explanatory strings in numeric fields; those must become valid numbers.

```bash
alembic upgrade head
python -m flask --app wsgi:app run --debug --host=127.0.0.1 --port=5000
```

### Start Express

In another terminal, from the repository root:

```bash
cd frontend
npm ci
```

Create `frontend/.env` with the following contents; the checked-in frontend example is empty:

```dotenv
PORT=3000
FLASK_API_URL=http://localhost:5000
SESSION_SECRET=replace-with-a-random-session-secret
```

```bash
npm run build:css
npm run dev
```

Run `npm run watch:css` in a third terminal when editing Tailwind styles. Use `docker stop logbeacon-local-postgres logbeacon-local-redis` to stop the data services, and `docker start` with the same names to resume them.

## Configuration

Backend variables are read by `backend/app/config.py`; frontend variables are read by `frontend/src/config.js`.

| Variable | Purpose / default |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy PostgreSQL connection URL; required. |
| `REDIS_URL` | Redis connection URL for cleanup/RQ. |
| `SECRET_KEY` | Flask session-signing secret; required for sign-in. |
| `GROQ_API_KEY` | Groq credential; required when importing the Groq client. |
| `GROQ_MODEL` | Model ID used for real analysis requests. |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins for `/analyze`; avoid spaces around entries. |
| `LOG_RETENTION_DAYS` | Expiry age used by cleanup; defaults to `7`. It does not schedule cleanup. |
| `MAX_ERROR_LENGTH` | Maximum error text length in characters; defaults to `500`. |
| `PRICE_PER_MILLION_TOKENS` | Single rate applied to combined input/output tokens; defaults to `0.05`. |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | Passed through from the environment as a string in the current code; boolean parsing is not implemented. |
| `SMTP_HOST`, `SMTP_PORT` | SMTP endpoint; port defaults to `587`. The job uses STARTTLS. |
| `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL` | SMTP login and sender for expiry emails. |
| `PORT` | Express port; defaults to `3000`. Keep `3000` with the existing Compose port mapping. |
| `FLASK_API_URL` | Backend URL as seen by Express; defaults to `http://localhost:5000`. Compose sets `http://backend:5000`. |
| `SESSION_SECRET` | Express session-signing secret. |

Cost is an estimate using one configured rate, not a provider billing record or a model-specific input/output price calculation. Error text is sent to Groq; remove credentials and sensitive log content before submission.

## API

Local API base URL: `http://localhost:5000`.

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | None | PostgreSQL connectivity check. |
| `POST` | `/auth/register` | None | Register using `username`, `email`, `password` |
| `POST` | `/auth/signin` | None | Sign in with `username` and `password`; sets a Flask session cookie. |
| `POST` | `/auth/signout` | Session if present | Remove the user ID from the Flask session. |
| `POST` | `/analyze` | Flask session **or** Bearer API key | Analyze `{ "error_log": "..." }`; returns HTTP `201` on success. |
| `GET` | `/log` | Flask session | Return the signed-in user's analyzed entries and totals. |
| `POST` | `/log` | Flask session | Save an error/solution pair supplied by the caller. |

Example using the API key returned at registration:


The result includes `id`, `error_solution`, `input_tokens`, `output_tokens`, `latency_ms`, and `cost`. Bearer authentication currently applies to `/analyze`; `/log` requires the session cookie. Registration does not sign the user in automatically.

## Background cleanup and email

The repository provides job functions but no Compose worker service or recurring scheduler. The basic web application can run without them.

With the Compose helper defined above, start a worker in a separate terminal:

```bash
dc run --rm --no-deps backend rq worker --url redis://redis:6379/0 logbeacon
```

Manually enqueue expired logs from another terminal:

```bash
dc run --rm --no-deps backend python -c \
  'from app.jobs.cleanup_logs import run_cleanup; run_cleanup()'
```

For host-based development, run the equivalent commands from `backend/` with the virtual environment active, using `redis://localhost:6379/0` for the worker.

To automate expiry, arrange a recurring cleanup invocation and keep a worker running. The cleanup command selects logs older than `LOG_RETENTION_DAYS`; the worker emails each log and then deletes it. If SMTP delivery raises an error, deletion does not proceed. Do not repeatedly enqueue the same backlog without checking the queue: the cleanup function does not deduplicate outstanding jobs.

## Tests and development commands

Frontend, from `frontend/`:

```bash
npm ci
npm test
npm run lint
npm run build:css
```

Backend tests use a **hard-coded disposable database** in `backend/tests/conftest.py`: `postgresql://logbeacon:logbeacon@localhost/logbeacon_dev_test`. Fixtures create and drop application tables. Use that dedicated database, never a database containing data you want to keep.

If you started the host-development PostgreSQL container above, create the test database once:

```bash
docker exec logbeacon-local-postgres \
  createdb -U logbeacon logbeacon_dev_test
```

Then, from `backend/` with its virtual environment active:

```bash
python -m pip install -r requirements.txt
GROQ_API_KEY=test-groq-api-key \
GROQ_MODEL=test-groq-model \
REDIS_URL=redis://localhost:6379/0 \
python -m pytest
ruff check .
```

The tests mock the external operations they cover; they are not an end-to-end validation of Groq or SMTP. Setting `DATABASE_URL` alone does not change the fixture's hard-coded test database.

# CI and image releases
## Logbeacon App Ci on PR
![Logbeacon App Ci on PR](diagrams/ci/logbeacon-app-ci-pr.png)


## Logbeacon App Ci on Merge
![Logbeacon App Ci on Merge](diagrams/ci/logbeacon-app-ci-merge.png)


| Workflow | Trigger | Behavior |
| --- | --- | --- |
| `app-ci-pr.yaml` | Pull request to `main`, or manual dispatch | Frontend/backend tests and linting; Trivy filesystem scans; Checkov Dockerfile scans; SonarQube analysis/quality gates; build and scan both images. |
| `app-ci-merge.yaml` | Push to `main`, or manual dispatch | Build Linux/AMD64 images, fail on critical image findings, and push short-commit-SHA tags to ECR. Uses the `app-release-production` environment. |

Current workflows do not define separate `dev`/`qa` pipelines and do not run a Docker Compose integration stack. The release workflow does not repeat all PR tests; protect `main` with the required PR checks.

Configure the following for AWS-backed CI:

| Setting | Location / value |
| --- | --- |
| `AWS_REGION` | GitHub Actions variable, matching the AWS deployment. |
| `AWS_ACCOUNT_ID` | GitHub Actions secret. |
| `logbeacon-app-ci-role` | IAM role created by the infrastructure bootstrap root; trust must match the workflow's actual OIDC subject. |
| `app-release-production` | GitHub environment used for releases; configure deployment rules as needed. |
| `sonarqube-ci-cred` | AWS Secrets Manager JSON containing `SONAR_HOST_URL` and `SONAR_TOKEN`. |

The IAM role needs ECR access and access to the SonarQube secret, including `kms:Decrypt` for its customer-managed encryption key. The checked-in app CI role has the Secrets Manager read policy but does not attach a corresponding KMS decrypt policy; account administrators must resolve that before using the encrypted secret.

Images are published to `<account>.dkr.ecr.<region>.amazonaws.com/logbeacon/frontend:<short-sha>` and the equivalent `logbeacon/backend` repository. The application pipeline does not directly deploy Kubernetes. Argo CD Image Updater is configured in the Kubernetes repository to propose image-tag changes through GitHub pull requests.

## Troubleshooting and current limitations

| Symptom / area | What to check |
| --- | --- |
| Table does not exist | Run `alembic upgrade head` against the same database used by the backend. |
| Analysis fails | Check the Groq key, model ID, quota, outbound connectivity, and `MAX_ERROR_LENGTH`. |
| Database authentication fails after editing `.env` | Existing PostgreSQL volumes retain their original credentials. Changing environment variables does not change an initialized database password. |
| Old logs remain | Run both cleanup and an RQ worker; set `LOG_RETENTION_DAYS`,  verify SMTP delivery. |

Before a public multi-replica deployment, address the current in-memory Express session store and `secure: false` cookie setting, remove the registration route's request-body logging, sanitize rendered model-generated Markdown, and review sign-out/session handling. These are visible implementation limitations, not features supplied by the deployment manifests.

## Contributing

Create a feature branch, make a focused change, run the relevant tests/lint/build commands, and open a pull request to `main`. Include migrations when changing the database schema and update configuration examples when adding environment variables. Keep credentials, `.env` files, and local data out of commits.
