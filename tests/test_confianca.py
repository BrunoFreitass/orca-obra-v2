"""Testes de core/confianca.py -- pontuacao de confianca da extracao e
heuristica de plausibilidade da metragem de parede."""
import pytest

from core.confianca import (
    CAMPOS_EXTRACAO,
    calcular_indice_confianca,
    estimar_metros_parede,
    validar_proporcao_parede,
)


def _confianca(niveis: dict) -> dict:
    """Monta o dict de confianca no formato que a IA retorna, um nivel
    por campo de CAMPOS_EXTRACAO -- campos nao informados usam 'media'."""
    return {campo: {"nivel": niveis.get(campo, "media")} for campo in CAMPOS_EXTRACAO}


class TestCalcularIndiceConfianca:
    def test_sem_confianca_retorna_padrao_media(self):
        indice = calcular_indice_confianca({})
        assert indice["nivel"] == "media"
        assert indice["percentual"] == 50

    def test_todos_os_campos_alta_da_100_por_cento(self):
        niveis = dict.fromkeys(CAMPOS_EXTRACAO, "alta")
        indice = calcular_indice_confianca(_confianca(niveis))
        assert indice["percentual"] == 100
        assert indice["nivel"] == "alta"

    def test_todos_os_campos_baixa_fica_no_nivel_baixa(self):
        niveis = dict.fromkeys(CAMPOS_EXTRACAO, "baixa")
        indice = calcular_indice_confianca(_confianca(niveis))
        # 1 ponto/campo de 3 possiveis = 33% -- bem abaixo do limiar de 70%
        assert indice["percentual"] == 33
        assert indice["nivel"] == "baixa"

    def test_limiar_de_90_por_cento_e_inclusive(self):
        # 5 campos "alta" (3 pts) + 2 "media" (2 pts) = 19/21 = 90.48% -> arredonda pra 90
        niveis = dict.fromkeys(CAMPOS_EXTRACAO[:5], "alta")
        niveis.update(dict.fromkeys(CAMPOS_EXTRACAO[5:], "media"))
        indice = calcular_indice_confianca(_confianca(niveis))
        assert indice["percentual"] == 90
        assert indice["nivel"] == "alta"

    def test_um_ponto_abaixo_do_limiar_de_90_cai_pra_media(self):
        # 4 "alta" + 3 "media" = 12+6=18/21 = 85.7% -> nivel media
        niveis = dict.fromkeys(CAMPOS_EXTRACAO[:4], "alta")
        niveis.update(dict.fromkeys(CAMPOS_EXTRACAO[4:], "media"))
        indice = calcular_indice_confianca(_confianca(niveis))
        assert indice["nivel"] == "media"
        assert indice["percentual"] < 90

    def test_limiar_de_70_por_cento_e_inclusive(self):
        # 1 "alta" + 6 "media" = 3+12 = 15/21 = 71.4% -> nivel media (>=70)
        niveis = dict.fromkeys(CAMPOS_EXTRACAO[:1], "alta")
        niveis.update(dict.fromkeys(CAMPOS_EXTRACAO[1:], "media"))
        indice = calcular_indice_confianca(_confianca(niveis))
        assert indice["percentual"] == 71
        assert indice["nivel"] == "media"

    def test_abaixo_do_limiar_de_70_cai_pra_baixa(self):
        niveis = dict.fromkeys(CAMPOS_EXTRACAO, "media")
        indice = calcular_indice_confianca(_confianca(niveis))
        assert indice["percentual"] < 70
        assert indice["nivel"] == "baixa"


class TestEstimarMetrosParede:
    def test_area_zero_ou_negativa_retorna_zero(self):
        assert estimar_metros_parede(0, 5) == 0.0
        assert estimar_metros_parede(-10, 5) == 0.0

    def test_sem_portas_internas_usa_fator_minimo(self):
        assert estimar_metros_parede(100, 0) == pytest.approx(55.0)

    def test_fator_cresce_com_portas_internas_ate_o_teto(self):
        # fator = 0.55 + min(portas*0.05, 0.55), com teto em 1.10
        assert estimar_metros_parede(100, 5) == pytest.approx(80.0)  # 0.55+0.25
        assert estimar_metros_parede(100, 20) == pytest.approx(110.0)  # teto 1.10


class TestValidarProporcaoParede:
    def test_area_ou_parede_zerada_nao_gera_aviso(self):
        assert validar_proporcao_parede(0, 60, 3) == ([], None)
        assert validar_proporcao_parede(100, 0, 3) == ([], None)

    def test_proporcao_dentro_da_faixa_nao_gera_aviso(self):
        # 100m2, 80m de parede -> razao 0.80, dentro de [0.55, 1.10]
        avisos, sugestao = validar_proporcao_parede(100, 80, 3)
        assert avisos == []
        assert sugestao is None

    def test_parede_subestimada_sugere_ajuste(self):
        # 100m2, 30m de parede -> razao 0.30, abaixo do minimo 0.55
        avisos, sugestao = validar_proporcao_parede(100, 30, 3)
        assert len(avisos) == 1
        assert "SUBESTIMADOS" in avisos[0]
        assert sugestao == estimar_metros_parede(100, 3)

    def test_parede_superestimada_avisa_sem_sugerir_ajuste(self):
        # 100m2, 150m de parede -> razao 1.5, acima do maximo 1.10
        avisos, sugestao = validar_proporcao_parede(100, 150, 3)
        assert len(avisos) == 1
        assert "SUPerestimados" in avisos[0]
        assert sugestao is None
