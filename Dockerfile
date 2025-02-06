FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set up a non-root user for better security
RUN useradd -m appuser

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Install Poetry & dependencies
RUN python -m pip install --upgrade pip && \
    pip install poetry==2.0.1 && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

COPY . .

RUN chown -R appuser:appuser /app

USER appuser

RUN chmod +x scripts/entrypoint.sh
ENTRYPOINT ["sh", "/app/scripts/entrypoint.sh"]
