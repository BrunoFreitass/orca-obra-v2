"""Listagem, exclusão e download de orçamentos salvos (core/historico.py)."""
import os
import tempfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from api.schemas import OrcamentoHistorico
from core.historico import buscar_orcamento, excluir_orcamento, listar_orcamentos
from core.perfil_empresa import carregar_perfil
from core.proposta_pdf import gerar_pdf_proposta
from core.reporter import gerar_excel

router = APIRouter(prefix="/api/historico", tags=["historico"])


def _achar_ou_404(orcamento_id: int) -> dict:
    registro = buscar_orcamento(orcamento_id)
    if registro is None:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado no histórico.")
    return registro


def _contato_e_registro(perfil: dict) -> tuple[list[str], str]:
    contato_linhas = []
    if perfil.get("profissional_responsavel"):
        contato_linhas.append(f"Profissional Responsável: {perfil['profissional_responsavel']}")
    if perfil.get("telefone"):
        contato_linhas.append(f"Contato: {perfil['telefone']}")
    if perfil.get("email"):
        contato_linhas.append(f"E-mail: {perfil['email']}")

    registro_str = ""
    if perfil.get("registro"):
        registro_str = f"Registro (CREA/CAU/CNPJ): {perfil['registro']}"

    return contato_linhas, registro_str


@router.get("", response_model=list[OrcamentoHistorico])
def listar() -> list[dict]:
    return listar_orcamentos()


@router.delete("/{orcamento_id}", status_code=204)
def excluir(orcamento_id: int) -> None:
    _achar_ou_404(orcamento_id)
    excluir_orcamento(orcamento_id)


@router.get("/{orcamento_id}/excel")
def baixar_excel(orcamento_id: int) -> FileResponse:
    """Regenera o Excel a partir do orcamento_json salvo no histórico
    (não depende de arquivo em disco, que não sobrevive a um redeploy
    no Render free -- ver core/historico.py::buscar_orcamento)."""
    registro = _achar_ou_404(orcamento_id)

    fd, caminho = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    gerar_excel(registro["orcamento_json"], caminho, registro["bdi_percentual"])

    return FileResponse(
        caminho,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"orcamento_{orcamento_id}.xlsx",
        background=BackgroundTask(os.remove, caminho),
    )


@router.get("/{orcamento_id}/pdf")
def baixar_pdf(orcamento_id: int) -> FileResponse:
    """Regenera o PDF a partir do orcamento_json salvo no histórico --
    mesmo motivo de baixar_excel acima."""
    registro = _achar_ou_404(orcamento_id)
    perfil = carregar_perfil()
    contato_linhas, registro_str = _contato_e_registro(perfil)

    fd, caminho = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    gerar_pdf_proposta(
        registro["orcamento_json"], caminho,
        nome_projeto=registro["nome_projeto"],
        estado_uf=registro["estado_uf"], padrao=registro["padrao"],
        tipo_cobertura=registro["tipo_cobertura"], area_piso=registro["area_piso"],
        bdi_percentual=registro["bdi_percentual"],
        nome_empresa=perfil["nome_empresa"] or "OrçaObra AI",
        contato=contato_linhas,
        registro=registro_str,
        caminho_logo=perfil["caminho_logo"],
    )

    return FileResponse(
        caminho,
        media_type="application/pdf",
        filename=f"orcamento_{orcamento_id}.pdf",
        background=BackgroundTask(os.remove, caminho),
    )
