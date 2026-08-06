import json
import os

from core import paths

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
    """Le o perfil salvo em disco. Se nao existir ainda (primeira vez
    que o app roda), retorna os valores padrao (vazios)."""
    if not os.path.exists(PERFIL_PATH):
        return dict(PERFIL_PADRAO)
    with open(PERFIL_PATH, encoding="utf-8") as f:
        dados = json.load(f)
    # Garante que campos novos (adicionados em versoes futuras) existam
    # mesmo lendo um perfil.json salvo por uma versao anterior.
    perfil = dict(PERFIL_PADRAO)
    perfil.update(dados)
    return perfil


def salvar_perfil(nome_empresa, profissional_responsavel, telefone, email,
                   registro, caminho_logo=""):
    """Grava o perfil da empresa/profissional em disco (perfil_empresa.json),
    pra nao precisar redigitar isso a cada orcamento gerado."""
    perfil = {
        "nome_empresa": nome_empresa,
        "profissional_responsavel": profissional_responsavel,
        "telefone": telefone,
        "email": email,
        "registro": registro,
        "caminho_logo": caminho_logo,
    }
    with open(PERFIL_PATH, "w", encoding="utf-8") as f:
        json.dump(perfil, f, ensure_ascii=False, indent=2)
    return perfil
