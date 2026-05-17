#!/bin/bash
set -e

alembic upgrade head

exec python -m uvicorn app.core.main:app \
  --host 0.0.0.0 \
  --port 8888 \
  --reload \
  --reload-dir /graxon/graxon
