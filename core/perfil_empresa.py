import base64
import glob
import json
import os
import tempfile
from contextlib import contextmanager

from core import paths
from core.historico import obter_configuracao, salvar_configuracao

PERFIL_PATH = paths.PERFIL_PATH
CHAVE_LOGO = "logo_empresa"

PERFIL_PADRAO = {
    "nome_empresa": "",
    "profissional_responsavel": "",
    "telefone": "",
    "email": "",
    "registro": "",  # ex: CREA/CAU/CNPJ
    "caminho_logo": "",
}


def carregar_perfil():
    """Lê o perfil da empresa. Prioriza o PostgreSQL (sobrevive a redeploy
    no Render), com fallback transparente para o arquivo local perfil_empresa.json
    quando o banco não estiver configurado ou estiver inacessível."""
    dados_banco = obter_configuracao("perfil_empresa")
    if dados_banco and isinstance(dados_banco, dict):
        perfil = dict(PERFIL_PADRAO)
        perfil.update(dados_banco)
        return perfil

    if not os.path.exists(PERFIL_PATH):
        return dict(PERFIL_PADRAO)
    with open(PERFIL_PATH, encoding="utf-8") as f:
        dados = json.load(f)
    perfil = dict(PERFIL_PADRAO)
    perfil.update(dados)
    return perfil


def salvar_perfil(nome_empresa, profissional_responsavel, telefone, email,
                   registro, caminho_logo=""):
    """Grava o perfil tanto no PostgreSQL (persistência definitiva)
    quanto no arquivo local perfil_empresa.json (fallback e desenvolvimento)."""
    perfil = {
        "nome_empresa": nome_empresa,
        "profissional_responsavel": profissional_responsavel,
        "telefone": telefone,
        "email": email,
        "registro": registro,
        "caminho_logo": caminho_logo,
    }
    # Persiste no banco se disponível
    salvar_configuracao("perfil_empresa", perfil)

    # Persiste localmente como garantia offline
    try:
        with open(PERFIL_PATH, "w", encoding="utf-8") as f:
            json.dump(perfil, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

    return perfil


def salvar_logo(conteudo: bytes, extensao: str) -> str:
    """Grava a logo (já validada pelo router) no PostgreSQL, em base64 na
    tabela configuracoes -- o disco do Render é efêmero e a logo sumia a
    cada redeploy. Também grava o arquivo local (fallback sem banco),
    removendo a logo anterior de qualquer extensão. Retorna o caminho local."""
    for antiga in glob.glob(os.path.join(paths.PASTA_PERFIL, "logo.*")):
        os.remove(antiga)
    caminho_logo = os.path.join(paths.PASTA_PERFIL, f"logo{extensao}")
    with open(caminho_logo, "wb") as f:
        f.write(conteudo)

    salvar_configuracao(CHAVE_LOGO, {
        "extensao": extensao,
        "base64": base64.b64encode(conteudo).decode("ascii"),
    })
    return caminho_logo


@contextmanager
def arquivo_logo(caminho_logo: str):
    """Caminho de arquivo da logo pra montar o PDF. Se a logo estiver no
    banco, gera um arquivo temporário (apagado ao sair do bloco); senão,
    usa o caminho local salvo no perfil (fallback sem DATABASE_URL)."""
    dados = obter_configuracao(CHAVE_LOGO)
    if not dados:
        yield caminho_logo
        return

    fd, caminho_temp = tempfile.mkstemp(suffix=dados["extensao"])
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(base64.b64decode(dados["base64"]))
        yield caminho_temp
    finally:
        os.remove(caminho_temp)
