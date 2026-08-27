"""Status de cota da API do Gemini (core/monitor_api.py)."""
from fastapi import APIRouter

from api.schemas import MonitorStatus
from core.monitor_api import status_cota

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


@router.get("/status", response_model=MonitorStatus)
def obter_status() -> dict:
    return status_cota()
