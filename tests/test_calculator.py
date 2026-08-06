"""Testes do motor de calculo (core/calculator.py).

Dois tipos de caso:
1. Contas fechadas a mao, com numeros redondos -- provam que a FORMULA
   esta certa, nao so "deu igual a ultima vez".
2. Um caso real completo, usado como sentinela de regressao -- se esse
   total mudar sem voce ter alterado um preco/coeficiente de proposito
   em core/coeficientes.py, este teste quebra e avisa.
"""
import pytest

from core import tabela_precos
from core.calculator import calcular_mao_de_obra, calcular_materiais
from core.coeficientes import (
    CONSUMO_TIJOLO_POR_M2_PAREDE,
    FATOR_REGIONAL_RR,
    MARGEM_PERDA,
    PRECO_BLOCO_CERAMICO,
)
from core.models import DadosExtracao


def _item(itens, nome):
    """Acha um item pelo nome exato do Material -- deixa os testes
    legiveis sem depender da ordem da lista retornada."""
    for it in itens:
        if it["Material"] == nome:
            return it
    raise KeyError(f"item {nome!r} nao encontrado nos itens gerados")



@pytest.fixture(autouse=True)
def sem_overrides():
    """Garante que os testes rodem com precos padrao."""
    tabela_precos.restaurar_padroes()
    yield
    tabela_precos.restaurar_padroes()

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


class TestFaseObraBrutaAcabamento:
    """A divisao Obra Bruta / Acabamento existe pra refletir a ordem
    real da obra: eletrica e hidraulica embutidas tem que estar prontas
    ANTES do acabamento comecar -- por isso viram 2 itens (nao 1)."""

    def _dados(self):
        return DadosExtracao(area_piso_seco=100, metros_parede=40, portas_internas=2, janelas=3)

    def test_estrutura_e_sempre_obra_bruta(self):
        itens = calcular_materiais(self._dados(), padrao="Médio")
        for nome in ["Bloco Cerâmico 14x19x29", "Cimento (Fundação/Estrutura)", "Areia", "Brita", "Aço/Vergalhão"]:
            assert _item(itens, nome)["Fase"] == "Obra Bruta", nome

    def test_piso_e_pintura_sao_sempre_acabamento(self):
        itens = calcular_materiais(self._dados(), padrao="Médio")
        assert _item(itens, "Piso Interno - Área Seca (Médio)")["Fase"] == "Acabamento"
        assert _item(itens, "Tinta Acrílica Premium")["Fase"] == "Acabamento"

    def test_ponto_eletrico_vira_dois_itens_infra_e_acabamento(self):
        itens = calcular_materiais(self._dados(), padrao="Médio")
        infra = _item(itens, "Pontos Elétricos - Infraestrutura (Médio)")
        acabamento = _item(itens, "Pontos Elétricos - Acabamento (Médio)")
        assert infra["Fase"] == "Obra Bruta"
        assert acabamento["Fase"] == "Acabamento"
        # mesma quantidade de pontos nas duas partes (e o preco que se divide, nao a contagem)
        assert infra["Quantidade"] == acabamento["Quantidade"]

    def test_split_infra_60_acabamento_40_do_ponto_eletrico(self):
        itens = calcular_materiais(self._dados(), padrao="Médio")
        infra = _item(itens, "Pontos Elétricos - Infraestrutura (Médio)")
        acabamento = _item(itens, "Pontos Elétricos - Acabamento (Médio)")
        # 75 (infra) + 45 (acabamento) = 120 (preco original do ponto eletrico Medio split, antes do fator regional)
        assert infra["Preco_Unit"] + acabamento["Preco_Unit"] == pytest.approx(
            (75.0 + 45.0) * FATOR_REGIONAL_RR.valor, abs=0.01
        )

    def test_mao_de_obra_eletrica_tambem_divide_em_infra_e_acabamento(self):
        itens = calcular_mao_de_obra(self._dados())
        infra = _item(itens, "Instalação Elétrica - Infraestrutura")
        acabamento = _item(itens, "Instalação Elétrica - Acabamento")
        assert infra["Fase"] == "Obra Bruta"
        assert acabamento["Fase"] == "Acabamento"

    def test_dividir_ponto_em_dois_nao_muda_o_total_pago_por_ele(self):
        # Girar o dial de 1 item pra 2 (infra+acabamento) e so reorganizacao
        # -- a soma das duas partes tem que ser igual ao preco unico de antes.
        itens = calcular_materiais(self._dados(), padrao="Alto Padrão")
        infra = _item(itens, "Pontos Hidráulicos - Infraestrutura (Alto Padrão)")
        acabamento = _item(itens, "Pontos Hidráulicos - Acabamento (Alto Padrão)")
        # 140 (infra) + 85 (acabamento) = 225 (preco original split do Alto Padrao)
        assert infra["Preco_Unit"] + acabamento["Preco_Unit"] == pytest.approx(
            (140.0 + 85.0) * FATOR_REGIONAL_RR.valor, abs=0.01
        )


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
    intencao, este teste acusa.

    NOTA: o valor de referencia foi atualizado em 2026-08 apos correcao
    do coeficiente de cimento (de 7 sacos/m2 absurdo para 0.5 saco/m2
    realista, conforme SINAPI)."""

    def _dados(self):
        return DadosExtracao(
            area_piso_seco=50.60, area_piso_molhado=8.23, area_piso_externo=23.78,
            metros_parede=60, portas_internas=8, portas_externas=2, janelas=6,
        )

    def test_total_material_medio_telhado(self):
        materiais = calcular_materiais(self._dados(), padrao="Médio", tipo_cobertura="Telhado")
        total = round(sum(i["Total"] for i in materiais), 2)
        # Valor atualizado apos correcao do coeficiente de cimento (0.5 saco/m2)
        assert total == pytest.approx(51599.95, abs=0.5)

    def test_total_mao_de_obra_telhado(self):
        mao_de_obra = calcular_mao_de_obra(self._dados(), tipo_cobertura="Telhado")
        total = round(sum(i["Total"] for i in mao_de_obra), 2)
        assert total == pytest.approx(21825.47, abs=0.5)
