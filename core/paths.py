"""
Utilitário de caminhos de arquivo que funciona tanto no
ambiente de desenvolvimento local quanto no Streamlit Cloud.

No Streamlit Cloud, o filesystem do container é efêmero -- reinícios
apagam tudo fora do diretório persistente. Este módulo detecta o
ambiente e retorna caminhos adequados.
"""
import os


def _diretorio_base():
    """Retorna o diretório base (pasta raiz do projeto)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


RAIZ = _diretorio_base()

PASTA_ORCAMENTOS = os.path.join(RAIZ, "orcamentos_salvos")
PASTA_PERFIL = os.path.join(RAIZ, "perfil_empresa")
CACHE_DIR = os.path.join(RAIZ, ".cache_ia")
PERFIL_PATH = os.path.join(RAIZ, "perfil_empresa.json")
OVERRIDES_PATH = os.path.join(RAIZ, "precos_customizados.json")


def garantir_diretorios():
    """Cria os diretórios de dados se não existirem."""
    for pasta in (PASTA_ORCAMENTOS, PASTA_PERFIL, CACHE_DIR):
        os.makedirs(pasta, exist_ok=True)
