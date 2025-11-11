#!/bin/sh

echo "Waiting for Postgres..."
while ! pg_isready -h db -p 5432 -U "$POSTGRES_USER"; do
  sleep 1
done

echo "Running Alembic migrations..."
alembic -c /app/alembic.ini upgrade head

echo "Starting Flask..."
exec flask run --host=0.0.0.0 --port=5000
