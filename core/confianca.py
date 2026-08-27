"""Pontuação de confiança da extração e heurística de plausibilidade da
metragem de parede -- lógica pura, sem dependência de UI, reaproveitável
por qualquer front-end (Streamlit hoje, API/React no futuro).

Realocado de core/ui_revisao.py em 2026-08 -- mesma lógica, sem mudança
de comportamento."""

CAMPOS_EXTRACAO = (
    "area_piso_seco", "area_piso_molhado", "area_piso_externo",
    "metros_parede", "portas_internas", "portas_externas", "janelas",
)

# Pesos para cálculo do índice global de confiança
PESO_CONFIANCA = {"alta": 3, "media": 2, "baixa": 1}


def calcular_indice_confianca(confianca: dict) -> dict:
    """Calcula o índice global de confiança (0–100%) com base nos 7 campos.
    Retorna dict com: percentual, nivel, cor, emoji, mensagem."""
    if not confianca:
        return {
            "percentual": 50,
            "nivel": "media",
            "cor": "#F9A825",
            "emoji": "🟡",
            "mensagem": "Confiança não avaliada pela IA",
        }

    total_pontos = 0
    maximo_pontos = 0
    for campo in CAMPOS_EXTRACAO:
        info = confianca.get(campo, {"nivel": "media"})
        nivel = info.get("nivel", "media")
        total_pontos += PESO_CONFIANCA.get(nivel, 2)
        maximo_pontos += 3  # máximo = alta (3)

    percentual = round((total_pontos / maximo_pontos) * 100) if maximo_pontos > 0 else 50

    if percentual >= 90:
        return {
            "percentual": percentual,
            "nivel": "alta",
            "cor": "#2E7D32",
            "emoji": "🟢",
            "mensagem": f"Confiabilidade da extração: {percentual}% — dados altamente confiáveis",
        }
    elif percentual >= 70:
        return {
            "percentual": percentual,
            "nivel": "media",
            "cor": "#F9A825",
            "emoji": "🟡",
            "mensagem": f"Confiabilidade da extração: {percentual}% — revise os campos em amarelo/vermelho",
        }
    else:
        return {
            "percentual": percentual,
            "nivel": "baixa",
            "cor": "#C62828",
            "emoji": "🔴",
            "mensagem": f"Confiabilidade da extração: {percentual}% — recomendamos revisar todos os dados na planta",
        }


def estimar_metros_parede(area_total: float, portas_internas: int) -> float:
    """Heurística: usa portas internas como proxy para número de divisões.
    Fator base 0.55 (studio) até 1.10 (muitas divisões)."""
    if area_total <= 0:
        return 0.0
    fator = 0.55 + min(portas_internas * 0.05, 0.55)
    fator = max(0.55, min(fator, 1.10))
    return round(area_total * fator, 2)


def validar_proporcao_parede(area_piso_total, metros_parede, portas_internas):
    """Verifica se a metragem de parede é plausível pra área de piso
    informada. Retorna (avisos: list[str], sugestao: float|None)."""
    avisos = []
    sugestao = None
    if area_piso_total <= 0 or metros_parede <= 0:
        return avisos, sugestao

    razao = metros_parede / area_piso_total
    minimo_razao = 0.55
    maximo_razao = 1.10
    minimo_esperado = round(area_piso_total * minimo_razao)
    maximo_esperado = round(area_piso_total * maximo_razao)
    sugestao_tipica = estimar_metros_parede(area_piso_total, portas_internas)

    if razao < minimo_razao:
        sugestao = sugestao_tipica
        impacto_min = round((sugestao_tipica - metros_parede) * 2.8 * 40)
        impacto_max = round((sugestao_tipica - metros_parede) * 2.8 * 55)
        avisos.append(
            f"""🧱 ATENÇÃO: Metros de parede SUBESTIMADOS

A IA leu **{metros_parede:.0f} m** de parede para **{area_piso_total:.0f} m²** de área.
O mínimo esperado é **{minimo_esperado} m** (máximo: {maximo_esperado} m).

👉 Sugestão: ajuste para ~{sugestao_tipica:.0f} m de parede, que é o típico para uma casa
de {area_piso_total:.0f} m² com {portas_internas} porta(s) interna(s).

_Se não ajustar, o orçamento ficará R$ {impacto_min:,} a R$ {impacto_max:,} mais barato do que deveria
(impacto em blocos, tinta e mão de obra)._"""
        )
    elif razao > maximo_razao:
        avisos.append(
            f"""🧱 ATENÇÃO: Metros de parede SUPerestimados

A IA leu **{metros_parede:.0f} m** de parede para **{area_piso_total:.0f} m²** de área.
O máximo esperado é **{maximo_esperado} m**. Confira se nenhuma parede foi contada duas vezes."""
        )

    return avisos, sugestao
