"""Testes de core/validacao.py -- faixas plausiveis dos dados extraidos."""
from core.validacao import validar_dados


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
