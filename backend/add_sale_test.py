from app.database import SessionLocal
from app.models.venda import Venda, ItemVenda
from app.models.produto import Produto
from app.models.cliente import Cliente
from uuid import uuid4
from datetime import datetime

def add_sale():
    db = SessionLocal()
    try:
        store_id = db.query(Produto).first().store_id
        client_id = db.query(Cliente).first().id
        product = db.query(Produto).filter(Produto.name == "Ração Golden 15kg").first()
        
        venda = Venda(
            id=uuid4(),
            store_id=store_id,
            client_id=client_id,
            total=150.00,
            payment_method="pix",
            payment_status="paid",
            created_at=datetime.utcnow()
        )
        db.add(venda)
        db.flush()
        
        item = ItemVenda(
            id=uuid4(),
            sale_id=venda.id,
            product_id=product.id,
            quantity=5,
            unit_price=150.00,
            total=150.00
        )
        db.add(item)
        
        # Diminuir estoque para forçar alerta
        product.quantity = 4
        
        db.commit()
        print("Venda fake adicionada e estoque atualizado para 4 un.")
    except Exception as e:
        db.rollback()
        print(f"Erro: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_sale()
