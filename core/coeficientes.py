"""
Tabela de precos e coeficientes de consumo -- fonte unica de verdade,
versionada e rastreavel.

Antes desta refatoracao (Fase 3 do roadmap), esses numeros estavam
espalhados como constantes soltas em core/calculator.py e
core/sinapi.py, sem nenhum registro de onde vieram nem de quando
foram conferidos pela ultima vez. Se um preco estivesse desatualizado,
a unica forma de descobrir era lembrar de cabeca.

Cada valor agora e um objeto Preco(valor, fonte, data_ref) -- e da pra
perguntar ao sistema, a qualquer momento, "qual e o dado mais antigo
usado neste orcamento?" (ver data_mais_antiga(), usada no rodape do
PDF gerado por core/proposta_pdf.py).

REGRA AO ATUALIZAR UM PRECO: mude o "valor" e o "data_ref" juntos.
Um preco novo com data antiga e uma mentira sobre a procedencia do
dado -- pior do que nao ter o rastreamento.
"""

from dataclasses import dataclass

VERSAO_TABELA = "2026.07"  # AAAA.MM da ultima revisao geral desta tabela


@dataclass(frozen=True)
class Preco:
    valor: float
    fonte: str
    data_ref: str  # "AAAA-MM"


def _mais_antiga(*precos_ou_dicts) -> str:
    """Retorna a menor (mais antiga) data_ref entre varios Preco ou
dicts de {chave: Preco}. Usado para calcular a data de referencia
efetiva de um orcamento inteiro (ver data_mais_antiga() abaixo)."""
    datas = []
    for item in precos_ou_dicts:
        if isinstance(item, Preco):
            datas.append(item.data_ref)
        else:
            datas.extend(p.data_ref for p in item.values())
    return min(datas)


# =====================================================================
# COEFICIENTES DE CONSUMO FISICO (quanto material por m2/ml) -- nao
# variam por estado, so o PRECO do material varia regionalmente.
# =====================================================================
CONSUMO_CIMENTO_SACO_POR_M2 = Preco(0.5, "SINAPI - composição contrapiso", "2026-06")
CONSUMO_AREIA_M3_POR_M2 = Preco(0.5, "SINAPI - composição contrapiso", "2026-06")
CONSUMO_BRITA_M3_POR_M2 = Preco(0.3, "SINAPI - composição concreto estrutural", "2026-06")
CONSUMO_ACO_KG_POR_M2 = Preco(6, "SINAPI - composição estrutura/fundação", "2026-06")
CONSUMO_ARGAMASSA_KG_POR_M2 = Preco(5, "Padrão de mercado - argamassa AC-II para assentamento de piso", "2026-06")
CONSUMO_TINTA_L_POR_M2 = Preco(0.4, "Padrão de mercado - tinta acrílica premium, 2 demãos", "2026-06")
M2_POR_PONTO_ELETRICO = Preco(5, "Estimativa de mercado (heurística, não é item SINAPI)", "2026-06")
M2_POR_PONTO_HIDRAULICO = Preco(8, "Estimativa de mercado (heurística, não é item SINAPI)", "2026-06")
MARGEM_PERDA = Preco(1.1, "Padrão de mercado para perda/quebra de material (10%)", "2026-06")

# =====================================================================
# PRECOS BASE POR PADRAO DE ACABAMENTO (R$), antes do fator regional
# =====================================================================
PRECOS_PISO_SECO = {
    "Econômico": Preco(35.00, "Pesquisa de mercado - piso cerâmico econômico", "2026-06"),
    "Médio": Preco(55.00, "Pesquisa de mercado - porcelanato padrão médio", "2026-06"),
    "Alto Padrão": Preco(89.90, "Pesquisa de mercado - porcelanato importado/grande formato", "2026-06"),
}
PRECOS_PISO_MOLHADO = {
    "Econômico": Preco(28.00, "Pesquisa de mercado - cerâmica antiderrapante econômica", "2026-06"),
    "Médio": Preco(42.00, "Pesquisa de mercado - porcelanato antiderrapante médio", "2026-06"),
    "Alto Padrão": Preco(68.00, "Pesquisa de mercado - porcelanato antiderrapante premium", "2026-06"),
}
PRECOS_PISO_EXTERNO = {
    "Econômico": Preco(38.00, "Pesquisa de mercado - piso externo econômico", "2026-06"),
    "Médio": Preco(58.00, "Pesquisa de mercado - piso externo antiderrapante médio", "2026-06"),
    "Alto Padrão": Preco(95.00, "Pesquisa de mercado - piso externo premium", "2026-06"),
}
PRECOS_PORTA_INTERNA = {
    "Econômico": Preco(150.00, "Pesquisa de mercado - porta lisa econômica", "2026-06"),
    "Médio": Preco(260.00, "Pesquisa de mercado - porta semi-oca padrão médio", "2026-06"),
    "Alto Padrão": Preco(480.00, "Pesquisa de mercado - porta maciça/design", "2026-06"),
}
PRECOS_PORTA_EXTERNA = {
    "Econômico": Preco(280.00, "Pesquisa de mercado - porta externa econômica", "2026-06"),
    "Médio": Preco(480.00, "Pesquisa de mercado - porta externa reforçada média", "2026-06"),
    "Alto Padrão": Preco(850.00, "Pesquisa de mercado - porta externa blindada/design", "2026-06"),
}
PRECOS_JANELA = {
    "Econômico": Preco(150.00, "Pesquisa de mercado - janela de alumínio econômica", "2026-06"),
    "Médio": Preco(280.00, "Pesquisa de mercado - janela de alumínio padrão médio", "2026-06"),
    "Alto Padrão": Preco(590.00, "Pesquisa de mercado - janela de alumínio premium/vidro duplo", "2026-06"),
}

# -----------------------------------------------------------------
# PONTOS ELÉTRICOS E HIDRÁULICOS — split em infraestrutura + acabamento
# (adicionado na v2 para maior granularidade de custo)
# -----------------------------------------------------------------
PRECOS_PONTO_ELETRICO_INFRA = {
    "Econômico": Preco(55.00, "Pesquisa de mercado - infra elétrica econômica (tubo/fio/caixa)", "2026-06"),
    "Médio": Preco(75.00, "Pesquisa de mercado - infra elétrica padrão médio", "2026-06"),
    "Alto Padrão": Preco(110.00, "Pesquisa de mercado - infra elétrica premium (eletroduto, condulete)", "2026-06"),
}
PRECOS_PONTO_ELETRICO_ACABAMENTO = {
    "Econômico": Preco(30.00, "Pesquisa de mercado - acabamento elétrico econômico (tomada/interruptor simples)", "2026-06"),
    "Médio": Preco(45.00, "Pesquisa de mercado - acabamento elétrico padrão médio", "2026-06"),
    "Alto Padrão": Preco(70.00, "Pesquisa de mercado - acabamento elétrico premium (tomada USB, dimmer, inteligente)", "2026-06"),
}
PRECOS_PONTO_HIDRAULICO_INFRA = {
    "Econômico": Preco(70.00, "Pesquisa de mercado - infra hidráulica econômica (tubo/cotovelo/caixa)", "2026-06"),
    "Médio": Preco(95.00, "Pesquisa de mercado - infra hidráulica padrão médio", "2026-06"),
    "Alto Padrão": Preco(140.00, "Pesquisa de mercado - infra hidráulica premium (tubo PPR, registros de gaveta)", "2026-06"),
}
PRECOS_PONTO_HIDRAULICO_ACABAMENTO = {
    "Econômico": Preco(40.00, "Pesquisa de mercado - acabamento hidráulico econômico (torneira simples, sifão)", "2026-06"),
    "Médio": Preco(55.00, "Pesquisa de mercado - acabamento hidráulico padrão médio", "2026-06"),
    "Alto Padrão": Preco(85.00, "Pesquisa de mercado - acabamento hidráulico premium (torneira monocomando, ducha)", "2026-06"),
}

PRECOS_COBERTURA = {
    "Telhado": {
        "Econômico": Preco(75.00, "Pesquisa de mercado - telhado cerâmico econômico", "2026-06"),
        "Médio": Preco(110.00, "Pesquisa de mercado - telhado cerâmico padrão médio", "2026-06"),
        "Alto Padrão": Preco(165.00, "Pesquisa de mercado - telhado com manta/isolamento premium", "2026-06"),
    },
    "Laje": {
        "Econômico": Preco(95.00, "Pesquisa de mercado - laje pré-moldada econômica", "2026-06"),
        "Médio": Preco(140.00, "Pesquisa de mercado - laje maciça padrão médio", "2026-06"),
        "Alto Padrão": Preco(210.00, "Pesquisa de mercado - laje com impermeabilização premium", "2026-06"),
    },
}

# =====================================================================
# PRECOS FIXOS (nao variam por padrao de acabamento)
# =====================================================================
# R$/m² de parede pronta (material + mão de obra de assentamento), não
# R$/tijolo -- desde 2026-08 esta chave pode ser sobrescrita pela
# composição SINAPI completa "bloco_ceramico" (ver core/sinapi_codigos.py),
# que já embute os dois. O padrão abaixo soma as duas estimativas
# antigas (pesquisa de mercado: R$1,25/tijolo × 27 tijolos/m² ≈ R$33,75
# de material + R$37,86 de mão de obra que existia como item separado)
# pra manter o mesmo total de antes da mudança de unidade, só que numa
# unidade consistente com o que calcular.py de fato multiplica.
PRECO_BLOCO_CERAMICO = Preco(71.61, "Pesquisa de mercado - bloco cerâmico 14x19x29, m² de parede pronta", "2026-06")
PRECO_ARGAMASSA_KG = Preco(1.80, "Pesquisa de mercado - argamassa AC-II", "2026-06")
PRECO_TINTA_L = Preco(22.00, "Pesquisa de mercado - tinta acrílica premium", "2026-06")
PRECO_CIMENTO_SACO = Preco(44.00, "SINAPI/IBGE - média nacional, 1º bimestre/2026", "2026-06")
PRECO_AREIA_M3 = Preco(120.00, "Pesquisa de mercado - areia média/grossa", "2026-06")
PRECO_BRITA_M3 = Preco(140.00, "Pesquisa de mercado - brita nº 1", "2026-06")

# =====================================================================
# ITENS EXTRAS (reboco, impermeabilizacao, forro de gesso, rejunte) --
# ativados a partir do bloco ITENS_EXTRAS em core/sinapi_codigos.py
# para ampliar a cobertura de itens necessarios pra construir uma obra
# completa. reboco/impermeabilizacao/forro sao "composicao pronta por
# m2" (material+mao de obra, mesmo padrao de PRECO_BLOCO_CERAMICO);
# rejunte e "insumo por kg" (mesmo padrao de PRECO_ARGAMASSA_KG), por
# isso tem coeficiente de consumo proprio.
# =====================================================================
PRECO_REBOCO_M2 = Preco(
    60.09,
    "SINAPI oficial (CAIXA/IBGE) RR, ref. 2026-07 - soma de 2 composições "
    "(sem código único pro reboco completo): chapisco 87878 (R$6,81/m²) + "
    "emboço/massa única 87794 (R$53,28/m²), sem presença de vãos, preparo manual",
    "2026-07",
)
PRECO_IMPERMEABILIZACAO_M2 = Preco(55.00, "Pesquisa de mercado - impermeabilização de área molhada (manta asfáltica ou argamassa polimérica), material+mão de obra, m² aplicado", "2026-09")
PRECO_FORRO_GESSO_M2 = Preco(48.00, "Pesquisa de mercado - forro de gesso liso, material+mão de obra, m²", "2026-09")
CONSUMO_REJUNTE_KG_POR_M2 = Preco(0.4, "Padrão de mercado - rejunte para piso/revestimento cerâmico", "2026-09")
PRECO_REJUNTE_KG = Preco(12.00, "Pesquisa de mercado - rejunte cimentício/epóxi padrão médio", "2026-09")

# =====================================================================
# FATOR REGIONAL E ACO -- fixos para Roraima (RR), unico estado
# atendido pelo OrçaObra neste momento.
# =====================================================================
FATOR_REGIONAL_RR = Preco(
    1.070,
    "buscadorsinapi.com.br (CEF/IBGE) - média geral de RR sobre a média nacional",
    "2026-06",
)

PRECO_ACO_RR = Preco(
    9.38,
    "buscadorsinapi.com.br - insumo 32 (aço CA-50, 6,3mm, vergalhão), desonerado, RR",
    "2026-04",
)

# =====================================================================
# MAO DE OBRA POR SERVICO (valores medios de referencia nacional --
# SEMPRE editaveis pelo usuario na tela antes de gerar o orcamento)
#
# "Alvenaria (assentamento)", "Assentamento de Piso (Área Seca/
# Molhada)" e "Instalação de Porta Interna/Externa" foram removidos
# daqui em 2026-08: o material equivalente (bloco_ceramico, piso_seco,
# piso_molhado, porta_interna, porta_externa) já usa uma composição
# SINAPI completa com mão de obra embutida -- ver
# core/sinapi_codigos.py e core/calculator.py:calcular_mao_de_obra().
# Manter os dois contaria a mão de obra 2x.
# =====================================================================
_FONTE_MAO_DE_OBRA = "Aproximação a partir da parcela de mão de obra das composições SINAPI (ainda não coletado item a item)"
_DATA_MAO_DE_OBRA = "2026-06"

MAO_DE_OBRA_POR_SERVICO = {
    "Assentamento de Piso (Área Externa)": {
        "preco": Preco(
            26.00, _FONTE_MAO_DE_OBRA, _DATA_MAO_DE_OBRA
        ),
        "unidade": "m2_piso_externo",
    },
    "Pintura": {
        "preco": Preco(
            12.00, _FONTE_MAO_DE_OBRA, _DATA_MAO_DE_OBRA
        ),
        "unidade": "m2_parede",
    },
    "Instalação de Janela": {
        "preco": Preco(
            70.00, _FONTE_MAO_DE_OBRA, _DATA_MAO_DE_OBRA
        ),
        "unidade": "unidade",
    },
    "Execução de Cobertura": {
        "preco": Preco(
            45.00, _FONTE_MAO_DE_OBRA, _DATA_MAO_DE_OBRA
        ),
        "unidade": "m2_cobertura",
    },
    "Estrutura (fundação/armação)": {
        "preco": Preco(
            35.00, _FONTE_MAO_DE_OBRA, _DATA_MAO_DE_OBRA
        ),
        "unidade": "m2_area",
    },
    "Instalação Elétrica": {
        "preco": Preco(
            60.00, _FONTE_MAO_DE_OBRA, _DATA_MAO_DE_OBRA
        ),
        "unidade": "unidade",
    },
    "Instalação Hidráulica": {
        "preco": Preco(
            55.00, _FONTE_MAO_DE_OBRA, _DATA_MAO_DE_OBRA
        ),
        "unidade": "unidade",
    },
}


def data_mais_antiga() -> str:
    """Retorna a data_ref (AAAA-MM) mais antiga entre TODOS os precos e
coeficientes desta tabela -- ou seja, o quao "desatualizado" o dado
mais velho usado no motor de calculo esta."""
    datas_mao_de_obra = [info["preco"].data_ref for info in MAO_DE_OBRA_POR_SERVICO.values()]
    return min([
        _mais_antiga(
            CONSUMO_CIMENTO_SACO_POR_M2,
            CONSUMO_AREIA_M3_POR_M2, CONSUMO_BRITA_M3_POR_M2, CONSUMO_ACO_KG_POR_M2,
            CONSUMO_ARGAMASSA_KG_POR_M2, CONSUMO_TINTA_L_POR_M2,
            M2_POR_PONTO_ELETRICO, M2_POR_PONTO_HIDRAULICO, MARGEM_PERDA,
            PRECOS_PISO_SECO, PRECOS_PISO_MOLHADO, PRECOS_PISO_EXTERNO,
            PRECOS_PORTA_INTERNA, PRECOS_PORTA_EXTERNA, PRECOS_JANELA,
            PRECOS_PONTO_ELETRICO_INFRA, PRECOS_PONTO_ELETRICO_ACABAMENTO,
            PRECOS_PONTO_HIDRAULICO_INFRA, PRECOS_PONTO_HIDRAULICO_ACABAMENTO,
            PRECOS_COBERTURA["Telhado"], PRECOS_COBERTURA["Laje"],
            PRECO_BLOCO_CERAMICO, PRECO_ARGAMASSA_KG, PRECO_TINTA_L,
            PRECO_CIMENTO_SACO, PRECO_AREIA_M3, PRECO_BRITA_M3,
            FATOR_REGIONAL_RR, PRECO_ACO_RR,
            PRECO_REBOCO_M2, PRECO_IMPERMEABILIZACAO_M2, PRECO_FORRO_GESSO_M2,
            CONSUMO_REJUNTE_KG_POR_M2, PRECO_REJUNTE_KG,
        )
    ] + datas_mao_de_obra)
