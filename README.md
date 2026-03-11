# 🌐 Mindful Web Backend
*FastAPI backend for mindful internet tracking*

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-black)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-50%2B-green)]()
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)

> Production-ready FastAPI backend for authentication, event tracking, and analytics.

## 🔗 Project Links

| Component | Repository | Description |
|-----------|-----------|-------------|
| 🔌 **Extensions** | [mindful-web-extensions](https://github.com/Jaldsky/mindful-web-extensions) | Browser extensions (Chrome) |
| ⚙️ **Backend** | [mindful-web-backend](https://github.com/Jaldsky/mindful-web-backend) | FastAPI backend server |
| 🖥️ **Frontend** | [mindful-web-frontend](https://github.com/Jaldsky/mindful-web-frontend) | React dashboard and analytics |

---

## ✨ Key Features

- 🔐 **Authentication** — JWT tokens, email verification, anonymous sessions
- 📊 **Event Tracking** — Batch processing, PostgreSQL storage, optimized queries
- 📈 **Analytics** — Celery jobs for domain usage computation
- 📧 **Email Service** — SMTP integration with verification codes
- 👤 **User Management** — Profile, username/email updates
- 🐳 **Docker-Ready** — Complete orchestration with 6 services
- 🧪 **Well-Tested** — tests covering all services

---

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### 2. Environment Setup
Create `.env` file:
```bash
# Database
POSTGRES_USER=root
POSTGRES_PASSWORD=root
POSTGRES_DB=wmb

# Application
SECRET_KEY=$(openssl rand -hex 32)

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Deploy
```bash
# Build and start all services
poetry run invoke compose --build

# Check health
curl http://localhost:8000/api/v1/healthcheck
```

### 4. Access
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🛠️ Development

### Tech Stack
- **Backend**: Python 3.11+, FastAPI 0.115+, SQLAlchemy 2.0
- **Database**: PostgreSQL with Alembic migrations
- **Queue**: Celery 5.5+ + Redis 6.4+
- **Email**: aiosmtplib + Jinja2
- **Security**: bcrypt, python-jose (JWT)
- **Testing**: unittest

### Local Development
```bash
# Install dependencies
poetry install

# Start services
poetry run invoke compose "up db redis" -d
poetry run invoke migrate-apply --local
poetry run invoke dev

# Run tests
poetry run invoke tests

# Linting
poetry run invoke lint
poetry run invoke format
```

### Docker Services
| Service | Port | Description |
|---------|------|-------------|
| `app` | 8000 | FastAPI application |
| `db` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis cache/queue |
| `worker` | - | Celery worker |
| `beat` | - | Celery scheduler |
| `migrate` | - | Auto migrations |

---

## 📡 API Endpoints

### Authentication (`/api/v1/auth/`)
- `POST /register` — Register with email verification
- `POST /login` — Login with username/email
- `POST /verify` — Verify email with 6-digit code
- `POST /refresh` — Refresh access token
- `GET /session` — Get current session status
- `POST /anonymous` — Create anonymous session

### Events & Analytics (`/api/v1/`)
- `POST /events/save` — Save batch of attention events
- `GET /analytics/domains` — Get domain usage statistics

### User (`/api/v1/user/`)
- `GET /profile` — Get user profile
- `PATCH /profile/username` — Update username
- `PATCH /profile/email` — Update email

### Health
- `GET /healthcheck` — Health check
- `GET /healthcheck/database` — Database health check

---

## 🗄️ Database Schema

**Core Tables:**
- `users` — User accounts (UUID, username, email, password)
- `verification_codes` — Email verification (6-digit, expiring)
- `attention_events` — Activity tracking (domain, event_type, timestamp)
- `domain_categories` — Domain classification
- `domain_to_category` — Domain-category mapping

**Features:**
- UUID-based user identification
- Soft delete support
- Optimized indexes for analytics
- Foreign key cascades

---

## 🧪 Testing

```bash
# Run all tests
poetry run invoke tests

# Run specific test
poetry run python -m unittest app.tests.services.auth.use_cases.test_register

# Coverage
poetry run python -m unittest discover -s app/tests -p "test_*.py"
```

**Test Structure:** tests covering API, services, database, and common utilities.

---

## 🔧 Configuration

**Required Environment Variables:**
```bash
POSTGRES_USER=root
POSTGRES_PASSWORD=root
POSTGRES_DB=wmb
SECRET_KEY=your-secret-key
```

**Optional:**
```bash
# Token lifetimes
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-password
```

---

<div align="center">

**[🔌 Extensions](https://github.com/Jaldsky/mindful-web-extensions)** • **[🖥️ Frontend](https://github.com/Jaldsky/mindful-web-frontend)** • **[⚙️ Backend](https://github.com/Jaldsky/mindful-web-backend)**

Restore control over your attention! 🧘‍♀️

</div>
