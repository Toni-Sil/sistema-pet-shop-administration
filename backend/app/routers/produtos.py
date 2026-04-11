from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.database import get_db
from app.core.deps import get_any_role, get_gerente_ou_admin, get_current_store_id
from app.models.user import User
from app.schemas.produto import ProdutoCreate, ProdutoUpdate, ProdutoResponse
from app.services import produto_service

router = APIRouter(prefix="/produtos", tags=["Produtos"])

@router.get("", response_model=List[ProdutoResponse])
def listar_produtos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    return produto_service.listar(db, store_id, skip, limit)

@router.get("/barcode/{codigo}", response_model=ProdutoResponse)
def buscar_por_codigo_barras(
    codigo: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    produto = produto_service.buscar_por_codigo_barras(db, codigo, store_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@router.get("/by-weight", response_model=List[ProdutoResponse])
def listar_produtos_por_peso(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    return produto_service.listar_por_tipo(db, store_id, "WEIGHT")

@router.get("/{id}", response_model=ProdutoResponse)
def buscar_produto(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id)
):
    return produto_service.buscar_por_id(db, id, store_id)

@router.post("", response_model=ProdutoResponse, status_code=201)
def criar_produto(
    produto: ProdutoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_gerente_ou_admin),
    store_id: UUID = Depends(get_current_store_id)
):
    return produto_service.criar(db, produto, store_id)

@router.patch("/{id}", response_model=ProdutoResponse)
def atualizar_produto(
    id: UUID,
    produto: ProdutoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_gerente_ou_admin),
    store_id: UUID = Depends(get_current_store_id)
):
    return produto_service.atualizar(db, id, produto, store_id)

@router.delete("/{id}")
def deletar_produto(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_gerente_ou_admin),
    store_id: UUID = Depends(get_current_store_id)
):
    return produto_service.deletar(db, id, store_id)
