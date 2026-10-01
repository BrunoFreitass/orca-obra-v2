import hashlib
import json
import os

from core import paths

CACHE_DIR = paths.CACHE_DIR
paths.garantir_diretorios()


def _chave_cache(caminho_arquivo, contexto):
    """Gera uma 'impressao digital' do conteudo do arquivo + contexto.
    Mesmo arquivo (mesmos bytes) com o mesmo contexto = mesma resposta
    em cache. O contexto (modelo + versao do prompt, ver core/vision.py)
    evita devolver resultado velho depois de trocar o modelo ou o prompt."""
    with open(caminho_arquivo, "rb") as f:
        conteudo = f.read()
    return hashlib.sha256(conteudo + contexto.encode("utf-8")).hexdigest()


def _caminho_cache(caminho_arquivo, contexto):
    chave = _chave_cache(caminho_arquivo, contexto)
    return os.path.join(CACHE_DIR, f"{chave}.json")


def buscar_cache(caminho_arquivo, contexto):
    """Retorna os dados salvos anteriormente para este arquivo e contexto,
    ou None se essa planta ainda nunca foi analisada nesse contexto."""
    caminho = _caminho_cache(caminho_arquivo, contexto)
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    return None


def salvar_cache(caminho_arquivo, dados, contexto):
    caminho = _caminho_cache(caminho_arquivo, contexto)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
