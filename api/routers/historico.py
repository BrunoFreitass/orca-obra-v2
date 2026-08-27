"""Listagem, exclusão e download de orçamentos salvos (core/historico.py)
-- rotas adicionadas na Fase 1."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/historico", tags=["historico"])
