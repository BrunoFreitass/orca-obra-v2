import json
import os

from core import paths
from core.historico import obter_configuracao, salvar_configuracao

PERFIL_PATH = paths.PERFIL_PATH

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
