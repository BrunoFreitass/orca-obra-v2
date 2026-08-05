"""
Logging estruturado para o OrçaObra AI.

Por padrao, logs de INFO+ vao para o console (visiveis no Streamlit
Cloud / terminal) e logs de DEBUG+ vao para arquivo rotativo
(app.log, max 5MB, 3 backups). Isso permite diagnosticar problemas
em producao sem poluir a tela do usuario.

Uso:
    from core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Orçamento gerado: %s", nome_projeto)
    logger.error("Falha ao gerar PDF", exc_info=True)
"""

import logging
import logging.handlers
import os
import sys

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_PATH = os.path.join(LOG_DIR, "orcaobra.log")

_FMT_CONSOLE = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_FMT_FILE = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"


def _configurar():
    """Configura o logging global uma unica vez."""
    root = logging.getLogger()
    if root.handlers:
        return  # ja configurado (evita duplicar em reloads do Streamlit)

    root.setLevel(logging.DEBUG)

    # Handler de console: INFO+ (visivel pro usuario/dev)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(_FMT_CONSOLE, datefmt="%H:%M:%S"))
    root.addHandler(console)

    # Handler de arquivo rotativo: DEBUG+ (diagnostico completo)
    arquivo = logging.handlers.RotatingFileHandler(
        LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    arquivo.setLevel(logging.DEBUG)
    arquivo.setFormatter(logging.Formatter(_FMT_FILE, datefmt="%Y-%m-%d %H:%M:%S"))
    root.addHandler(arquivo)

    # Reduz verbosidade de bibliotecas de terceiros
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def get_logger(nome: str) -> logging.Logger:
    """Retorna um logger nomeado, ja configurado."""
    _configurar()
    return logging.getLogger(nome)
