from core.coeficientes import (
    CONSUMO_ACO_KG_POR_M2,
    CONSUMO_AREIA_M3_POR_M2,
    CONSUMO_ARGAMASSA_KG_POR_M2,
    CONSUMO_BRITA_M3_POR_M2,
    CONSUMO_CIMENTO_SACO_POR_M2,
    CONSUMO_TINTA_L_POR_M2,
    FATOR_REGIONAL_RR,
    M2_POR_PONTO_ELETRICO,
    M2_POR_PONTO_HIDRAULICO,
    MAO_DE_OBRA_POR_SERVICO,
    MARGEM_PERDA,
    PRECO_ACO_RR,
    PRECO_AREIA_M3,
    PRECO_ARGAMASSA_KG,
    PRECO_BLOCO_CERAMICO,
    PRECO_BRITA_M3,
    PRECO_CIMENTO_SACO,
    PRECO_TINTA_L,
    PRECOS_COBERTURA,
    PRECOS_JANELA,
    PRECOS_PISO_EXTERNO,
    PRECOS_PISO_MOLHADO,
    PRECOS_PISO_SECO,
    PRECOS_PONTO_ELETRICO_ACABAMENTO,
    PRECOS_PONTO_ELETRICO_INFRA,
    PRECOS_PONTO_HIDRAULICO_ACABAMENTO,
    PRECOS_PONTO_HIDRAULICO_INFRA,
    PRECOS_PORTA_EXTERNA,
    PRECOS_PORTA_INTERNA,
)
from core.models import DadosExtracao, ItemOrcamento, itens_para_dicts
from core.tabela_precos import obter_preco


def _dados_extracao(dados) -> DadosExtracao:
    """Aceita tanto um DadosExtracao pronto quanto um dict cru."""
    return dados if isinstance(dados, DadosExtracao) else DadosExtracao.from_dict(dados)


def calcular_materiais(dados, padrao, tipo_cobertura="Telhado"):
    """Calcula os itens de MATERIAL do orcamento."""
    d = _dados_extracao(dados)

    fator_regional = FATOR_REGIONAL_RR.valor
    area_cobertura = d.area_cobertura(tipo_cobertura)
    margem = MARGEM_PERDA.valor
    preco_aco_real = obter_preco("aco", PRECO_ACO_RR).valor
    qtd_pontos_eletricos = round(d.area_piso_total / M2_POR_PONTO_ELETRICO.valor)
    qtd_pontos_hidraulicos = round(d.area_piso_total / M2_POR_PONTO_HIDRAULICO.valor)

    itens = [
        # === OBRA BRUTA ===
        # Quantidade em m² de parede (não nº de tijolos): PRECO_BLOCO_CERAMICO
        # e a composição SINAPI "bloco_ceramico" já são preço por m² de
        # parede pronta (material + mão de obra de assentamento), não
        # preço por tijolo -- ver comentário de PRECO_BLOCO_CERAMICO em
        # coeficientes.py.
        ItemOrcamento("Material", "Bloco Cerâmico 14x19x29",
                      round(d.area_parede * margem, 2),
                      obter_preco("bloco_ceramico", PRECO_BLOCO_CERAMICO).valor * fator_regional,
                      fase="Obra Bruta"),
        ItemOrcamento("Material", f"Piso Interno - Área Seca ({padrao})",
                      round(d.area_piso_seco * margem, 2),
                      obter_preco(f"piso_seco__{padrao}", PRECOS_PISO_SECO[padrao]).valor * fator_regional,
                      fase="Acabamento"),
        ItemOrcamento("Material", f"Piso Interno - Área Molhada ({padrao})",
                      round(d.area_piso_molhado * margem, 2),
                      obter_preco(f"piso_molhado__{padrao}", PRECOS_PISO_MOLHADO[padrao]).valor * fator_regional,
                      fase="Acabamento"),
        ItemOrcamento("Material", f"Piso Externo ({padrao})",
                      round(d.area_piso_externo * margem, 2),
                      obter_preco(f"piso_externo__{padrao}", PRECOS_PISO_EXTERNO[padrao]).valor * fator_regional,
                      fase="Acabamento"),
        ItemOrcamento("Material", "Argamassa AC-II",
                      round(d.area_piso_total * CONSUMO_ARGAMASSA_KG_POR_M2.valor * margem),
                      obter_preco("argamassa", PRECO_ARGAMASSA_KG).valor * fator_regional,
                      fase="Acabamento"),
        ItemOrcamento("Material", "Tinta Acrílica Premium",
                      round(d.area_parede * CONSUMO_TINTA_L_POR_M2.valor),
                      obter_preco("tinta", PRECO_TINTA_L).valor * fator_regional,
                      fase="Acabamento"),
        ItemOrcamento("Material", f"Porta Interna ({padrao})",
                      d.portas_internas,
                      obter_preco(f"porta_interna__{padrao}", PRECOS_PORTA_INTERNA[padrao]).valor * fator_regional,
                      fase="Acabamento"),
        ItemOrcamento("Material", f"Porta Externa ({padrao})",
                      d.portas_externas,
                      obter_preco(f"porta_externa__{padrao}", PRECOS_PORTA_EXTERNA[padrao]).valor * fator_regional,
                      fase="Acabamento"),
        ItemOrcamento("Material", f"Janela ({padrao})",
                      d.janelas,
                      obter_preco(f"janela__{padrao}", PRECOS_JANELA[padrao]).valor * fator_regional,
                      fase="Acabamento"),
        ItemOrcamento("Material", f"Cobertura em {tipo_cobertura} ({padrao})",
                      area_cobertura,
                      obter_preco(f"cobertura_{tipo_cobertura}__{padrao}",
                                  PRECOS_COBERTURA[tipo_cobertura][padrao]).valor * fator_regional,
                      fase="Obra Bruta"),
        ItemOrcamento("Material", "Cimento (Fundação/Estrutura)",
                      round(d.area_piso_total * CONSUMO_CIMENTO_SACO_POR_M2.valor * margem),
                      obter_preco("cimento", PRECO_CIMENTO_SACO).valor * fator_regional,
                      fase="Obra Bruta"),
        ItemOrcamento("Material", "Areia",
                      round(d.area_piso_total * CONSUMO_AREIA_M3_POR_M2.valor * margem, 2),
                      obter_preco("areia", PRECO_AREIA_M3).valor * fator_regional,
                      fase="Obra Bruta"),
        ItemOrcamento("Material", "Brita",
                      round(d.area_piso_total * CONSUMO_BRITA_M3_POR_M2.valor * margem, 2),
                      obter_preco("brita", PRECO_BRITA_M3).valor * fator_regional,
                      fase="Obra Bruta"),
        ItemOrcamento("Material", "Aço/Vergalhão",
                      round(d.area_piso_total * CONSUMO_ACO_KG_POR_M2.valor * margem),
                      preco_aco_real,
                      fase="Obra Bruta"),
        # --- Elétrica: split infra (obra bruta) + acabamento ---
        ItemOrcamento("Material", f"Pontos Elétricos - Infraestrutura ({padrao})",
                      qtd_pontos_eletricos,
                      obter_preco(f"ponto_eletrico_infra__{padrao}",
                                  PRECOS_PONTO_ELETRICO_INFRA[padrao]).valor * fator_regional,
                      fase="Obra Bruta"),
        ItemOrcamento("Material", f"Pontos Elétricos - Acabamento ({padrao})",
                      qtd_pontos_eletricos,
                      obter_preco(f"ponto_eletrico_acabamento__{padrao}",
                                  PRECOS_PONTO_ELETRICO_ACABAMENTO[padrao]).valor * fator_regional,
                      fase="Acabamento"),
        # --- Hidráulica: split infra (obra bruta) + acabamento ---
        ItemOrcamento("Material", f"Pontos Hidráulicos - Infraestrutura ({padrao})",
                      qtd_pontos_hidraulicos,
                      obter_preco(f"ponto_hidraulico_infra__{padrao}",
                                  PRECOS_PONTO_HIDRAULICO_INFRA[padrao]).valor * fator_regional,
                      fase="Obra Bruta"),
        ItemOrcamento("Material", f"Pontos Hidráulicos - Acabamento ({padrao})",
                      qtd_pontos_hidraulicos,
                      obter_preco(f"ponto_hidraulico_acabamento__{padrao}",
                                  PRECOS_PONTO_HIDRAULICO_ACABAMENTO[padrao]).valor * fator_regional,
                      fase="Acabamento"),
    ]

    return itens_para_dicts(itens)


def calcular_mao_de_obra(dados, tipo_cobertura="Telhado"):
    """Gera as linhas de MAO DE OBRA por servico.

    Servicos cujo material equivalente ja e' uma composicao SINAPI
    completa (material + mao de obra embutidos -- ver GRUPOS_POR_PADRAO
    e MATERIAIS_SIMPLES em core/sinapi_codigos.py) NAO geram linha
    aqui, pra nao contar a mao de obra 2x: 1x embutida no preco do
    material, 1x aqui como estimativa separada. "Execução de Cobertura"
    e' condicional -- so' fica redundante quando tipo_cobertura="Telhado"
    (cobertura_Laje ainda nao tem composicao SINAPI mapeada, entao
    continua precisando da mao de obra em separado)."""
    d = _dados_extracao(dados)
    fator_regional = FATOR_REGIONAL_RR.valor
    area_cobertura = d.area_cobertura(tipo_cobertura)
    qtd_eletricos = round(d.area_piso_total / M2_POR_PONTO_ELETRICO.valor)
    qtd_hidraulicos = round(d.area_piso_total / M2_POR_PONTO_HIDRAULICO.valor)

    # Mapeamento de servico -> (quantidade, fase)
    servicos_base = {
        "Assentamento de Piso (Área Externa)": (d.area_piso_externo, "Acabamento"),
        "Pintura": (d.area_parede, "Acabamento"),
        "Instalação de Janela": (d.janelas, "Acabamento"),
        "Estrutura (fundação/armação)": (d.area_piso_total, "Obra Bruta"),
    }
    if tipo_cobertura != "Telhado":
        servicos_base["Execução de Cobertura"] = (area_cobertura, "Obra Bruta")

    itens = []
    for servico, (qtd, fase) in servicos_base.items():
        info = MAO_DE_OBRA_POR_SERVICO[servico]
        itens.append(ItemOrcamento(
            "Mão de Obra", servico, qtd,
            round(obter_preco(f"mao_de_obra__{servico}", info["preco"]).valor * fator_regional, 2),
            fase=fase
        ))

    # Split elétrico: infra (obra bruta) + acabamento
    # Usa obter_preco() (em vez do Preco padrão direto) para respeitar
    # preços customizados que o usuário tenha enviado pela planilha de
    # preços (core/tabela_precos.py) -- do contrário essa customização
    # era salva, mas nunca aplicada aqui.
    preco_eletrico_base = obter_preco(
        "mao_de_obra__Instalação Elétrica",
        MAO_DE_OBRA_POR_SERVICO["Instalação Elétrica"]["preco"],
    )
    # 60% infra / 40% acabamento (proporção aproximada do mercado)
    itens.append(ItemOrcamento(
        "Mão de Obra", "Instalação Elétrica - Infraestrutura", qtd_eletricos,
        round(preco_eletrico_base.valor * 0.60 * fator_regional, 2),
        fase="Obra Bruta"
    ))
    itens.append(ItemOrcamento(
        "Mão de Obra", "Instalação Elétrica - Acabamento", qtd_eletricos,
        round(preco_eletrico_base.valor * 0.40 * fator_regional, 2),
        fase="Acabamento"
    ))

    # Split hidráulico: infra (obra bruta) + acabamento
    preco_hidraulico_base = obter_preco(
        "mao_de_obra__Instalação Hidráulica",
        MAO_DE_OBRA_POR_SERVICO["Instalação Hidráulica"]["preco"],
    )
    itens.append(ItemOrcamento(
        "Mão de Obra", "Instalação Hidráulica - Infraestrutura", qtd_hidraulicos,
        round(preco_hidraulico_base.valor * 0.60 * fator_regional, 2),
        fase="Obra Bruta"
    ))
    itens.append(ItemOrcamento(
        "Mão de Obra", "Instalação Hidráulica - Acabamento", qtd_hidraulicos,
        round(preco_hidraulico_base.valor * 0.40 * fator_regional, 2),
        fase="Acabamento"
    ))

    return itens_para_dicts(itens)
