"""Status de cota da API do Gemini (core/monitor_api.py) -- rota
adicionada na Fase 1."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/monitor", tags=["monitor"])
