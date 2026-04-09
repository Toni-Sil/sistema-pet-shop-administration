from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai.routes import router as ai_router

app = FastAPI(title="Pet Shop Administration API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restringir para domínios confiáveis
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas de saúde
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Pet Shop Administration API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Rotas de IA / agentes
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
