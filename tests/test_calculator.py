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
    FATOR_REGIONAL_RR,
    MARGEM_PERDA,
    PRECO_BLOCO_CERAMICO,
)
from core.models import AREA_MEDIA_JANELA_M2, DadosExtracao


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
        # 10m lineares de parede x pe direito 2.8m = 28 m2 de parede.
        # Quantidade em m² de parede pronta, nao em nº de tijolos --
        # PRECO_BLOCO_CERAMICO e' preco por m² (material + mao de obra
        # de assentamento), igual a composicao SINAPI que pode
        # sobrescreve-lo.
        d = DadosExtracao(metros_parede=10)
        itens = calcular_materiais(d, padrao="Médio")
        item = _item(itens, "Bloco Cerâmico 14x19x29")

        qtd_esperada = round(28 * MARGEM_PERDA.valor, 2)
        assert item["Quantidade"] == pytest.approx(qtd_esperada, abs=0.001)
        # fator regional fixo de Roraima, unico estado atendido hoje
        assert item["Preco_Unit"] == pytest.approx(PRECO_BLOCO_CERAMICO.valor * FATOR_REGIONAL_RR.valor, abs=0.001)

    def test_portas_sao_unidade_inteira_sem_margem_de_perda(self):
        # Nao faz sentido aplicar margem de perda de 10% em porta (nao
        # se "perde" meia porta) -- a quantidade deve ser exata.
        d = DadosExtracao(portas_internas=3, portas_externas=1)
        itens = calcular_materiais(d, padrao="Econômico")
        assert _item(itens, "Porta Interna (Econômico)")["Quantidade"] == 3
        assert _item(itens, "Porta Externa (Econômico)")["Quantidade"] == 1

    def test_janela_converte_contagem_em_area_media(self):
        # SINAPI precifica janela por m2 do vao, nao por unidade -- a
        # contagem que a IA extrai da planta (unica coisa que da pra ler
        # com confianca, ja que uma planta baixa nao mostra a altura do
        # vao) e convertida em area usando um tamanho medio fixo
        # (AREA_MEDIA_JANELA_M2 em core/models.py), sem margem de perda.
        d = DadosExtracao(janelas=5)
        itens = calcular_materiais(d, padrao="Econômico")
        qtd_esperada = round(5 * AREA_MEDIA_JANELA_M2, 2)
        assert _item(itens, "Janela (Econômico)")["Quantidade"] == pytest.approx(qtd_esperada, abs=0.001)

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
        assert _item(itens, "Pintura (Médio)")["Fase"] == "Acabamento"

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


class TestMaoDeObraSemDuplicarComposicaoSinapiCompleta:
    """Servicos cujo material ja e' uma composicao SINAPI completa
    (material + mao de obra) nao devem gerar linha de mao de obra em
    paralelo -- ver core/sinapi_codigos.py secao 3."""

    def _dados(self):
        return DadosExtracao(
            metros_parede=10, area_piso_seco=20, area_piso_molhado=5,
            portas_internas=2, portas_externas=1,
        )

    def test_itens_cobertos_por_composicao_sinapi_completa_nao_aparecem(self):
        itens = calcular_mao_de_obra(self._dados(), tipo_cobertura="Telhado")
        nomes = {it["Material"] for it in itens}
        redundantes = {
            "Alvenaria (assentamento)",
            "Assentamento de Piso (Área Seca)",
            "Assentamento de Piso (Área Molhada)",
            "Instalação de Porta Interna",
            "Instalação de Porta Externa",
        }
        assert not (nomes & redundantes)

    def test_execucao_de_cobertura_nunca_aparece_em_mao_de_obra(self):
        # "Execução de Cobertura" saiu de MAO_DE_OBRA_POR_SERVICO em
        # 2026-09: pra Telhado, cobertura_Telhado ja e' composicao SINAPI
        # completa (94195/94207/94216); pra Laje, virou item de MATERIAL
        # "Estrutura da Laje de Cobertura" (laje pre-moldada, que inclui
        # material, nao so mao de obra) -- ver teste abaixo.
        itens_telhado = calcular_mao_de_obra(self._dados(), tipo_cobertura="Telhado")
        itens_laje = calcular_mao_de_obra(self._dados(), tipo_cobertura="Laje")
        assert "Execução de Cobertura" not in {it["Material"] for it in itens_telhado}
        assert "Execução de Cobertura" not in {it["Material"] for it in itens_laje}

    def test_estrutura_da_laje_de_cobertura_so_aparece_para_laje(self):
        materiais_telhado = calcular_materiais(self._dados(), padrao="Médio", tipo_cobertura="Telhado")
        materiais_laje = calcular_materiais(self._dados(), padrao="Médio", tipo_cobertura="Laje")
        assert "Estrutura da Laje de Cobertura (Médio)" not in {it["Material"] for it in materiais_telhado}
        assert "Estrutura da Laje de Cobertura (Médio)" in {it["Material"] for it in materiais_laje}


class TestRegressaoCasoReal:
    """Sentinela: caso completo com dados reais de uma planta ja
    validada manualmente durante o desenvolvimento (Boa Vista/RR, unico
    estado atendido). Se um preco em core/coeficientes.py mudar sem
    intencao, este teste acusa.

    NOTA: o valor de referencia foi atualizado em 2026-08 apos correcao
    do coeficiente de cimento (de 7 sacos/m2 absurdo para 0.5 saco/m2
    realista, conforme SINAPI).

    NOTA 2: total_mao_de_obra_telhado caiu de R$21.825,47 pra R$8.041,72
    em 2026-08 -- nao e' regressao, e' a remocao intencional dos
    servicos que duplicavam mao de obra ja embutida nas composicoes
    SINAPI completas de material (ver
    TestMaoDeObraSemDuplicarComposicaoSinapiCompleta acima).

    NOTA 3: total_material_medio_telhado subiu de R$51.599,95 pra
    R$59.085,69 em 2026-08 -- correcao de bug: "Bloco Ceramico" media
    quantidade em nº de tijolos mas PRECO_BLOCO_CERAMICO (e a
    composicao SINAPI que pode sobrescreve-lo) sempre foi preco por m²
    de parede pronta, nao por tijolo. Ver comentario de
    PRECO_BLOCO_CERAMICO em coeficientes.py.

    NOTA 4: total_material_medio_telhado subiu de R$59.085,69 pra
    R$72.266,06 em 2026-09 -- nao e' regressao, e' a adicao intencional
    de 4 itens que faltavam pra cobrir uma obra completa: Reboco,
    Impermeabilizacao (area molhada), Rejunte e Forro de Gesso (ver
    ITENS_EXTRAS em core/sinapi_codigos.py e a secao correspondente em
    core/coeficientes.py).

    NOTA 5: total_material_medio_telhado subiu de R$72.266,06 pra
    R$76.634,05 em 2026-09 (mesmo dia) -- conferencia do preco de
    Reboco contra o arquivo oficial SINAPI (RR, ref. 2026-07): o
    "chute" inicial de pesquisa de mercado (R$38,00/m2) foi substituido
    pelo valor real (R$60,09/m2 = soma de 2 composicoes SINAPI,
    chapisco + emboço/massa unica -- ver PRECO_REBOCO_M2 em
    coeficientes.py).

    NOTA 6: total_material_medio_telhado subiu de R$76.634,05 pra
    R$78.630,42 e total_mao_de_obra_telhado caiu de R$8.041,72 pra
    R$6.930,76 em 2026-09 -- Janela passou a ser precificada por m2
    (SINAPI so' tem preco de janela por m2 do vao, nao por unidade;
    ver AREA_MEDIA_JANELA_M2 em core/models.py), com preco real do
    SINAPI (antes era pesquisa de mercado por unidade). Como a
    composicao de janela ja inclui "fornecimento e instalacao", o item
    de mao de obra "Instalacao de Janela" saiu do calculo pra nao
    contar 2x (mesmo motivo removeu "Assentamento de Piso (Area
    Externa)", ja coberto desde o commit a69d1d5).

    NOTA 7: total_material_medio_telhado subiu de R$78.630,42 pra
    R$79.799,79 e total_mao_de_obra_telhado caiu de R$6.930,76 pra
    R$4.773,64 em 2026-09 -- "Tinta Acrilica Premium" (material, por
    litro) + "Pintura" (mao de obra avulsa) foram fundidos num unico
    item "Pintura ({padrao})", usando 3 composicoes SINAPI reais que ja
    embutem tinta + aplicacao manual (2 demaos) -- ver PRECOS_PINTURA em
    coeficientes.py. Mesmo motivo das fusoes anteriores: manter os dois
    em paralelo contaria a mao de obra 2x."""

    def _dados(self):
        return DadosExtracao(
            area_piso_seco=50.60, area_piso_molhado=8.23, area_piso_externo=23.78,
            metros_parede=60, portas_internas=8, portas_externas=2, janelas=6,
        )

    def test_total_material_medio_telhado(self):
        materiais = calcular_materiais(self._dados(), padrao="Médio", tipo_cobertura="Telhado")
        total = round(sum(i["Total"] for i in materiais), 2)
        # Valor atualizado apos fundir tinta+pintura num item SINAPI so
        # -- ver NOTA 7 na docstring da classe.
        assert total == pytest.approx(79799.79, abs=0.5)

    def test_total_mao_de_obra_telhado(self):
        mao_de_obra = calcular_mao_de_obra(self._dados(), tipo_cobertura="Telhado")
        total = round(sum(i["Total"] for i in mao_de_obra), 2)
        # Valor atualizado apos remover "Pintura" (agora embutida na
        # composicao do material) -- ver NOTA 7 na docstring da classe.
        assert total == pytest.approx(4773.64, abs=0.5)
