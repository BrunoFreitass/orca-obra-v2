"""Extração de dados de planta baixa via IA (core/vision.py)."""
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from api.schemas import DadosExtraidos
from core.vision import ErroExtracaoAmigavel, extrair_dados_da_planta

router = APIRouter(prefix="/api/extracao", tags=["extracao"])


@router.post("", response_model=DadosExtraidos)
async def extrair(planta: UploadFile) -> dict:
    extensao = Path(planta.filename or "planta").suffix or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=extensao) as tmp:
        tmp.write(await planta.read())
        caminho_temp = tmp.name

    try:
        return extrair_dados_da_planta(caminho_temp)
    except ErroExtracaoAmigavel as e:
        raise HTTPException(
            status_code=422,
            detail={"mensagem_amigavel": e.mensagem_amigavel, "detalhe_tecnico": e.detalhe_tecnico},
        ) from e
    except (ValueError, KeyError, RuntimeError) as e:
        raise HTTPException(
            status_code=422,
            detail={"mensagem_amigavel": "Erro inesperado na análise.", "detalhe_tecnico": str(e)},
        ) from e
    finally:
        Path(caminho_temp).unlink(missing_ok=True)
