#!/bin/bash

# if some error, stop
set -e

echo "Running database migrations..."
cd /app/models/db_schemes/minirag/
alembic upgrade head
cd /app


# The next two lines make docker to continuou execution not starting from beginning
echo "Starting FastAPI application..."
exec "$@"