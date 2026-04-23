#!/bin/bash

# Esperar DB estar pronto (opcional com healthcheck no compose, mas bom ter)
echo "Waiting for database..."

# Rodar migrações ou criar tabelas via script
python redeploy_db.py

echo "Starting server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
