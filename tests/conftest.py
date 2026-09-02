import pytest

from core import tabela_precos


@pytest.fixture(autouse=True)
def _isola_overrides_de_preco(monkeypatch, tmp_path):
    """core/paths.py nao distingue ambiente de teste do real -- sem
    isso, qualquer teste que chame tabela_precos.restaurar_padroes()
    ou salvar_overrides() mexe direto no precos_customizados.json do
    projeto (ja aconteceu: rodar a suite apagava overrides reais
    gravados via core/sinapi_import.py). Redireciona pra um arquivo
    temporario, por teste, sem precisar mudar os testes que ja usam
    esses dois."""
    monkeypatch.setattr(
        tabela_precos, "CAMINHO_OVERRIDES", str(tmp_path / "precos_customizados_teste.json")
    )
