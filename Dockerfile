# syntax=docker/dockerfile:1

FROM python:3.11 as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install Poetry & dependencies
RUN python -m pip install --upgrade pip && \
    pip install poetry==2.0.1 && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

COPY scripts/entrypoint.sh /app/scripts/entrypoint.sh
COPY src /app/src

RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --no-root --no-interaction --no-ansi

FROM python:3.11-slim as final

# Set up a non-root user for better security
RUN useradd -m appuser

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

RUN chown -R appuser:appuser /app

USER appuser

RUN chmod +x scripts/entrypoint.sh
ENTRYPOINT ["sh", "/app/scripts/entrypoint.sh"]
