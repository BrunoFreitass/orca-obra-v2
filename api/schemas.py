"""Espelhos pydantic dos modelos de core/models.py e respostas da API.
Preenchido conforme cada fase liga suas rotas -- ver
C:\\Users\\bruno\\.claude\\plans\\immutable-rolling-volcano.md."""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
