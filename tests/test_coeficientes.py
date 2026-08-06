"""Testes de core/coeficientes.py -- garante que a tabela de precos
esta bem formada (toda entrada tem fonte e data), nao que os VALORES
em si estao certos (isso e decisao de negocio, nao de codigo).
"""
import re

from core import coeficientes
from core.coeficientes import VERSAO_TABELA, Preco, data_mais_antiga


def _todos_os_precos():
    """Percorre o modulo inteiro e devolve todo objeto Preco encontrado
    (direto ou dentro de dict/dict-de-dict) -- pra testar a tabela
    inteira sem listar cada constante manualmente aqui."""
    encontrados = []

    def visitar(valor):
        if isinstance(valor, Preco):
            encontrados.append(valor)
        elif isinstance(valor, dict):
            for v in valor.values():
                visitar(v)

    for nome in dir(coeficientes):
        if nome.startswith("_"):
            continue
        visitar(getattr(coeficientes, nome))

    return encontrados


def test_todo_preco_tem_fonte_preenchida():
    for preco in _todos_os_precos():
        assert preco.fonte and preco.fonte.strip(), f"Preco sem fonte: {preco}"


def test_todo_preco_tem_data_referencia_no_formato_aaaa_mm():
    padrao = re.compile(r"^\d{4}-\d{2}$")
    for preco in _todos_os_precos():
        assert padrao.match(preco.data_ref), f"data_ref fora do formato AAAA-MM: {preco}"


def test_todo_preco_tem_valor_positivo():
    for preco in _todos_os_precos():
        assert preco.valor > 0, f"Preco com valor zero/negativo: {preco}"


def test_versao_da_tabela_no_formato_aaaa_ponto_mm():
    assert re.match(r"^\d{4}\.\d{2}$", VERSAO_TABELA)


def test_data_mais_antiga_e_uma_das_datas_realmente_presentes():
    todas_as_datas = {p.data_ref for p in _todos_os_precos()}
    assert data_mais_antiga() in todas_as_datas
    assert data_mais_antiga() == min(todas_as_datas)
