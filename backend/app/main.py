import logging
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.routers import (
    auth, produtos, estoque, vendas, clientes, agendamentos, despesas,
    settings as settings_router, services, pets, public, whatsapp, ai, schedule_block, 
    reports, payments, mfa, idempotency
)
from app.middleware import RequestLoggingMiddleware
from app.rate_limit import RateLimitMiddleware
from app.exceptions import (
    validation_exception_handler,
    pydantic_validation_handler,
    database_exception_handler,
    general_exception_handler
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Sistema de Gestão Pet Shop - API REST",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(produtos.router, prefix=settings.API_V1_STR)
app.include_router(estoque.router, prefix=settings.API_V1_STR)
app.include_router(vendas.router, prefix=settings.API_V1_STR)
app.include_router(clientes.router, prefix=settings.API_V1_STR)
app.include_router(agendamentos.router, prefix=settings.API_V1_STR)
app.include_router(despesas.router, prefix=settings.API_V1_STR)
app.include_router(services.router, prefix=settings.API_V1_STR)
app.include_router(pets.router, prefix=settings.API_V1_STR)
app.include_router(public.router, prefix=settings.API_V1_STR)
app.include_router(whatsapp.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(settings_router.router, prefix=settings.API_V1_STR)
app.include_router(schedule_block.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(mfa.router, prefix=settings.API_V1_STR)
app.include_router(idempotency.router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok"}
