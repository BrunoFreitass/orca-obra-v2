"""Ponto de entrada da API do OrçaObra AI -- camada fina sobre core/,
pensada pra rodar em paralelo ao app Streamlit existente (app.py)
durante a transição pro front-end em React. Nada aqui modifica core/*.py
além do que já foi explicitamente movido (core/confianca.py,
core/orcamento_service.py:gerar_orcamento_completo).

Ver plano completo em C:\\Users\\bruno\\.claude\\plans\\immutable-rolling-volcano.md.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import (
    extracao,
    historico,
    monitor,
    orcamento,
    perfil,
    precos,
    revisao,
    sinapi,
)
from api.schemas import HealthResponse

app = FastAPI(title="OrçaObra AI API")

# Em dev, o Vite roda em processo separado (porta 5173) e precisa de CORS
# pra chamar a API (porta 8000). Em produção, o frontend é servido pelos
# mesmos estáticos desta API (mesma origem) -- sem necessidade de CORS.
ORIGENS_DEV = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENS_DEV,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (extracao, revisao, orcamento, historico, perfil, precos, sinapi, monitor):
    app.include_router(router.router)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


# Build estático do frontend (gerado por `npm run build` em frontend/) --
# só existe a partir da Fase 6 (ou antes, se alguém rodar o build local).
# Montado por último pra não sombrear as rotas /api/*.
_CAMINHO_FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_CAMINHO_FRONTEND_BUILD):
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=_CAMINHO_FRONTEND_BUILD, html=True), name="frontend")
