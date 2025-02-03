#!/bin/sh

# Exit immediately if a command fails
set -e

exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload