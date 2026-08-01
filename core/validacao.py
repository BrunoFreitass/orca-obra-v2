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
