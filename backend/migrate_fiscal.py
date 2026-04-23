#!/usr/bin/env python3
"""
Script de migração para adicionar tabela de notas fiscais.
Execute com: python3 migrate_fiscal.py
(com as variáveis de ambiente do .env carregadas)
"""

import os
import sys

# Garante que app/ é importável
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.database import engine, Base
# Importa todos os modelos para garantir que as FKs sejam resolvidas
from app.models import (  # noqa: F401
    cliente, produto, venda, financeiro, estoque,
    agendamento, service, store, user, fiscal,
    pet_note, pet_vaccine, schedule_block, whatsapp_log
)
from sqlalchemy import text, inspect

def migrate():
    print("🚀 Criando tabela notas_fiscais …")
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if "notas_fiscais" not in existing_tables:
        Base.metadata.tables["notas_fiscais"].create(bind=engine)
        print("  ✅ Tabela notas_fiscais criada!")
    else:
        print("  ⚠️  Tabela notas_fiscais já existe, pulando criação.")

    # Adiciona colunas fiscal_status e fiscal_document_id em sales (se ainda não existirem)
    if "sales" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("sales")]
        with engine.connect() as conn:
            for col_name, col_def in [
                ("fiscal_status", "VARCHAR(20) DEFAULT 'none'"),
                ("fiscal_document_id", "VARCHAR(255)"),
            ]:
                if col_name not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE sales ADD COLUMN {col_name} {col_def}"))
                        conn.commit()
                        print(f"  ✅ Coluna '{col_name}' adicionada à tabela sales.")
                    except Exception as e:
                        print(f"  ⚠️  Não foi possível adicionar '{col_name}': {e}")
                else:
                    print(f"  ⚠️  Coluna '{col_name}' já existe.")

    print("\n✅ Migração fiscal concluída.")

if __name__ == "__main__":
    migrate()
