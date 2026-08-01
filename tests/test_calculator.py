"""Testes do motor de calculo (core/calculator.py).

Dois tipos de caso:
1. Contas fechadas a mao, com numeros redondos -- provam que a FORMULA
   esta certa, nao so "deu igual a ultima vez".
2. Um caso real completo, usado como sentinela de regressao -- se esse
   total mudar sem voce ter alterado um preco/coeficiente de proposito
   em core/coeficientes.py, este teste quebra e avisa.
"""
import pytest

from core.models import DadosExtracao
from core.calculator import calcular_materiais, calcular_mao_de_obra
from core.coeficientes import PRECO_BLOCO_CERAMICO, CONSUMO_TIJOLO_POR_M2_PAREDE, MARGEM_PERDA, FATOR_REGIONAL_RR


def _item(itens, nome):
    """Acha um item pelo nome exato do Material -- deixa os testes
    legiveis sem depender da ordem da lista retornada."""
    for it in itens:
        if it["Material"] == nome:
            return it
    raise KeyError(f"item {nome!r} nao encontrado nos itens gerados")


class TestCalcularMateriaisContaFechada:
    def test_bloco_ceramico_bate_com_conta_manual(self):
        # 10m lineares de parede x pe direito 2.8m = 28 m2 de parede
        d = DadosExtracao(metros_parede=10)
        itens = calcular_materiais(d, padrao="Médio")
        item = _item(itens, "Bloco Cerâmico 14x19x29")

        qtd_esperada = round(28 * CONSUMO_TIJOLO_POR_M2_PAREDE.valor * MARGEM_PERDA.valor)
        assert item["Quantidade"] == qtd_esperada
        # fator regional fixo de Roraima, unico estado atendido hoje
        assert item["Preco_Unit"] == pytest.approx(PRECO_BLOCO_CERAMICO.valor * FATOR_REGIONAL_RR.valor, abs=0.001)

    def test_portas_e_janelas_sao_unidade_inteira_sem_margem_de_perda(self):
        # Nao faz sentido aplicar margem de perda de 10% em porta/janela
        # (nao se "perde" meia porta) -- a quantidade deve ser exata.
        d = DadosExtracao(portas_internas=3, portas_externas=1, janelas=5)
        itens = calcular_materiais(d, padrao="Econômico")
        assert _item(itens, "Porta Interna (Econômico)")["Quantidade"] == 3
        assert _item(itens, "Porta Externa (Econômico)")["Quantidade"] == 1
        assert _item(itens, "Janela (Econômico)")["Quantidade"] == 5

    def test_area_piso_total_soma_as_tres_areas(self):
        d = DadosExtracao(area_piso_seco=10, area_piso_molhado=5, area_piso_externo=3)
        assert d.area_piso_total == 18


class TestCalcularMaoDeObraContaFechada:
    def test_alvenaria_usa_area_de_parede_nao_metros_lineares(self):
        d = DadosExtracao(metros_parede=10)  # => 28 m2 de parede
        itens = calcular_mao_de_obra(d)
        item = _item(itens, "Alvenaria (assentamento)")
        assert item["Quantidade"] == pytest.approx(28.0, abs=0.001)


class TestRegressaoCasoReal:
    """Sentinela: caso completo com dados reais de uma planta ja
    validada manualmente durante o desenvolvimento (Boa Vista/RR, unico
    estado atendido). Se um preco em core/coeficientes.py mudar sem
    intencao, este teste acusa."""

    def _dados(self):
        return DadosExtracao(
            area_piso_seco=50.60, area_piso_molhado=8.23, area_piso_externo=23.78,
            metros_parede=60, portas_internas=8, portas_externas=2, janelas=6,
        )

    def test_total_material_medio_telhado(self):
        materiais = calcular_materiais(self._dados(), padrao="Médio", tipo_cobertura="Telhado")
        total = round(sum(i["Total"] for i in materiais), 2)
        assert total == pytest.approx(79135.33, abs=0.5)

    def test_total_mao_de_obra_telhado(self):
        mao_de_obra = calcular_mao_de_obra(self._dados(), tipo_cobertura="Telhado")
        total = round(sum(i["Total"] for i in mao_de_obra), 2)
        assert total == pytest.approx(20053.07, abs=0.5)
