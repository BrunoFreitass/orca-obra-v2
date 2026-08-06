"""Testes de core/models.py -- propriedades derivadas de DadosExtracao
e serializacao de ItemOrcamento."""
import pytest

from core.models import (
    ALTURA_PAREDE_PADRAO,
    DadosExtracao,
    ItemOrcamento,
    itens_para_dicts,
)


class TestDadosExtracao:
    def test_area_piso_total_soma_as_tres_areas(self):
        d = DadosExtracao(area_piso_seco=10, area_piso_molhado=5, area_piso_externo=3)
        assert d.area_piso_total == 18

    def test_portas_total_soma_internas_e_externas(self):
        d = DadosExtracao(portas_internas=3, portas_externas=2)
        assert d.portas_total == 5

    def test_area_parede_usa_pe_direito_padrao(self):
        d = DadosExtracao(metros_parede=10)
        assert d.area_parede == pytest.approx(10 * ALTURA_PAREDE_PADRAO)

    def test_area_cobertura_telhado_tem_fator_de_beiral(self):
        d = DadosExtracao(area_piso_seco=100)
        assert d.area_cobertura("Telhado") == pytest.approx(115.0)  # +15%

    def test_area_cobertura_laje_nao_tem_fator_extra(self):
        d = DadosExtracao(area_piso_seco=100)
        assert d.area_cobertura("Laje") == pytest.approx(100.0)

    def test_from_dict_aceita_chaves_faltando(self):
        d = DadosExtracao.from_dict({"area_piso_seco": 50})
        assert d.area_piso_seco == 50
        assert d.metros_parede == 0
        assert d.portas_internas == 0

    def test_from_dict_aceita_valores_none(self):
        # A IA as vezes retorna null pra um campo que nao conseguiu ler
        # -- from_dict nao pode quebrar nesse caso.
        d = DadosExtracao.from_dict({"area_piso_seco": None, "portas_internas": None})
        assert d.area_piso_seco == 0
        assert d.portas_internas == 0


class TestItemOrcamento:
    def test_total_e_quantidade_vezes_preco_unitario(self):
        item = ItemOrcamento("Material", "Bloco", quantidade=100, preco_unit=1.5)
        assert item.total == 150.0

    def test_total_arredonda_a_duas_casas(self):
        item = ItemOrcamento("Material", "X", quantidade=3, preco_unit=0.333)
        assert item.total == 1.0  # 0.999 arredondado

    def test_to_dict_tem_as_6_chaves_esperadas(self):
        item = ItemOrcamento("Material", "Bloco", 100, 1.5)
        d = item.to_dict()
        assert set(d.keys()) == {"Tipo", "Material", "Quantidade", "Preco_Unit", "Total", "Fase"}
        assert d["Total"] == 150.0

    def test_fase_padrao_e_obra_bruta_quando_nao_especificada(self):
        item = ItemOrcamento("Material", "Bloco", 100, 1.5)
        assert item.fase == "Obra Bruta"

    def test_fase_pode_ser_definida_explicitamente(self):
        item = ItemOrcamento("Material", "Tinta", 10, 22.0, fase="Acabamento")
        assert item.to_dict()["Fase"] == "Acabamento"


def test_itens_para_dicts_converte_lista_inteira():
    itens = [ItemOrcamento("Material", "A", 1, 10), ItemOrcamento("Material", "B", 2, 5)]
    dicts = itens_para_dicts(itens)
    assert len(dicts) == 2
    assert dicts[0]["Total"] == 10
    assert dicts[1]["Total"] == 10
