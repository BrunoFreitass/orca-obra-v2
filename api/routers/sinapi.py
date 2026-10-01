"""Importação de preços oficiais do SINAPI (core/sinapi_import.py)."""
import re
import tempfile
from pathlib import Path
from zipfile import BadZipFile

from fastapi import APIRouter, Form, UploadFile
from openpyxl.utils.exceptions import InvalidFileException

from api.routers.precos import _listar as listar_precos
from api.schemas import ItemPreco, SinapiAplicarRequest, SinapiImportarResponse
from api.uploads import erro_amigavel, ler_com_limite
from core import sinapi_import as si
from core import tabela_precos as tp

router = APIRouter(prefix="/api/sinapi", tags=["sinapi"])

MAX_ARQUIVOS = 5
MAX_TAMANHO_ARQUIVO = 30 * 1024 * 1024  # 30 MB


def _basename_seguro(nome: str | None) -> str:
    """Stem do nome enviado (sem diretórios), só com [A-Za-z0-9._-]. A
    barra invertida também conta como separador, já que Path no Linux
    não a reconhece."""
    stem = Path((nome or "").replace("\\", "/")).stem
    return re.sub(r"[^A-Za-z0-9._-]", "_", stem)


@router.post("/importar", response_model=SinapiImportarResponse)
async def importar(
    arquivos: list[UploadFile],
    mes_referencia: str | None = Form(default=None),
) -> dict:
    if len(arquivos) > MAX_ARQUIVOS:
        raise erro_amigavel(400, f"Envie no máximo {MAX_ARQUIVOS} arquivos por vez.")

    with tempfile.TemporaryDirectory() as tmpdir:
        caminhos = []
        for i, arquivo in enumerate(arquivos):
            if Path(arquivo.filename or "").suffix.lower() != ".xlsx":
                raise erro_amigavel(400, "Formato não suportado. Envie arquivos .xlsx do SINAPI.")
            # O nome do cliente nunca vira caminho: só o basename sanitizado
            # entra no nome gerado, pra _extrair_mes_referencia ainda achar o
            # mês (ex.: SINAPI_2025_08.xlsx).
            caminho = Path(tmpdir) / f"arquivo_{i}_{_basename_seguro(arquivo.filename)}.xlsx"
            caminho.write_bytes(await ler_com_limite(arquivo, MAX_TAMANHO_ARQUIVO))
            caminhos.append(caminho)

        try:
            precos, avisos, mes_ref = si.importar(caminhos, mes_referencia=mes_referencia or None)
        except (BadZipFile, InvalidFileException, KeyError, ValueError, OSError) as e:
            raise erro_amigavel(
                400, "Não foi possível ler a planilha. Confira se é um arquivo .xlsx válido do SINAPI."
            ) from e

    return {"precos": precos, "avisos": avisos, "mes_ref": mes_ref}


@router.post("/aplicar", response_model=list[ItemPreco])
def aplicar(corpo: SinapiAplicarRequest) -> list[dict]:
    tp.salvar_overrides(
        corpo.valores,
        fonte=f"SINAPI oficial (CAIXA/IBGE) - ref. {corpo.mes_ref}",
        data_ref=corpo.mes_ref,
    )
    return listar_precos()
