from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.user import User
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse, PetCreate, PetResponse, PetUpdate, ClienteInativoResponse
from app.services import cliente_service

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("", response_model=List[ClienteResponse])
def listar(
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    return cliente_service.listar(db, store_id, search, skip, limit)


@router.get("/inactive", response_model=List[ClienteInativoResponse])
def listar_inativos(
    dias: int = Query(60, ge=30, description="Dias sem visita"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_any_role),
    store_id: UUID = Depends(get_current_store_id),
):
    return cliente_service.listar_inativos(db, store_id, dias)


@router.get("/{id}", response_model=ClienteResponse)
def buscar(id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_any_role), store_id: UUID = Depends(get_current_store_id)):
    return cliente_service.buscar(db, id, store_id)


@router.post("", response_model=ClienteResponse, status_code=201)
def criar(dados: ClienteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_any_role), store_id: UUID = Depends(get_current_store_id)):
    return cliente_service.criar(db, dados, store_id)


@router.patch("/{id}", response_model=ClienteResponse)
def atualizar(id: UUID, dados: ClienteUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_any_role), store_id: UUID = Depends(get_current_store_id)):
    return cliente_service.atualizar(db, id, dados, store_id)


@router.delete("/{id}")
def deletar(id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_any_role), store_id: UUID = Depends(get_current_store_id)):
    return cliente_service.deletar(db, id, store_id)


@router.post("/{client_id}/pets", response_model=PetResponse, status_code=201)
def criar_pet(client_id: UUID, dados: PetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_any_role), store_id: UUID = Depends(get_current_store_id)):
    return cliente_service.criar_pet(db, client_id, dados, store_id)


@router.patch("/{client_id}/pets/{pet_id}", response_model=PetResponse)
def atualizar_pet(client_id: UUID, pet_id: UUID, dados: PetUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_any_role), store_id: UUID = Depends(get_current_store_id)):
    return cliente_service.atualizar_pet(db, pet_id, client_id, dados, store_id)
