#!/bin/bash
cd "$(dirname "$0")"
echo "Starting DinaHelper Backend Server..."
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 3099 --reload
