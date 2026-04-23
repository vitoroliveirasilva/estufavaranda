#!/bin/sh
set -eu

cd /app/backend

python -m flask --app manage.py db upgrade

exec "$@"
