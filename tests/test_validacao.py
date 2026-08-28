"""Testes de core/validacao.py -- faixas plausiveis dos dados extraidos."""
from core.validacao import validar_area_total_planta, validar_dados


def _dados_ok():
    """Um conjunto de dados totalmente dentro das faixas esperadas,
    usado como base -- cada teste so muda o campo que quer testar."""
    return {"area_piso": 75, "metros_parede": 60, "portas": 5, "janelas": 6}


class TestValidarDados:
    def test_dados_normais_nao_geram_aviso(self):
        assert validar_dados(_dados_ok()) == []

    def test_campo_ausente_gera_aviso(self):
        dados = _dados_ok()
        del dados["area_piso"]
        avisos = validar_dados(dados)
        assert len(avisos) == 1
        assert "não foi retornado pela IA" in avisos[0]

    def test_valor_negativo_gera_aviso(self):
        dados = _dados_ok()
        dados["metros_parede"] = -10
        avisos = validar_dados(dados)
        assert any("negativo" in a for a in avisos)

    def test_area_piso_zerada_gera_aviso(self):
        # area_piso tem minimo > 0 na faixa -- zero e implausivel pra
        # uma planta de verdade, deve alertar.
        dados = _dados_ok()
        dados["area_piso"] = 0
        avisos = validar_dados(dados)
        assert any("zerado" in a for a in avisos)

    def test_portas_zeradas_nao_gera_aviso(self):
        # portas/janelas tem faixa comecando em 0 -- zero e um resultado
        # legitimo (planta sem porta interna, por exemplo) e NAO deve
        # gerar aviso de "zerado".
        dados = _dados_ok()
        dados["portas"] = 0
        avisos = validar_dados(dados)
        assert avisos == []

    def test_valor_muito_acima_do_esperado_gera_aviso(self):
        dados = _dados_ok()
        dados["area_piso"] = 5000  # acima do maximo (2000)
        avisos = validar_dados(dados)
        assert any("acima do esperado" in a for a in avisos)

    def test_multiplos_campos_problematicos_geram_multiplos_avisos(self):
        dados = {"area_piso": -5, "metros_parede": None, "portas": 0, "janelas": 6}
        avisos = validar_dados(dados)
        assert len(avisos) == 2  # area_piso negativa + metros_parede ausente


class TestValidarAreaTotalPlanta:
    def _dados_base(self, **overrides):
        dados = {
            "area_piso_seco": 100.0,
            "area_piso_molhado": 15.0,
            "area_piso_externo": 48.4,  # soma = 163.4
            "area_total_planta": 0,
            "confianca": {
                "area_piso_seco": {"nivel": "alta", "motivo": "lida diretamente"},
                "area_piso_molhado": {"nivel": "alta", "motivo": "lida diretamente"},
                "area_piso_externo": {"nivel": "alta", "motivo": "lida diretamente"},
            },
        }
        dados.update(overrides)
        return dados

    def test_sem_area_total_impressa_nao_mexe(self):
        # Caso mais comum: a planta nao tem area total impressa em
        # lugar nenhum (area_total_planta == 0) -- nao ha o que cruzar.
        dados = self._dados_base(area_total_planta=0)
        resultado = validar_area_total_planta(dados)
        assert resultado["confianca"]["area_piso_seco"]["nivel"] == "alta"

    def test_area_total_dentro_da_tolerancia_mantem_confianca(self):
        # soma = 163.4, total impresso 173.5 -> divergencia ~5.8%, dentro
        # dos 10% de tolerancia (paredes, arredondamento).
        dados = self._dados_base(area_total_planta=173.5)
        resultado = validar_area_total_planta(dados)
        assert resultado["confianca"]["area_piso_seco"]["nivel"] == "alta"

    def test_area_total_muito_divergente_rebaixa_as_3_areas(self):
        # Caso real: planta "Casa Brunort" -- soma dos ambientes deu
        # 163.4, mas a planta declarava area total de 156.1 no titulo
        # (divergencia ~4.7%... o teste abaixo usa uma diferenca maior
        # de proposito pra forcar o rebaixamento).
        dados = self._dados_base(area_total_planta=140.0)  # divergencia ~16.7%
        resultado = validar_area_total_planta(dados)
        for campo in ("area_piso_seco", "area_piso_molhado", "area_piso_externo"):
            assert resultado["confianca"][campo]["nivel"] == "baixa"
            assert "diverge" in resultado["confianca"][campo]["motivo"]

    def test_sem_soma_de_ambientes_nao_mexe(self):
        dados = self._dados_base(
            area_piso_seco=0, area_piso_molhado=0, area_piso_externo=0,
            area_total_planta=173.5,
        )
        resultado = validar_area_total_planta(dados)
        assert resultado["confianca"]["area_piso_seco"]["nivel"] == "alta"
