import sys
import os
from uuid import UUID

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.database import SessionLocal

from app.services import venda_service
from app.schemas.venda import VendaCreate, ItemVendaBase
from decimal import Decimal

db = SessionLocal()
try:
    # Get a store and product
    from app.models.store import Store
    from app.models.produto import Produto
    from app.models.user import User
    
    store = db.query(Store).first()
    product = db.query(Produto).filter(Produto.store_id == store.id).first()
    user = db.query(User).filter(User.store_id == store.id).first()
    
    if not store or not product or not user:
        print("Missing data for test")
        sys.exit(1)
        
    print(f"Testing sale for store {store.name}, product {product.name}, user {user.name}")
    
    venda_data = VendaCreate(
        client_id=None,
        items=[
            ItemVendaBase(
                product_id=product.id,
                quantity=1,
                unit_price=product.sale_price,
                total=product.sale_price
            )
        ],
        discount=Decimal('0.00'),
        payment_method='pix',
        notes='Teste automatizado'
    )
    
    venda = venda_service.realizar_venda(db, venda_data, store.id, user.id)
    print(f"Sale successful! ID: {venda.id}")
    
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
