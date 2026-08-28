# Faixas plausiveis para uma planta residencial/comercial tipica.
# Valores fora daqui nao sao necessariamente errados (obras grandes
# existem), mas sao raros o suficiente para merecer uma conferencia
# manual antes de gerar o orcamento.
FAIXAS = {
    "area_piso": (5, 2000),       # m2
    "metros_parede": (5, 2000),   # m lineares
    "portas": (0, 50),            # unidades
    "janelas": (0, 100),          # unidades
}

NOMES_EXIBICAO = {
    "area_piso": "Área de Piso",
    "metros_parede": "Paredes Lineares",
    "portas": "Portas",
    "janelas": "Janelas",
}


def validar_dados(dados):
    """Confere se os valores extraidos estao dentro de uma faixa plausivel.
    Retorna uma lista de avisos (strings). Lista vazia = tudo dentro do
    esperado. Nao bloqueia o fluxo -- so alerta, ja que o usuario pode
    corrigir os campos manualmente antes de gerar o orcamento."""
    avisos = []

    for campo, (minimo, maximo) in FAIXAS.items():
        valor = dados.get(campo)
        nome = NOMES_EXIBICAO[campo]

        if valor is None:
            avisos.append(f"{nome} não foi retornado pela IA.")
            continue

        if valor < 0:
            avisos.append(f"{nome} veio negativo ({valor}) — provavelmente um erro de leitura.")
        elif valor == 0 and minimo > 0:
            # So alerta "zerado" quando o proprio campo NAO admite 0 como
            # valor plausivel (ex: area de piso). Para campos cuja faixa
            # comeca em 0 (portas, janelas), zero e um resultado legitimo
            # e nao deveria gerar aviso.
            avisos.append(f"{nome} veio zerado — confira se a planta foi lida corretamente.")
        elif valor < minimo:
            avisos.append(f"{nome} está bem abaixo do esperado ({valor}) — vale conferir.")
        elif valor > maximo:
            avisos.append(f"{nome} está bem acima do esperado ({valor}) — vale conferir.")

    return avisos


TOLERANCIA_AREA_TOTAL_PLANTA = 0.10  # 10% de divergência aceitável (paredes, arredondamento)


def validar_area_total_planta(dados: dict) -> dict:
    """Confere a área total impressa na planta (quando a IA achou uma,
    em area_total_planta) contra a soma das 3 categorias de área
    (area_piso_seco + area_piso_molhado + area_piso_externo). Diverge
    mais que a tolerância -> rebaixa a confiança das 3 áreas pra
    "baixa", mas NAO altera os valores -- quem decide e o engenheiro
    na tela de revisao.

    Se a planta nao tinha area total impressa (area_total_planta == 0,
    caso mais comum) ou nao ha soma de ambientes pra comparar, nao
    mexe em nada.
    """
    area_total_planta = dados.get("area_total_planta") or 0
    area_soma_ambientes = (
        (dados.get("area_piso_seco") or 0)
        + (dados.get("area_piso_molhado") or 0)
        + (dados.get("area_piso_externo") or 0)
    )

    if area_total_planta <= 0 or area_soma_ambientes <= 0:
        return dados

    divergencia = abs(area_total_planta - area_soma_ambientes) / area_total_planta

    if divergencia > TOLERANCIA_AREA_TOTAL_PLANTA:
        if "confianca" not in dados:
            dados["confianca"] = {}
        motivo = (
            f"Área total da planta ({area_total_planta:.1f}m²) diverge "
            f"{divergencia*100:.0f}% da soma dos ambientes ({area_soma_ambientes:.1f}m²). "
            "Revise na tela seguinte."
        )
        for campo in ("area_piso_seco", "area_piso_molhado", "area_piso_externo"):
            dados["confianca"][campo] = {"nivel": "baixa", "motivo": motivo}

    return dados
