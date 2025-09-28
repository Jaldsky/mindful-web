# 🌐 Mindful-Web
*Aware presence in the digital world*

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-black)](https://fastapi.tiangolo.com/)

> **Mindful-Web** is an open-source tool for mindful internet use.

---

## 🌍 About / О проекте
### 🇬🇧 English
Mindful-Web is an open-source tool for anyone who wants to understand where their time online goes and reclaim
control over their attention.

### 🇷🇺 Русский
Mindful-Web — это open-source инструмент для тех, кто хочет понимать, куда уходит их время в интернете, и возвращать
контроль над своим вниманием.

## ✨ Features

- 🕒 **Full domain-level time tracking**
- 📊 **Daily & weekly usage reports**
- 💡 **Personalized suggestions** based on your habits
- 🔒 **Privacy-first**: only domains, never full URLs

## 🛠️ Tech Stack

- **Frontend**: Chrome Extension (JavaScript)
- **Backend**: Python, FastAPI
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL
- **Infrastructure**: Docker, Docker Compose
- **CI/CD**: GitHub Actions (tests, linting, build)

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/Jaldsky/mindful-web.git
cd mindful-web
```

### 2. Set up environment variables

### 3. Build the base image
```bash
docker build -t mindfulweb-base:latest -f deploy/docker/base.Dockerfile .
```

### 4. Build and start all services
```bash
docker-compose -f deploy/docker-compose.yml up --build
```

### 4. Check that it works
Open in your browser:<br>
🔗 http://localhost:8000/docs
