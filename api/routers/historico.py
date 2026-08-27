"""Listagem, exclusão e download de orçamentos salvos (core/historico.py)."""
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.schemas import OrcamentoHistorico
from core.historico import excluir_orcamento, listar_orcamentos

router = APIRouter(prefix="/api/historico", tags=["historico"])


def _achar_ou_404(orcamento_id: int) -> dict:
    for registro in listar_orcamentos():
        if registro["id"] == orcamento_id:
            return registro
    raise HTTPException(status_code=404, detail="Orçamento não encontrado no histórico.")


@router.get("", response_model=list[OrcamentoHistorico])
def listar() -> list[dict]:
    return listar_orcamentos()


@router.delete("/{orcamento_id}", status_code=204)
def excluir(orcamento_id: int) -> None:
    _achar_ou_404(orcamento_id)
    excluir_orcamento(orcamento_id)


@router.get("/{orcamento_id}/excel")
def baixar_excel(orcamento_id: int) -> FileResponse:
    registro = _achar_ou_404(orcamento_id)
    caminho = registro["caminho_excel"]
    if not os.path.exists(caminho):
        raise HTTPException(status_code=404, detail="Arquivo Excel não encontrado no disco.")
    return FileResponse(
        caminho,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(caminho),
    )


@router.get("/{orcamento_id}/pdf")
def baixar_pdf(orcamento_id: int) -> FileResponse:
    registro = _achar_ou_404(orcamento_id)
    caminho = registro.get("caminho_pdf")
    if not caminho or not os.path.exists(caminho):
        raise HTTPException(status_code=404, detail="Arquivo PDF não encontrado no disco.")
    return FileResponse(caminho, media_type="application/pdf", filename=os.path.basename(caminho))
