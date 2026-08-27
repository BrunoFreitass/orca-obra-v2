"""Tabela de preços customizados (core/tabela_precos.py)."""
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse

from api.schemas import ItemPreco, PrecosAplicarRequest, PrecosImportarResponse
from core import paths
from core import tabela_precos as tp

router = APIRouter(prefix="/api/precos", tags=["precos"])


def _listar() -> list[dict]:
    overrides = tp.carregar_overrides()
    itens = []
    for chave, categoria, rotulo, preco_padrao in tp._itens_editaveis():
        efetivo = tp.obter_preco(chave, preco_padrao)
        itens.append({
            "chave": chave,
            "categoria": categoria,
            "rotulo": rotulo,
            "valor": efetivo.valor,
            "fonte": efetivo.fonte,
            "data_ref": efetivo.data_ref,
            "customizado": chave in overrides,
        })
    return itens


@router.get("", response_model=list[ItemPreco])
def listar() -> list[dict]:
    return _listar()


@router.get("/modelo")
def baixar_modelo() -> FileResponse:
    caminho = os.path.join(paths.PASTA_PERFIL, "modelo_tabela_precos.xlsx")
    tp.gerar_modelo_excel(caminho)
    return FileResponse(
        caminho,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="tabela_precos_orcaobra.xlsx",
    )


@router.post("/importar", response_model=PrecosImportarResponse)
async def importar(arquivo: UploadFile) -> dict:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(await arquivo.read())
        caminho_temp = tmp.name
    try:
        atualizados, avisos = tp.importar_tabela_excel(caminho_temp)
    finally:
        Path(caminho_temp).unlink(missing_ok=True)
    return {"atualizados": atualizados, "avisos": avisos}


@router.post("/aplicar", response_model=list[ItemPreco])
def aplicar(corpo: PrecosAplicarRequest) -> list[dict]:
    tp.salvar_overrides(corpo.valores)
    return _listar()


@router.post("/restaurar", response_model=list[ItemPreco])
def restaurar() -> list[dict]:
    tp.restaurar_padroes()
    return _listar()
