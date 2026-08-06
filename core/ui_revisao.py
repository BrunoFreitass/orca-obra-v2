"""Tela de revisão dos dados extraídos da planta — blocos de campos com validação
e modo confirmado/recolhido."""

import streamlit as st

from core.models import DadosExtracao
from core.validacao import validar_dados


CONFIANCA_VISUAL = {
    "alta": {"emoji": "🟢", "label": "Confiança alta"},
    "media": {"emoji": "🟡", "label": "Confiança média"},
    "baixa": {"emoji": "🔴", "label": "Confiança baixa — revise"},
}

CAMPOS_EXTRACAO = (
    "area_piso_seco", "area_piso_molhado", "area_piso_externo",
    "metros_parede", "portas_internas", "portas_externas", "janelas",
)


def _chave_metros_parede():
    """Retorna a key atual do widget de metros de parede. É uma key
    dinâmica (versionada) de propósito: usar sempre a mesma key fixa
    e torcer pra Streamlit reaplicar o "value=" depois de um
    st.session_state.pop(...) se mostrou frágil na prática (o widget
    às vezes reaparece com o valor antigo). Ao MUDAR o nome da key
    (incrementando a versão), forçamos o Streamlit a tratar o campo
    como um widget novo, que nunca existiu em session_state antes —
    isso garante que o "value=" passado seja sempre respeitado."""
    versao = st.session_state.get("parede_key_versao", 0)
    return f"input_metros_parede_v{versao}"


def _badge(campo, confianca):
    info = (confianca or {}).get(campo, {"nivel": "media", "motivo": ""})
    nivel = info.get("nivel", "media")
    visual = CONFIANCA_VISUAL.get(nivel, CONFIANCA_VISUAL["media"])
    motivo = info.get("motivo", "")
    st.caption(f"{visual['emoji']} {visual['label']}" + (f" — {motivo}" if motivo else ""))


def _estimar_metros_parede(area_total: float, portas_internas: int) -> float:
    """Heurística melhorada: usa portas internas como proxy para número de divisões.
    Fator base 0.55 (studio) até 1.10 (muitas divisões)."""
    if area_total <= 0:
        return 0.0
    fator = 0.55 + min(portas_internas * 0.05, 0.55)
    fator = max(0.55, min(fator, 1.10))
    return round(area_total * fator, 2)


def _validar_proporcao_parede(area_piso_total, metros_parede, portas_internas):
    avisos = []
    sugestao = None
    if area_piso_total <= 0 or metros_parede <= 0:
        return avisos, sugestao

    razao = metros_parede / area_piso_total
    minimo_razao = 0.55
    maximo_razao = 1.10
    minimo_esperado = round(area_piso_total * minimo_razao)
    maximo_esperado = round(area_piso_total * maximo_razao)
    sugestao_tipica = _estimar_metros_parede(area_piso_total, portas_internas)

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


def _renderizar_bloco_areas(dados_extraidos, confianca, confirmado):
    """Renderiza o bloco de áreas de piso."""
    wrapper = st.expander if confirmado else lambda title, **kw: st.container(border=True)
    with wrapper("🏠 Áreas de Piso (m²)", expanded=False):
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            area_piso_seco = st.number_input(
                "Área Seca",
                value=float(dados_extraidos.get("area_piso_seco") or 0),
                step=0.5, min_value=0.0,
                key="input_area_seca",
                help="Sala, quartos, cozinha, corredores — ambientes sem ponto de água",
            )
            _badge("area_piso_seco", confianca)

        with col_a2:
            area_piso_molhado = st.number_input(
                "Área Molhada",
                value=float(dados_extraidos.get("area_piso_molhado") or 0),
                step=0.5, min_value=0.0,
                key="input_area_molhada",
                help="Banheiros, área de serviço, lavabo — ambientes com ponto de água",
            )
            _badge("area_piso_molhado", confianca)

        with col_a3:
            area_piso_externo = st.number_input(
                "Área Externa",
                value=float(dados_extraidos.get("area_piso_externo") or 0),
                step=0.5, min_value=0.0,
                key="input_area_externa",
                help="Varanda, garagem, área externa coberta — ambientes semi-descobertos",
            )
            _badge("area_piso_externo", confianca)

        preview = DadosExtracao(
            area_piso_seco=area_piso_seco,
            area_piso_molhado=area_piso_molhado,
            area_piso_externo=area_piso_externo,
            metros_parede=0, portas_internas=0, portas_externas=0, janelas=0,
        )
        st.caption(f"**Área total de piso:** {preview.area_piso_total:.1f} m²")

    return area_piso_seco, area_piso_molhado, area_piso_externo


def _renderizar_bloco_paredes(dados_extraidos, confianca, confirmado):
    """Renderiza o bloco de paredes."""
    wrapper = st.expander if confirmado else lambda title, **kw: st.container(border=True)
    with wrapper("🧱 Vedação", expanded=False):
        metros_parede = st.number_input(
            "Metros lineares de parede",
            value=float(dados_extraidos.get("metros_parede") or 0),
            step=0.5,
            key=_chave_metros_parede(),
            help="Soma do perímetro de todos os cômodos, contando cada parede interna apenas uma vez",
        )
        _badge("metros_parede", confianca)
    return metros_parede


def _renderizar_bloco_aberturas(dados_extraidos, confianca, confirmado):
    """Renderiza o bloco de aberturas."""
    wrapper = st.expander if confirmado else lambda title, **kw: st.container(border=True)
    with wrapper("🚪 Aberturas (unidades)", expanded=False):
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            portas_internas = st.number_input(
                "Portas Internas",
                value=int(dados_extraidos.get("portas_internas") or 0),
                step=1, min_value=0,
                key="input_portas_internas",
                help="Portas que ligam dois ambientes internos",
            )
            _badge("portas_internas", confianca)

        with col_p2:
            portas_externas = st.number_input(
                "Portas Externas",
                value=int(dados_extraidos.get("portas_externas") or 0),
                step=1, min_value=0,
                key="input_portas_externas",
                help="Portas de entrada, fundos ou acesso a área externa",
            )
            _badge("portas_externas", confianca)

        with col_p3:
            janelas = st.number_input(
                "Janelas",
                value=int(dados_extraidos.get("janelas") or 0),
                step=1, min_value=0,
                key="input_janelas",
                help="Total de janelas na planta (incluindo banheiro e cozinha)",
            )
            _badge("janelas", confianca)

    return portas_internas, portas_externas, janelas


def renderizar_revisao(dados_extraidos: dict, padrao: str, estrutura: str, local_obra: str):
    """Renderiza a tela de revisão dos dados e retorna o DadosExtracao validado."""
    confianca = dados_extraidos.get("confianca", {})
    confirmado = st.session_state.get("dados_revisao_confirmados", False)

    st.header("📊 Revisão dos Dados Extraídos")
    st.caption("Confira os valores lidos pela IA antes de gerar o orçamento. Ajuste se necessário.")

    # KPIs
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.metric("Padrão selecionado", padrao)
    with col_kpi2:
        st.metric("Cobertura", estrutura)
    with col_kpi3:
        st.metric("Local da obra", local_obra)

    st.divider()

    # -----------------------------------------------------------------
    # MODO CONFIRMADO: resumo compacto + botão de editar
    # -----------------------------------------------------------------
    if confirmado:
        st.success("✅ Dados confirmados. Revise abaixo se necessário.")

        # Resumo em cards
        area_total_atual = (
            float(st.session_state.get("input_area_seca", 0))
            + float(st.session_state.get("input_area_molhada", 0))
            + float(st.session_state.get("input_area_externa", 0))
        )
        parede_atual = float(st.session_state.get(_chave_metros_parede(), 0))
        pi = int(st.session_state.get("input_portas_internas", 0))
        pe = int(st.session_state.get("input_portas_externas", 0))
        jan = int(st.session_state.get("input_janelas", 0))

        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        col_r1.metric("Área Total", f"{area_total_atual:.1f} m²")
        col_r2.metric("Paredes", f"{parede_atual:.1f} m")
        col_r3.metric("Portas", f"{pi + pe} un")
        col_r4.metric("Janelas", f"{jan} un")

        if st.button("✏️ Reabrir para Edição", use_container_width=True, key="btn_reabrir_edicao"):
            st.session_state["dados_revisao_confirmados"] = False
            st.rerun()

        st.divider()

    # -----------------------------------------------------------------
    # BLOCOS DE CAMPOS (abertos se não confirmado, dentro de expander se confirmado)
    # -----------------------------------------------------------------
    area_piso_seco, area_piso_molhado, area_piso_externo = _renderizar_bloco_areas(
        dados_extraidos, confianca, confirmado
    )

    if not confirmado:
        st.divider()

    metros_parede = _renderizar_bloco_paredes(dados_extraidos, confianca, confirmado)

    if not confirmado:
        st.divider()

    portas_internas, portas_externas, janelas = _renderizar_bloco_aberturas(
        dados_extraidos, confianca, confirmado
    )

    # Avisos de confiança baixa
    campos_baixa = [
        campo for campo in CAMPOS_EXTRACAO
        if confianca.get(campo, {}).get("nivel") == "baixa"
    ]
    if campos_baixa:
        st.warning(
            "🔴 A IA teve baixa confiança em algum(ns) campo(s) acima. "
            "Recomendamos conferir esses valores direto na planta antes de prosseguir."
        )

    # Modelo de domínio
    dados_extracao = DadosExtracao(
        area_piso_seco=area_piso_seco,
        area_piso_molhado=area_piso_molhado,
        area_piso_externo=area_piso_externo,
        metros_parede=metros_parede,
        portas_internas=portas_internas,
        portas_externas=portas_externas,
        janelas=janelas,
    )
    area_piso_total = dados_extracao.area_piso_total

    # Validação proporção parede (heurística melhorada)
    avisos_parede, sugestao_parede = _validar_proporcao_parede(
        area_piso_total, metros_parede, portas_internas
    )
    for aviso in avisos_parede:
        st.error(aviso)

    if sugestao_parede and sugestao_parede != metros_parede:
        col_ajuste1, col_ajuste2 = st.columns([1, 3])
        with col_ajuste1:
            if st.button(f"⚡ Ajustar para {sugestao_parede:.0f} m", key="btn_ajuste_parede"):
                st.session_state["dados_extraidos"]["metros_parede"] = sugestao_parede
                # Em vez de popar a key fixa (frágil — o campo às vezes voltava
                # com o valor antigo mesmo assim), trocamos o NOME da key
                # incrementando a versão. Isso força o Streamlit a criar um
                # widget genuinamente novo, que nunca existiu em
                # session_state, então o "value=" novo é sempre respeitado.
                st.session_state["parede_key_versao"] = st.session_state.get("parede_key_versao", 0) + 1
                st.session_state.pop("orcamento_assinatura", None)
                st.session_state["dados_revisao_confirmados"] = False
                st.rerun()
        with col_ajuste2:
            st.caption("Clique para aplicar a sugestão automaticamente (pode editar depois).")

    # Validação geral
    avisos = validar_dados({
        "area_piso": area_piso_total,
        "metros_parede": metros_parede,
        "portas": dados_extracao.portas_total,
        "janelas": janelas,
    })
    if avisos:
        st.warning(
            "⚠️ Alguns valores parecem incomuns. Confira antes de gerar o orçamento:\n\n"
            + "\n".join(f"- {aviso}" for aviso in avisos)
        )

    # Botão de confirmar (só aparece se não confirmado)
    if not confirmado:
        st.divider()
        if st.button("✅ Confirmar Dados e Prosseguir", type="primary", use_container_width=True, key="btn_confirmar_dados"):
            st.session_state["dados_revisao_confirmados"] = True
            st.rerun()
        st.caption("Após confirmar, os campos serão recolhidos e você poderá focar no orçamento.")

    st.divider()

    # Assinatura para recalcular materiais/mão de obra
    assinatura_atual = (
        padrao, estrutura, area_piso_seco, area_piso_molhado,
        area_piso_externo, metros_parede, portas_internas,
        portas_externas, janelas,
    )
    if st.session_state.get("orcamento_assinatura") != assinatura_atual:
        st.session_state.pop("materiais_editados", None)
        st.session_state.pop("mao_de_obra_editada", None)
        st.session_state["orcamento_assinatura"] = assinatura_atual
        # Se os dados mudaram, resetar confirmação para forçar revisão
        if confirmado:
            st.session_state["dados_revisao_confirmados"] = False
            st.rerun()

    return dados_extracao
