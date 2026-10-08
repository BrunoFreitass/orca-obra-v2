import os

# Antes de qualquer import do projeto: config.py chama load_dotenv(), que
# NAO sobrescreve variaveis ja existentes. Com DATABASE_URL vazio aqui, o
# DATABASE_URL do .env (banco de producao) nunca chega aos testes -- ja
# aconteceu de a suite apagar precos_overrides reais no Neon. Teste que
# precisar de banco deve mockar _conectar/salvar_configuracao etc.
os.environ["DATABASE_URL"] = ""

import pytest  # noqa: E402

import config  # noqa: E402
from core import tabela_precos  # noqa: E402


@pytest.fixture(autouse=True)
def _sem_banco_real(monkeypatch):
    """Defesa extra caso algum modulo tenha lido o .env antes deste
    conftest: forca config.DATABASE_URL vazio em todo teste."""
    monkeypatch.setattr(config, "DATABASE_URL", "")


@pytest.fixture(autouse=True)
def _isola_overrides_de_preco(monkeypatch, tmp_path):
    """core/paths.py nao distingue ambiente de teste do real -- sem
    isso, qualquer teste que chame tabela_precos.restaurar_padroes()
    ou salvar_overrides() mexe direto no precos_customizados.json do
    projeto (ja aconteceu: rodar a suite apagava overrides reais
    gravados via core/sinapi_import.py). Redireciona pra um arquivo
    temporario, por teste, sem precisar mudar os testes que ja usam
    esses dois. Tambem zera o cache global de overrides antes e depois,
    pra um teste nao enxergar overrides deixados por outro."""
    monkeypatch.setattr(
        tabela_precos, "CAMINHO_OVERRIDES", str(tmp_path / "precos_customizados_teste.json")
    )
    tabela_precos.invalidar_cache_overrides()
    yield
    tabela_precos.invalidar_cache_overrides()
