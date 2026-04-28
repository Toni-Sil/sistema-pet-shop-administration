import sys
import traceback
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.store import Store
from app.services.produto_service import listar
from app.schemas.produto import ProdutoResponse

db = SessionLocal()
try:
    store = db.query(Store).first()
    res = listar(db, store.id, skip=0, limit=100)
    for p in res:
        try:
            p_resp = ProdutoResponse.model_validate(p)
            print(f"Validated: {p_resp.name}")
        except Exception as e:
            print(f"Failed to validate {p.name}:")
            traceback.print_exc()
finally:
    db.close()
