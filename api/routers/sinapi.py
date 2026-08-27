"""Importação de preços oficiais do SINAPI (core/sinapi_import.py) --
rotas adicionadas na Fase 2."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/sinapi", tags=["sinapi"])
