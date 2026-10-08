"""Perfil da empresa e logo (core/perfil_empresa.py)."""
import io

from fastapi import APIRouter, UploadFile
from PIL import Image

from api.schemas import PerfilEmpresa, PerfilEmpresaUpdate
from api.uploads import erro_amigavel, ler_com_limite
from core.perfil_empresa import carregar_perfil, salvar_logo, salvar_perfil

router = APIRouter(prefix="/api/perfil", tags=["perfil"])

MAX_TAMANHO_LOGO = 2 * 1024 * 1024  # 2 MB
EXTENSAO_POR_FORMATO = {"PNG": ".png", "JPEG": ".jpg"}


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
    conteudo = await ler_com_limite(logo, MAX_TAMANHO_LOGO)
    # Valida pelo conteúdo, não pela extensão enviada pelo cliente.
    try:
        with Image.open(io.BytesIO(conteudo)) as imagem:
            formato = imagem.format
            imagem.verify()
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError) as e:
        raise erro_amigavel(400, "Não foi possível ler a imagem. Envie uma logo PNG ou JPEG.") from e
    if formato not in EXTENSAO_POR_FORMATO:
        raise erro_amigavel(400, "Formato não suportado. Envie uma logo PNG ou JPEG.")

    caminho_logo = salvar_logo(conteudo, EXTENSAO_POR_FORMATO[formato])

    perfil_atual = carregar_perfil()
    return salvar_perfil(
        nome_empresa=perfil_atual["nome_empresa"],
        profissional_responsavel=perfil_atual["profissional_responsavel"],
        telefone=perfil_atual["telefone"],
        email=perfil_atual["email"],
        registro=perfil_atual["registro"],
        caminho_logo=caminho_logo,
    )
