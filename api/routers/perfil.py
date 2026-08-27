"""Perfil da empresa e logo (core/perfil_empresa.py)."""
import os

from fastapi import APIRouter, UploadFile

from api.schemas import PerfilEmpresa, PerfilEmpresaUpdate
from core import paths
from core.perfil_empresa import carregar_perfil, salvar_perfil

router = APIRouter(prefix="/api/perfil", tags=["perfil"])


@router.get("", response_model=PerfilEmpresa)
def obter() -> dict:
    return carregar_perfil()


@router.put("", response_model=PerfilEmpresa)
def atualizar(dados: PerfilEmpresaUpdate) -> dict:
    caminho_logo_atual = carregar_perfil()["caminho_logo"]
    return salvar_perfil(
        nome_empresa=dados.nome_empresa,
        profissional_responsavel=dados.profissional_responsavel,
        telefone=dados.telefone,
        email=dados.email,
        registro=dados.registro,
        caminho_logo=caminho_logo_atual,
    )


@router.post("/logo", response_model=PerfilEmpresa)
async def enviar_logo(logo: UploadFile) -> dict:
    extensao = os.path.splitext(logo.filename or "")[1] or ".png"
    caminho_logo = os.path.join(paths.PASTA_PERFIL, f"logo{extensao}")
    conteudo = await logo.read()
    with open(caminho_logo, "wb") as f:
        f.write(conteudo)

    perfil_atual = carregar_perfil()
    return salvar_perfil(
        nome_empresa=perfil_atual["nome_empresa"],
        profissional_responsavel=perfil_atual["profissional_responsavel"],
        telefone=perfil_atual["telefone"],
        email=perfil_atual["email"],
        registro=perfil_atual["registro"],
        caminho_logo=caminho_logo,
    )
