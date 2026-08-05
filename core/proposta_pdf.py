from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image, KeepTogether
)
from core.coeficientes import data_mais_antiga


def _agrupar_por_tipo(dados_orcamento):
    grupos = {}
    ordem = []
    for item in dados_orcamento:
        tipo = item.get("Tipo", "Itens")
        if tipo not in grupos:
            grupos[tipo] = []
            ordem.append(tipo)
        grupos[tipo].append(item)
    return ordem, grupos


def gerar_pdf_proposta(dados_orcamento, output_path, nome_projeto,
                        estado_uf, padrao, tipo_cobertura, area_piso,
                        bdi_percentual=0, nome_empresa="OrçaObra AI",
                        contato="", registro="", caminho_logo=""):
    """Gera uma proposta comercial em PDF, com capa e tabela resumida
    (sem quantidade/preco unitario por item -- so os totais por
    servico/material), pensada pra ser enviada ao cliente final.

    nome_empresa/contato/registro/caminho_logo: dados do profissional
    ou empresa que esta emitindo a proposta (ver core/perfil_empresa.py),
    pra personalizar o documento em vez de sair sempre com a marca
    "OrçaObra AI". Todos opcionais -- se nao informados, o PDF sai
    com a marca padrao e sem essas linhas de contato.

    Diferente do Excel (gerado por core/reporter.py), que mostra o
    detalhamento completo pra uso interno do profissional, o PDF e um
    documento de APRESENTACAO: mais limpo, com capa, e sem expor a
    composicao interna de custos linha a linha (o cliente ve o valor
    total de cada servico, nao a conta de "quantidade x preco unitario"
    que pode gerar questionamento ou negociacao item a item).
    """
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "TituloCapa", parent=styles["Title"], fontSize=24, spaceAfter=4,
        textColor=colors.HexColor("#1F4E78"),
    )
    estilo_subtitulo = ParagraphStyle(
        "SubtituloCapa", parent=styles["Normal"], fontSize=13,
        textColor=colors.HexColor("#4472A8"), spaceAfter=4,
    )
    estilo_contato = ParagraphStyle(
        "ContatoCapa", parent=styles["Normal"], fontSize=9,
        textColor=colors.HexColor("#666666"), spaceAfter=2,
    )
    estilo_secao = ParagraphStyle(
        "Secao", parent=styles["Heading2"], fontSize=13,
        textColor=colors.white, backColor=colors.HexColor("#4472A8"),
        spaceBefore=14, spaceAfter=6, leftIndent=6, borderPadding=6,
    )
    estilo_rodape = ParagraphStyle(
        "Rodape", parent=styles["Normal"], fontSize=8,
        textColor=colors.grey,
    )

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )
    story = []

    # --- Cabecalho: logo (se houver) + nome da empresa/profissional ---
    if caminho_logo:
        try:
            # Limita a largura maxima do logo pra nao dominar a pagina,
            # preservando a proporcao original da imagem.
            logo = Image(caminho_logo, width=4 * cm, height=4 * cm, kind="proportional")
            logo.hAlign = "LEFT"
            story.append(logo)
            story.append(Spacer(1, 8))
        except Exception:
            # Logo invalido/corrompido nao pode derrubar a geracao do
            # PDF inteiro -- ignora o logo e segue sem ele.
            pass

    story.append(Paragraph(nome_empresa or "OrçaObra AI", estilo_titulo))
    story.append(Paragraph("Proposta de Orçamento de Obra", estilo_subtitulo))

    linha_contato = " · ".join(parte for parte in (contato, registro) if parte)
    if linha_contato:
        story.append(Paragraph(linha_contato, estilo_contato))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#1F4E78"), thickness=1.2))
    story.append(Spacer(1, 16))

    dados_capa = [
        ["Projeto / Cliente:", nome_projeto],
        ["Data:", datetime.now().strftime("%d/%m/%Y")],
        ["Estado da Obra:", estado_uf],
        ["Padrão de Acabamento:", padrao],
        ["Tipo de Cobertura:", tipo_cobertura],
        ["Área de Piso:", f"{area_piso:.0f} m²"],
    ]
    tabela_capa = Table(dados_capa, colWidths=[5 * cm, 10 * cm])
    tabela_capa.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1F4E78")),
    ]))
    story.append(tabela_capa)
    story.append(Spacer(1, 20))

    # --- Tabela resumida por secao (Material / Mao de Obra), so com totais ---
    ordem_grupos, grupos = _agrupar_por_tipo(dados_orcamento)

    custo_direto = 0.0
    for tipo in ordem_grupos:
        # Monta a secao inteira em uma lista separada, depois envolve
        # em KeepTogether para evitar quebra no meio da tabela.
        elementos_secao = []
        elementos_secao.append(Paragraph(tipo.upper(), estilo_secao))

        linhas = [["Item", "Total (R$)"]]
        subtotal_grupo = 0.0
        for item in grupos[tipo]:
            linhas.append([item["Material"], f"R$ {item['Total']:,.2f}"])
            subtotal_grupo += item["Total"]
        linhas.append(["Subtotal", f"R$ {subtotal_grupo:,.2f}"])
        custo_direto += subtotal_grupo

        tabela = Table(linhas, colWidths=[11 * cm, 4 * cm])
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F2F2F2")]),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.HexColor("#1F4E78")),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elementos_secao.append(tabela)

        # KeepTogether: se a secao inteira (titulo + tabela) nao couber
        # no espaco restante da pagina atual, ela e jogada para a
        # proxima pagina inteira -- evitando a quebra no meio da tabela
        # que gerava lixo no PDF.
        story.append(KeepTogether(elementos_secao))

    story.append(Spacer(1, 16))

    # --- Bloco final: Custo Direto -> BDI -> Preco de Venda ---
    linhas_final = [["Custo Direto", f"R$ {custo_direto:,.2f}"]]
    if bdi_percentual:
        valor_bdi = custo_direto * bdi_percentual / 100
        preco_venda = custo_direto + valor_bdi
        linhas_final.append([f"BDI ({bdi_percentual:g}%)", f"R$ {valor_bdi:,.2f}"])
        linhas_final.append(["PREÇO DE VENDA", f"R$ {preco_venda:,.2f}"])

    tabela_final = Table(linhas_final, colWidths=[11 * cm, 4 * cm])
    estilo_final = [
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if bdi_percentual:
        estilo_final += [
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, -1), (-1, -1), 13),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#2E7D32")),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ]
    tabela_final.setStyle(TableStyle(estilo_final))
    story.append(tabela_final)

    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#CCCCCC"), thickness=0.6))
    story.append(Spacer(1, 6))
    ref_ano, ref_mes = data_mais_antiga().split("-")
    story.append(Paragraph(
        "Este documento é uma estimativa de custos gerada automaticamente e não "
        "substitui um orçamento detalhado de engenharia. Valores sujeitos a "
        "alteração conforme condições específicas da obra e negociação. "
        f"Preços de referência atualizados até {ref_mes}/{ref_ano} "
        "(SINAPI/IBGE e pesquisa de mercado).",
        estilo_rodape,
    ))

    doc.build(story)
    return output_path
