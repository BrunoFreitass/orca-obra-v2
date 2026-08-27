"""Materiais, mão de obra e geração de orçamento (calculator.py,
orcamento_service.py) -- rotas adicionadas na Fase 4."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/orcamento", tags=["orcamento"])
