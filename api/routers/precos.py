"""Tabela de preços customizados (core/tabela_precos.py) -- rotas
adicionadas na Fase 2."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/precos", tags=["precos"])
