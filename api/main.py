"""Ponto de entrada da API do OrçaObra AI -- camada fina sobre core/,
servindo tanto as rotas /api/* quanto o build estático do frontend
(frontend/dist) em produção.
"""
import base64
import binascii
import os
import secrets

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from core import paths
from core.historico import inicializar_db
from core.logger import get_logger
from core.monitor_api import inicializar_tabela_monitor

logger = get_logger(__name__)

try:
    inicializar_db()
    inicializar_tabela_monitor()
except Exception as e:
    logger.warning("Aviso: banco de dados não inicializado no startup (%s). Operações dependentes tentarão reconectar.", e)

paths.garantir_diretorios()

app = FastAPI(title="OrçaObra AI API")


def _credenciais_validas(cabecalho: str, usuario: str, senha: str) -> bool:
    esquema, _, token = cabecalho.partition(" ")
    if esquema.lower() != "basic":
        return False
    try:
        decodificado = base64.b64decode(token, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        return False
    usuario_enviado, separador, senha_enviada = decodificado.partition(":")
    if not separador:
        return False
    # Compara os dois sempre (sem curto-circuito) pra não vazar por tempo
    # qual dos campos está errado.
    usuario_ok = secrets.compare_digest(usuario_enviado.encode(), usuario.encode())
    senha_ok = secrets.compare_digest(senha_enviada.encode(), senha.encode())
    return usuario_ok and senha_ok


# HTTP Basic em todas as rotas (/api/* e frontend estático), exceto o
# health check. Fail-closed: sem APP_USER/APP_PASSWORD responde 503, a
# menos que AUTH_DISABLED=true (só dev/teste). Lido a cada requisição pra
# os testes poderem trocar as variáveis sem reimportar o app.
@app.middleware("http")
async def autenticacao_basic(request: Request, call_next):
    if request.method == "GET" and request.url.path == "/api/health":
        return await call_next(request)
    if os.environ.get("AUTH_DISABLED", "").lower() == "true":
        return await call_next(request)

    usuario = os.environ.get("APP_USER", "")
    senha = os.environ.get("APP_PASSWORD", "")
    if not usuario or not senha:
        return JSONResponse(
            status_code=503,
            content={"detail": "Autenticação não configurada no servidor: defina APP_USER e APP_PASSWORD."},
        )
    if not _credenciais_validas(request.headers.get("authorization", ""), usuario, senha):
        # WWW-Authenticate faz o navegador pedir a senha -- necessário pros
        # downloads de Excel/PDF, que são <a href> direto, sem fetch.
        return JSONResponse(
            status_code=401,
            content={"detail": "Usuário ou senha inválidos."},
            headers={"WWW-Authenticate": 'Basic realm="OrcaObra"'},
        )
    return await call_next(request)


@app.middleware("http")
async def headers_de_seguranca(request: Request, call_next):
    resposta = await call_next(request)
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["X-Frame-Options"] = "DENY"
    resposta.headers["Referrer-Policy"] = "same-origin"
    return resposta

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


# Build estático do frontend (gerado por `npm run build` em frontend/).
# Montado por último pra não sombrear as rotas /api/*.
_CAMINHO_FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_CAMINHO_FRONTEND_BUILD):
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=_CAMINHO_FRONTEND_BUILD, html=True), name="frontend")
