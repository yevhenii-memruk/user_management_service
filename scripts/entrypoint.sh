#!/bin/sh

# Exit immediately if a command fails
set -e

echo "Waiting for RabbitMQ to be ready..."
sleep 5

exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
