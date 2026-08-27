"""Importação de preços oficiais do SINAPI (core/sinapi_import.py)."""
import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, UploadFile

from api.routers.precos import _listar as listar_precos
from api.schemas import ItemPreco, SinapiAplicarRequest, SinapiImportarResponse
from core import sinapi_import as si
from core import tabela_precos as tp

router = APIRouter(prefix="/api/sinapi", tags=["sinapi"])


@router.post("/importar", response_model=SinapiImportarResponse)
async def importar(
    arquivos: list[UploadFile],
    mes_referencia: str | None = Form(default=None),
) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        caminhos = []
        for arquivo in arquivos:
            caminho = Path(tmpdir) / (arquivo.filename or "arquivo.xlsx")
            caminho.write_bytes(await arquivo.read())
            caminhos.append(caminho)

        precos, avisos, mes_ref = si.importar(caminhos, mes_referencia=mes_referencia or None)

    return {"precos": precos, "avisos": avisos, "mes_ref": mes_ref}


@router.post("/aplicar", response_model=list[ItemPreco])
def aplicar(corpo: SinapiAplicarRequest) -> list[dict]:
    tp.salvar_overrides(
        corpo.valores,
        fonte=f"SINAPI oficial (CAIXA/IBGE) - ref. {corpo.mes_ref}",
        data_ref=corpo.mes_ref,
    )
    return listar_precos()
