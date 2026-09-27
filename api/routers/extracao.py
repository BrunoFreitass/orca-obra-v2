"""Extração de dados de planta baixa via IA (core/vision.py)."""
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from api.schemas import DadosExtraidos, LayoutGeometria
from core.vision import ErroExtracaoAmigavel, extrair_dados_da_planta, gerar_layout_ilustrativo

router = APIRouter(prefix="/api/extracao", tags=["extracao"])


MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB
EXTENSOES_PERMITIDAS = {".pdf", ".jpg", ".jpeg", ".png"}


async def _validar_e_salvar_upload(planta: UploadFile) -> str:
    extensao = Path(planta.filename or "planta").suffix.lower() or ".png"
    if extensao not in EXTENSOES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail={"mensagem_amigavel": "Formato de arquivo não suportado. Envie um arquivo PDF, JPG ou PNG."},
        )

    conteudo = await planta.read()
    if len(conteudo) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail={"mensagem_amigavel": "Arquivo muito grande. O tamanho máximo permitido é 20MB."},
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=extensao) as tmp:
        tmp.write(conteudo)
        return tmp.name


@router.post("", response_model=DadosExtraidos)
async def extrair(planta: UploadFile) -> dict:
    caminho_temp = await _validar_e_salvar_upload(planta)
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


@router.post("/layout-ilustrativo", response_model=LayoutGeometria)
async def layout_ilustrativo(planta: UploadFile) -> dict:
    """Geometria 3D aproximada e ilustrativa, acionada sob demanda pelo
    frontend só quando a extração oficial (/api/extracao) já recusou a
    geometria (layout.disponivel=false). Nunca afeta o orçamento -- ver
    core.vision.gerar_layout_ilustrativo."""
    caminho_temp = await _validar_e_salvar_upload(planta)
    try:
        return gerar_layout_ilustrativo(caminho_temp)
    except ErroExtracaoAmigavel as e:
        raise HTTPException(
            status_code=422,
            detail={"mensagem_amigavel": e.mensagem_amigavel, "detalhe_tecnico": e.detalhe_tecnico},
        ) from e
    except (ValueError, KeyError, RuntimeError) as e:
        raise HTTPException(
            status_code=422,
            detail={"mensagem_amigavel": "Erro inesperado ao gerar a visualização ilustrativa.", "detalhe_tecnico": str(e)},
        ) from e
    finally:
        Path(caminho_temp).unlink(missing_ok=True)
