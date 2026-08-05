import hashlib
import json
import os

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache_ia")
os.makedirs(CACHE_DIR, exist_ok=True)


def _hash_arquivo(caminho_arquivo):
    """Gera uma 'impressao digital' do conteudo do arquivo.
    Mesmo arquivo (mesmos bytes) = mesmo hash = mesma resposta em cache."""
    with open(caminho_arquivo, "rb") as f:
        conteudo = f.read()
    return hashlib.sha256(conteudo).hexdigest()


def _caminho_cache(caminho_arquivo):
    chave = _hash_arquivo(caminho_arquivo)
    return os.path.join(CACHE_DIR, f"{chave}.json")


def buscar_cache(caminho_arquivo):
    """Retorna os dados salvos anteriormente para este arquivo, ou None
    se essa planta ainda nunca foi analisada."""
    caminho = _caminho_cache(caminho_arquivo)
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def salvar_cache(caminho_arquivo, dados):
    caminho = _caminho_cache(caminho_arquivo)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
