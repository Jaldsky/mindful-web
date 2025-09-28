FROM python:3.11-alpine3.21
LABEL maintainer="ryzhenkovartg@gmail.com"
ENV TZ="Europe/Moscow"

RUN apk add --no-cache gcc musl-dev postgresql-dev libpq

RUN addgroup -g 1001 -S appgroup \
    && adduser -u 1001 -S appuser -G appgroup

ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_VENV=/opt/poetry-venv \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN python -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip \
    && $POETRY_VENV/bin/pip install "poetry==$POETRY_VERSION" \
    && ln -s $POETRY_VENV/bin/poetry /usr/local/bin/poetry

WORKDIR /app
COPY pyproject.toml /app/

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

RUN python -m venv $VIRTUAL_ENV \
    && poetry config virtualenvs.create false \
    && poetry install --only=main --no-root

RUN chown -R appuser:appgroup /app
