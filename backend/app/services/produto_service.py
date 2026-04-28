from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException
from app.models.produto import Produto
from app.schemas.produto import ProdutoCreate, ProdutoUpdate, SaleType

def listar(db: Session, store_id: UUID, search: str = None, skip: int = 0, limit: int = 50):
    query = db.query(Produto).filter(
        Produto.store_id == store_id,
        Produto.is_active == True
    )
    if search:
        query = query.filter(Produto.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()

def buscar_por_id(db: Session, id: UUID, store_id: UUID):
    produto = db.query(Produto).filter(
        Produto.id == id,
        Produto.store_id == store_id
    ).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

def buscar_por_codigo_barras(db: Session, codigo: str, store_id: UUID):
    return db.query(Produto).filter(
        Produto.codigo_barras == codigo,
        Produto.store_id == store_id,
        Produto.is_active == True
    ).first()

def listar_por_tipo(db: Session, store_id: UUID, tipo: str):
    return db.query(Produto).filter(
        Produto.store_id == store_id,
        Produto.sale_type == tipo,
        Produto.is_active == True
    ).all()

def criar(db: Session, dados: ProdutoCreate, store_id: UUID):
    dados_dict = dados.model_dump()
    sale_type = dados_dict.get('sale_type', 'UNIT')
    
    if sale_type == 'WEIGHT':
        dados_dict['quantity'] = None
    else:
        dados_dict['weight_in_stock'] = None
    
    produto = Produto(store_id=store_id, **dados_dict)
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto

def atualizar(db: Session, id: UUID, dados: ProdutoUpdate, store_id: UUID):
    produto = buscar_por_id(db, id, store_id)
    update_data = dados.model_dump(exclude_unset=True)
    
    if 'sale_type' in update_data and update_data['sale_type'] != produto.sale_type:
        if update_data['sale_type'] == 'WEIGHT':
            produto.quantity = None
        else:
            produto.weight_in_stock = None
    
    for key, value in update_data.items():
        setattr(produto, key, value)
    db.commit()
    db.refresh(produto)
    return produto

def deletar(db: Session, id: UUID, store_id: UUID):
    produto = buscar_por_id(db, id, store_id)
    produto.is_active = False
    db.commit()
    return {"message": "Produto deletado (soft delete) com sucesso"}

def importar_csv(db: Session, rows: list, store_id: UUID):
    from decimal import Decimal
    count = 0
    for row in rows:
        try:
            # Normalização básica
            sale_type = 'WEIGHT' if str(row.get('tipo', '')).upper() in ['PESO', 'WEIGHT', 'KG'] else 'UNIT'
            name = row.get('nome') or row.get('name')
            if not name: continue
            
            p_data = {
                "name": name,
                "category": row.get('categoria', 'Outro'),
                "sale_price": Decimal(str(row.get('preco_venda', 0)).replace(',', '.')),
                "cost_price": Decimal(str(row.get('preco_custo', 0)).replace(',', '.')),
                "sku": row.get('sku'),
                "codigo_barras": row.get('codigo_barras'),
                "sale_type": sale_type,
                "unit": row.get('unidade', 'un' if sale_type == 'UNIT' else 'kg'),
                "min_qty": int(row.get('min_qtd', 5)),
                "min_weight": Decimal(str(row.get('min_peso', 0.5)).replace(',', '.'))
            }
            
            if sale_type == 'WEIGHT':
                p_data['weight_in_stock'] = Decimal(str(row.get('estoque', 0)).replace(',', '.'))
                p_data['quantity'] = None
            else:
                p_data['quantity'] = int(row.get('estoque', 0))
                p_data['weight_in_stock'] = None
                
            produto = Produto(store_id=store_id, **p_data)
            db.add(produto)
            count += 1
        except Exception as e:
            print(f"Erro ao importar linha {row}: {e}")
            continue
            
    db.commit()
    return {"message": f"{count} produtos importados com sucesso"}
