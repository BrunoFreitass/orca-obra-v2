"""
Caminhos dos arquivos locais do projeto (perfil, cache da IA, preços
customizados), todos relativos à raiz do repositório.

No Render o filesystem é efêmero -- o que precisa sobreviver a um
redeploy fica no Postgres (core/historico.py); estes arquivos são
fallback local e cache.
"""
import os


def _diretorio_base():
    """Retorna o diretório base (pasta raiz do projeto)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


RAIZ = _diretorio_base()

PASTA_PERFIL = os.path.join(RAIZ, "perfil_empresa")
CACHE_DIR = os.path.join(RAIZ, ".cache_ia")
PERFIL_PATH = os.path.join(RAIZ, "perfil_empresa.json")
OVERRIDES_PATH = os.path.join(RAIZ, "precos_customizados.json")


def garantir_diretorios():
    """Cria os diretórios de dados se não existirem."""
    for pasta in (PASTA_PERFIL, CACHE_DIR):
        os.makedirs(pasta, exist_ok=True)
