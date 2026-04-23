import os
from app.database import engine, Base
from app.models.store import Store
from app.models.user import User
from app.models.produto import Produto
from app.models.cliente import Cliente, Pet
from app.models.agendamento import Agendamento
from app.models.venda import Venda, ItemVenda
from app.models.financeiro import Despesa
from app.models.service import Service
from app.models.pet_vaccine import PetVaccine
from app.models.pet_note import PetNote
from app.models.whatsapp_log import WhatsAppLog
from app.models.schedule_block import ScheduleBlock

from app.core.config import settings

print("🧹 Verificando banco atual...")
if settings.DATABASE_URL.startswith("sqlite"):
    db_file = settings.DATABASE_URL.replace("sqlite:///./", "")
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"🗑️ Banco SQLite '{db_file}' removido.")
else:
    print("🐘 Banco não-SQLite detectado (Postgres). Pulando remoção de arquivo.")
    # No Postgres, poderíamos dar drop all tables se necessário
    Base.metadata.drop_all(bind=engine)

print("🏗️ Criando tabelas...")
Base.metadata.create_all(bind=engine)

print("🌱 Rodando seed...")
import seed
print("✅ Redeploy completo!")
