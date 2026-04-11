from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Generic, TypeVar

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Response padrão da API"""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """Response paginado"""
    items: list[T]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class ErrorResponse(BaseModel):
    """Response de erro"""
    success: bool = False
    error: str
    message: str
    details: Optional[list[dict]] = None
    code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Response de sucesso simples"""
    success: bool = True
    message: str
    data: Optional[dict] = None


def success_response(data: Any = None, message: str = "Operação realizada com sucesso"):
    return ApiResponse(success=True, data=data, message=message)


def error_response(error: str, message: str, details: list = None, code: str = None):
    return ErrorResponse(
        success=False,
        error=error,
        message=message,
        details=details,
        code=code
    )


from typing import Any