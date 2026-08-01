from core.models import DadosExtracao, ItemOrcamento, itens_para_dicts
from core.tabela_precos import obter_preco
from core.coeficientes import (
    CONSUMO_TIJOLO_POR_M2_PAREDE, CONSUMO_CIMENTO_SACO_POR_M2,
    CONSUMO_AREIA_M3_POR_M2, CONSUMO_BRITA_M3_POR_M2, CONSUMO_ACO_KG_POR_M2,
    M2_POR_PONTO_ELETRICO, M2_POR_PONTO_HIDRAULICO, MARGEM_PERDA,
    PRECOS_PISO_SECO, PRECOS_PISO_MOLHADO, PRECOS_PISO_EXTERNO,
    PRECOS_PORTA_INTERNA, PRECOS_PORTA_EXTERNA, PRECOS_JANELA,
    PRECOS_PONTO_ELETRICO, PRECOS_PONTO_HIDRAULICO, PRECOS_COBERTURA,
    PRECO_BLOCO_CERAMICO, PRECO_ARGAMASSA_KG, PRECO_TINTA_L,
    PRECO_CIMENTO_SACO, PRECO_AREIA_M3, PRECO_BRITA_M3,
    FATOR_REGIONAL_RR, PRECO_ACO_RR, MAO_DE_OBRA_POR_SERVICO,
)

# Os coeficientes/precos PADRAO (com fonte e data de referencia) vivem
# em core/coeficientes.py. Todo preco que o usuario pode customizar por
# planilha (ver core/tabela_precos.py) passa por obter_preco(chave, ...)
# antes de usar -- se houver uma customizacao salva, ela prevalece;
# senao, cai no padrao. Coeficientes de CONSUMO (quanto material por m2)
# nao sao customizaveis nesta v1.
#
# O fator regional e o preco do aco sao fixos para Roraima (RR) -- o
# OrçaObra atende apenas Boa Vista/RR neste momento, entao nao ha mais
# selecao de estado nem tabela por UF (ver core/coeficientes.py).


def _dados_extracao(dados) -> DadosExtracao:
    """Aceita tanto um DadosExtracao pronto quanto um dict cru (formato
    antigo), para nao quebrar chamadores externos durante a transicao."""
    return dados if isinstance(dados, DadosExtracao) else DadosExtracao.from_dict(dados)


def calcular_materiais(dados, padrao, tipo_cobertura="Telhado"):
    """Calcula os itens de MATERIAL do orcamento. Retorna uma lista de
    dicts (Tipo/Material/Quantidade/Preco_Unit/Total), formato esperado
    por core/reporter.py e core/proposta_pdf.py."""
    d = _dados_extracao(dados)

    fator_regional = FATOR_REGIONAL_RR.valor
    area_cobertura = d.area_cobertura(tipo_cobertura)
    margem = MARGEM_PERDA.valor
    preco_aco_real = obter_preco("aco", PRECO_ACO_RR).valor

    itens = [
        ItemOrcamento("Material", "Bloco Cerâmico 14x19x29",
                      round(d.area_parede * CONSUMO_TIJOLO_POR_M2_PAREDE.valor * margem),
                      obter_preco("bloco_ceramico", PRECO_BLOCO_CERAMICO).valor * fator_regional),
        ItemOrcamento("Material", f"Piso Interno - Área Seca ({padrao})",
                      round(d.area_piso_seco * margem, 2),
                      obter_preco(f"piso_seco__{padrao}", PRECOS_PISO_SECO[padrao]).valor * fator_regional),
        ItemOrcamento("Material", f"Piso Interno - Área Molhada ({padrao})",
                      round(d.area_piso_molhado * margem, 2),
                      obter_preco(f"piso_molhado__{padrao}", PRECOS_PISO_MOLHADO[padrao]).valor * fator_regional),
        ItemOrcamento("Material", f"Piso Externo ({padrao})",
                      round(d.area_piso_externo * margem, 2),
                      obter_preco(f"piso_externo__{padrao}", PRECOS_PISO_EXTERNO[padrao]).valor * fator_regional),
        ItemOrcamento("Material", "Argamassa AC-II",
                      round(d.area_piso_total * 5 * margem),  # 5kg por m2
                      obter_preco("argamassa", PRECO_ARGAMASSA_KG).valor * fator_regional),
        ItemOrcamento("Material", "Tinta Acrílica Premium",
                      round(d.area_parede * 0.4),  # 0.4L por m2 de parede
                      obter_preco("tinta", PRECO_TINTA_L).valor * fator_regional),
        ItemOrcamento("Material", f"Porta Interna ({padrao})",
                      d.portas_internas,
                      obter_preco(f"porta_interna__{padrao}", PRECOS_PORTA_INTERNA[padrao]).valor * fator_regional),
        ItemOrcamento("Material", f"Porta Externa ({padrao})",
                      d.portas_externas,
                      obter_preco(f"porta_externa__{padrao}", PRECOS_PORTA_EXTERNA[padrao]).valor * fator_regional),
        ItemOrcamento("Material", f"Janela ({padrao})",
                      d.janelas,
                      obter_preco(f"janela__{padrao}", PRECOS_JANELA[padrao]).valor * fator_regional),
        ItemOrcamento("Material", f"Cobertura em {tipo_cobertura} ({padrao})",
                      area_cobertura,
                      obter_preco(f"cobertura_{tipo_cobertura}__{padrao}",
                                  PRECOS_COBERTURA[tipo_cobertura][padrao]).valor * fator_regional),
        ItemOrcamento("Material", "Cimento (Fundação/Estrutura)",
                      round(d.area_piso_total * CONSUMO_CIMENTO_SACO_POR_M2.valor * margem),
                      obter_preco("cimento", PRECO_CIMENTO_SACO).valor * fator_regional),
        ItemOrcamento("Material", "Areia",
                      round(d.area_piso_total * CONSUMO_AREIA_M3_POR_M2.valor * margem, 2),
                      obter_preco("areia", PRECO_AREIA_M3).valor * fator_regional),
        ItemOrcamento("Material", "Brita",
                      round(d.area_piso_total * CONSUMO_BRITA_M3_POR_M2.valor * margem, 2),
                      obter_preco("brita", PRECO_BRITA_M3).valor * fator_regional),
        ItemOrcamento("Material", "Aço/Vergalhão",
                      round(d.area_piso_total * CONSUMO_ACO_KG_POR_M2.valor * margem),
                      preco_aco_real),
        ItemOrcamento("Material", f"Pontos Elétricos ({padrao})",
                      round(d.area_piso_total / M2_POR_PONTO_ELETRICO.valor),
                      obter_preco(f"ponto_eletrico__{padrao}", PRECOS_PONTO_ELETRICO[padrao]).valor * fator_regional),
        ItemOrcamento("Material", f"Pontos Hidráulicos ({padrao})",
                      round(d.area_piso_total / M2_POR_PONTO_HIDRAULICO.valor),
                      obter_preco(f"ponto_hidraulico__{padrao}", PRECOS_PONTO_HIDRAULICO[padrao]).valor * fator_regional),
    ]

    return itens_para_dicts(itens)


def calcular_mao_de_obra(dados, tipo_cobertura="Telhado"):
    """Gera as linhas de MAO DE OBRA por servico, com preco sugerido
    (baseado em composicoes SINAPI aproximadas -- ver core/coeficientes.py,
    customizavel via core/tabela_precos.py).

    Retorna uma lista de dicts no MESMO FORMATO de calcular_materiais(),
    para poder ser concatenada num unico orcamento. O preco de cada
    linha e so uma SUGESTAO inicial -- a tela (app.py) deve deixar o
    usuario editar cada Preco_Unit, ja que mao de obra varia por equipe.
    """
    d = _dados_extracao(dados)
    fator_regional = FATOR_REGIONAL_RR.valor
    area_cobertura = d.area_cobertura(tipo_cobertura)

    quantidades = {
        "Alvenaria (assentamento)": d.area_parede,
        "Assentamento de Piso (Área Seca)": d.area_piso_seco,
        "Assentamento de Piso (Área Molhada)": d.area_piso_molhado,
        "Assentamento de Piso (Área Externa)": d.area_piso_externo,
        "Pintura": d.area_parede,
        "Instalação de Porta Interna": d.portas_internas,
        "Instalação de Porta Externa": d.portas_externas,
        "Instalação de Janela": d.janelas,
        "Execução de Cobertura": area_cobertura,
        "Estrutura (fundação/armação)": d.area_piso_total,
        "Instalação Elétrica": round(d.area_piso_total / M2_POR_PONTO_ELETRICO.valor),
        "Instalação Hidráulica": round(d.area_piso_total / M2_POR_PONTO_HIDRAULICO.valor),
    }

    itens = [
        ItemOrcamento("Mão de Obra", servico, quantidades.get(servico, 0),
                      round(obter_preco(f"mao_de_obra__{servico}", info["preco"]).valor * fator_regional, 2))
        for servico, info in MAO_DE_OBRA_POR_SERVICO.items()
    ]

    return itens_para_dicts(itens)
