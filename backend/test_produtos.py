import sys
import traceback
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.store import Store
from app.services.produto_service import listar

db = SessionLocal()
try:
    store = db.query(Store).first()
    res = listar(db, store.id, skip=0, limit=100)
    print("Success, found", len(res), "products.")
except Exception as e:
    traceback.print_exc()
finally:
    db.close()
