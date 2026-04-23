#!/usr/bin/env python3
"""
job_reconciliacao_fiscal.py
--------------------------
Rotina de auditoria diária/horária para garantir o alinhamento entre o banco local
e o provedor (PlugNotas). 

O que faz:
1. Busca todas as notas em status 'processing' ou 'pending' criadas há mais de 1 hora.
2. Consulta o PlugNotas para cada uma.
3. Se o PlugNotas não conhecer a nota (ex: erro de rede no envio original), marca como 'error'.
4. Se o PlugNotas tiver um status final, atualiza o banco local.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Adiciona o path do projeto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.fiscal import NotaFiscal
from app.models.store import Store
from app.services import fiscal_service

async def reconciliar():
    db: Session = SessionLocal()
    try:
        print(f"[{datetime.utcnow()}] Iniciando rotina de reconciliação fiscal...")
        
        # 1. Busca notas "presas" (em processamento há mais de 60 minutos)
        limite_tempo = datetime.utcnow() - timedelta(minutes=60)
        notas_presas = db.query(NotaFiscal).filter(
            NotaFiscal.status.in_(["processing", "pending"]),
            NotaFiscal.created_at < limite_tempo
        ).all()

        if not notas_presas:
            print("Nenhuma nota pendente de reconciliação encontrada.")
            return

        print(f"Encontradas {len(notas_presas)} notas para auditoria.")

        # Agrupa por loja para otimizar busca de API Key
        stores_ids = list(set([n.store_id for n in notas_presas]))
        
        for s_id in stores_ids:
            # Força sincronização via polling para todas as notas daquela loja
            print(f"Reconciliando loja {s_id}...")
            count = await fiscal_service.sincronizar_status(db, s_id)
            print(f"  -> {count} notas atualizadas via polling.")

        # 2. Notas que continuam 'pending' e não foram enviadas (sem provider_id)
        # Provavelmente falhou o background task original.
        notas_nao_enviadas = db.query(NotaFiscal).filter(
            NotaFiscal.status == "pending",
            NotaFiscal.provider_id.is_(None),
            NotaFiscal.created_at < limite_tempo
        ).all()

        for n in notas_nao_enviadas:
            print(f"Nota {n.id} presa em 'pending' sem ID no provedor. Marcando como 'error' para reemissão manual.")
            n.status = "error"
            n.ultimo_erro = "Audit: Nota criada mas não enviada ao provedor após 1 hora."
        
        db.commit()
        print(f"[{datetime.utcnow()}] Reconciliação concluída com sucesso.")

    except Exception as e:
        print(f"ERRO CRÍTICO NA RECONCILIAÇÃO: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(reconciliar())
