#!/usr/bin/env python3
"""Adiciona colunas novas ao modelo revisado de notas_fiscais."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import os
os.environ.setdefault("DATABASE_URL", open(".env").read().split("DATABASE_URL=")[1].split()[0] if os.path.exists(".env") else "")

from app.database import engine
from sqlalchemy import text, inspect

NEW_COLS = [
    ("idempotency_key",      "VARCHAR(100)"),
    ("lote_id",              "VARCHAR(255)"),
    ("tentativas",           "INTEGER DEFAULT 0"),
    ("max_tentativas",       "INTEGER DEFAULT 3"),
    ("ultimo_erro",          "TEXT"),
    ("webhook_recebido_em",  "TIMESTAMP"),
    ("last_sync_at",         "TIMESTAMP"),
]

inspector = inspect(engine)
existing = [c["name"] for c in inspector.get_columns("notas_fiscais")]

with engine.connect() as conn:
    for col, typedef in NEW_COLS:
        if col not in existing:
            conn.execute(text(f"ALTER TABLE notas_fiscais ADD COLUMN {col} {typedef}"))
            conn.commit()
            print(f"  ✅ Coluna '{col}' adicionada.")
        else:
            print(f"  ⚠️  Coluna '{col}' já existe.")

print("\n✅ Colunas do modelo revisado aplicadas.")
