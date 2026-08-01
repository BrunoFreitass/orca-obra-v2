import json
import os

PERFIL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "perfil_empresa.json")

PERFIL_PADRAO = {
    "nome_empresa": "",
    "contato": "",
    "registro": "",  # ex: CREA/CAU
    "caminho_logo": "",
}


def carregar_perfil():
    """Le o perfil salvo em disco. Se nao existir ainda (primeira vez
    que o app roda), retorna os valores padrao (vazios)."""
    if not os.path.exists(PERFIL_PATH):
        return dict(PERFIL_PADRAO)
    with open(PERFIL_PATH, "r", encoding="utf-8") as f:
        dados = json.load(f)
    # Garante que campos novos (adicionados em versoes futuras) existam
    # mesmo lendo um perfil.json salvo por uma versao anterior.
    perfil = dict(PERFIL_PADRAO)
    perfil.update(dados)
    return perfil


def salvar_perfil(nome_empresa, contato, registro, caminho_logo=""):
    """Grava o perfil da empresa/profissional em disco (perfil_empresa.json),
    pra nao precisar redigitar isso a cada orcamento gerado."""
    perfil = {
        "nome_empresa": nome_empresa,
        "contato": contato,
        "registro": registro,
        "caminho_logo": caminho_logo,
    }
    with open(PERFIL_PATH, "w", encoding="utf-8") as f:
        json.dump(perfil, f, ensure_ascii=False, indent=2)
    return perfil
