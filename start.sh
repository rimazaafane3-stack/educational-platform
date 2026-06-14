#!/bin/bash
set -e
echo "=== Installing dependencies ==="
pip install -r requirements.txt -q
echo "=== Seeding database ==="
python seed.py
echo "=== Starting server ==="
exec gunicorn run:app --workers 2 --bind 0.0.0.0:${PORT:-5000} --timeout 120
