"""Tabela de preços customizados (core/tabela_precos.py)."""
import os
import tempfile
from pathlib import Path
from zipfile import BadZipFile

from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse
from openpyxl.utils.exceptions import InvalidFileException

from api.schemas import ItemPreco, PrecosAplicarRequest, PrecosImportarResponse
from api.uploads import erro_amigavel, ler_com_limite
from core import paths
from core import tabela_precos as tp

router = APIRouter(prefix="/api/precos", tags=["precos"])

MAX_TAMANHO_PLANILHA = 5 * 1024 * 1024  # 5 MB (o modelo tem poucos KB)


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
    conteudo = await ler_com_limite(arquivo, MAX_TAMANHO_PLANILHA)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(conteudo)
        caminho_temp = tmp.name
    try:
        atualizados, avisos = tp.importar_tabela_excel(caminho_temp)
    except (BadZipFile, InvalidFileException, KeyError, ValueError, OSError) as e:
        raise erro_amigavel(
            400, "Não foi possível ler a planilha. Envie o arquivo .xlsx do 'Baixar modelo Excel'."
        ) from e
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
