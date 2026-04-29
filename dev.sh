#!/bin/bash

python -m uvicorn app.core.main:app --host 0.0.0.0 --port 8888 --reload --reload-exclude '.venv/*'
