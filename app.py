import os
import tempfile

import streamlit as st

from config import LOCAL_OBRA
from core import orcamento_service, paths, tabela_precos
from core.calculator import calcular_mao_de_obra, calcular_materiais
from core.historico import (
    excluir_orcamento,
    inicializar_db,
    listar_orcamentos,
    salvar_orcamento,
)
from core.models import DadosExtracao
from core.monitor_api import inicializar_tabela_monitor, status_cota
from core.perfil_empresa import carregar_perfil, salvar_perfil
from core.proposta_pdf import gerar_pdf_proposta
from core.reporter import gerar_excel
from core.validacao import validar_dados
from core.vision import ErroExtracaoAmigavel, extrair_dados_da_planta

# =====================================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================================
st.set_page_config(
    page_title="OrçaObra AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# CSS CUSTOM
# =====================================================================
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #e9ecef;
    }
    div[data-testid="stMetric"] > div:first-child {
        font-weight: 600 !important;
        color: #1F4E78 !important;
    }
    .stButton>button[kind="primary"] {
        background-color: #1F4E78;
        color: white;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
        width: 100%;
    }
    .stButton>button {
        border-radius: 8px;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem;
    }
    .stAlert {
        border-radius: 8px !important;
    }
    /* Títulos mais limpos */
    h1, h2, h3 {
        color: #1F4E78 !important;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# INICIALIZAÇÃO
# =====================================================================
inicializar_db()
inicializar_tabela_monitor()

paths.garantir_diretorios()
PASTA_ORCAMENTOS = paths.PASTA_ORCAMENTOS
PASTA_PERFIL = paths.PASTA_PERFIL

CONFIANCA_VISUAL = {
    "alta": {"emoji": "🟢", "label": "Confiança alta"},
    "media": {"emoji": "🟡", "label": "Confiança média"},
    "baixa": {"emoji": "🔴", "label": "Confiança baixa — revise"},
}

CAMPOS_EXTRACAO = (
    "area_piso_seco", "area_piso_molhado", "area_piso_externo",
    "metros_parede", "portas_internas", "portas_externas", "janelas",
)


# =====================================================================
# FUNÇÕES AUXILIARES
# =====================================================================
def badge_confianca(campo, confianca):
    info = (confianca or {}).get(campo, {"nivel": "media", "motivo": ""})
    nivel = info.get("nivel", "media")
    visual = CONFIANCA_VISUAL.get(nivel, CONFIANCA_VISUAL["media"])
    return visual, info.get("motivo", "")


def mostrar_badge(campo, confianca):
    visual, motivo = badge_confianca(campo, confianca)
    st.caption(f"{visual['emoji']} {visual['label']}" + (f" — {motivo}" if motivo else ""))


def validar_proporcao_parede(area_piso_total, metros_parede):
    avisos = []
    sugestao = None
    if area_piso_total <= 0 or metros_parede <= 0:
        return avisos, sugestao

    razao = metros_parede / area_piso_total
    minimo_razao = 0.55
    maximo_razao = 1.10
    minimo_esperado = round(area_piso_total * minimo_razao)
    maximo_esperado = round(area_piso_total * maximo_razao)
    sugestao_tipica = round(area_piso_total * 0.75)

    if razao < minimo_razao:
        sugestao = sugestao_tipica
        avisos.append(
            f"🧱 ATENÇÃO: Metros de parede SUBESTIMADOS\n\n"
            f"A IA leu **{metros_parede:.0f} m** de parede para **{area_piso_total:.0f} m²** de área. "
            f"O mínimo esperado é **{minimo_esperado} m** (máximo: {maximo_esperado} m).\n\n"
            f"👉 Sugestão: ajuste para ~{sugestao_tipica} m de parede, que é o típico para uma casa "
            f"de {area_piso_total:.0f} m² com quartos, banheiros, sala e cozinha.\n\n"
            f"_Se não ajustar, o orçamento ficará R$ {round((sugestao_tipica - metros_parede) * 2.8 * 40):,} "
            f"a R$ {round((sugestao_tipica - metros_parede) * 2.8 * 55):,} mais barato do que deveria "
            f"(impacto em blocos, tinta e mão de obra)._"
        )
    elif razao > maximo_razao:
        avisos.append(
            f"🧱 ATENÇÃO: Metros de parede SUPESTIMADOS\n\n"
            f"A IA leu **{metros_parede:.0f} m** de parede para **{area_piso_total:.0f} m²** de área. "
            f"O máximo esperado é **{maximo_esperado} m**. Confira se nenhuma parede foi contada duas vezes."
        )

    return avisos, sugestao


# =====================================================================
# SIDEBAR — Upload, Configurações e Monitor
# =====================================================================
with st.sidebar:
    st.title("🏗️ OrçaObra AI")
    st.caption(f"📍 {LOCAL_OBRA}")

    st.divider()

    # --- Monitor de API ---
    cota = status_cota()
    if cota["nivel"] == "critico":
        st.error(cota["mensagem"], icon="🔴")
    elif cota["nivel"] == "alerta":
        st.warning(cota["mensagem"], icon="🟡")
    else:
        st.success(cota["mensagem"], icon="🟢")

    st.divider()

    # --- Upload da Planta ---
    st.subheader("📂 Planta Baixa")
    st.caption(
        "PDF, JPG ou PNG. Plantas com **Quadro de Áreas** dão resultados mais precisos."
    )
    arquivo_pdf = st.file_uploader(
        "Selecione o arquivo",
        type=["pdf", "jpg", "jpeg", "png"],
        label_visibility="collapsed",
        key="upload_planta",
    )

    if arquivo_pdf is not None:
        st.success("Planta carregada!")
        extensao = os.path.splitext(arquivo_pdf.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=extensao) as tmp:
            tmp.write(arquivo_pdf.getbuffer())
            arquivo_temp = tmp.name

        if st.button("🔍 Analisar Planta", type="primary", use_container_width=True):
            with st.spinner("Analisando com IA..."):
                try:
                    dados_extraidos = extrair_dados_da_planta(arquivo_temp)
                    st.session_state["dados_extraidos"] = dados_extraidos
                    for chave_para_limpar in (
                        "input_area_seca", "input_area_molhada", "input_area_externa",
                        "input_metros_parede", "input_portas_internas",
                        "input_portas_externas", "input_janelas",
                        "materiais_editados", "mao_de_obra_editada",
                        "orcamento_assinatura",
                    ):
                        st.session_state.pop(chave_para_limpar, None)
                    st.rerun()
                except ErroExtracaoAmigavel as e:
                    st.error(f"⚠️ {e.mensagem_amigavel}")
                    if e.detalhe_tecnico:
                        with st.expander("Detalhes técnicos"):
                            st.code(e.detalhe_tecnico)
                    st.session_state.pop("dados_extraidos", None)
                except (ValueError, KeyError, RuntimeError) as e:
                    st.error("⚠️ Erro inesperado na análise.")
                    with st.expander("Detalhes"):
                        st.code(str(e))
                    st.session_state.pop("dados_extraidos", None)
                finally:
                    if os.path.exists(arquivo_temp):
                        os.remove(arquivo_temp)
    else:
        st.session_state.pop("dados_extraidos", None)

    st.divider()

    # --- Configurações da Obra ---
    st.subheader("🛠️ Obra")
    nome_projeto = st.text_input(
        "Projeto / Cliente",
        placeholder="Ex.: Residência Sr. João",
        key="input_nome_projeto",
    )
    padrao = st.selectbox(
        "Padrão de Acabamento",
        ["Econômico", "Médio", "Alto Padrão"],
        key="select_padrao",
    )
    estrutura = st.selectbox(
        "Tipo de Cobertura",
        ["Telhado", "Laje"],
        key="select_estrutura",
    )

    st.divider()

    # --- Perfil da Empresa ---
    with st.expander("⚙️ Sua Empresa", expanded=False):
        perfil = carregar_perfil()
        nome_empresa_input = st.text_input(
            "Nome", value=perfil["nome_empresa"], key="input_nome_empresa"
        )
        registro_input = st.text_input(
            "Registro", value=perfil["registro"], key="input_registro"
        )
        contato_input = st.text_input(
            "Contato", value=perfil["contato"], key="input_contato"
        )
        logo_upload = st.file_uploader(
            "Logo", type=["png", "jpg", "jpeg"], key="upload_logo"
        )
        if perfil["caminho_logo"] and os.path.exists(perfil["caminho_logo"]) and not logo_upload:
            st.image(perfil["caminho_logo"], width=80)
        if st.button("💾 Salvar", use_container_width=True, key="btn_salvar_perfil"):
            caminho_logo_final = perfil["caminho_logo"]
            if logo_upload is not None:
                extensao = os.path.splitext(logo_upload.name)[1]
                caminho_logo_final = os.path.join(PASTA_PERFIL, f"logo{extensao}")
                with open(caminho_logo_final, "wb") as f:
                    f.write(logo_upload.getbuffer())
            perfil = salvar_perfil(
                nome_empresa=nome_empresa_input,
                contato=contato_input,
                registro=registro_input,
                caminho_logo=caminho_logo_final,
            )
            st.success("Salvo!")
            st.rerun()

    st.divider()

    # --- Tabela de Preços ---
    with st.expander("💲 Preços Customizados", expanded=False):
        caminho_modelo = os.path.join(PASTA_PERFIL, "modelo_tabela_precos.xlsx")
        tabela_precos.gerar_modelo_excel(caminho_modelo)
        with open(caminho_modelo, "rb") as f:
            st.download_button(
                "📥 Modelo Excel",
                data=f.read(),
                file_name="tabela_precos_orcaobra.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="btn_download_modelo",
            )

        arquivo_precos = st.file_uploader(
            "📤 Enviar planilha", type=["xlsx"], label_visibility="collapsed",
            key="upload_tabela_precos",
        )
        if arquivo_precos is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(arquivo_precos.getbuffer())
                caminho_temp_precos = tmp.name
            try:
                atualizados, avisos = tabela_precos.importar_tabela_excel(caminho_temp_precos)
                for aviso in avisos:
                    st.warning(aviso, icon="⚠️")
                if atualizados:
                    st.info(f"{len(atualizados)} preço(s) alterado(s).")
                    if st.button("✅ Aplicar", use_container_width=True, key="btn_aplicar_precos"):
                        tabela_precos.salvar_overrides(atualizados)
                        st.success("Atualizado!")
                        st.rerun()
                elif not avisos:
                    st.info("Nenhuma mudança detectada.")
            finally:
                if os.path.exists(caminho_temp_precos):
                    os.remove(caminho_temp_precos)

        overrides_atuais = tabela_precos.carregar_overrides()
        if overrides_atuais:
            st.caption(f"📌 {len(overrides_atuais)} preço(s) customizado(s)")
            if st.button("↩️ Restaurar padrão", use_container_width=True, key="btn_restaurar_precos"):
                tabela_precos.restaurar_padroes()
                st.success("Restaurado!")
                st.rerun()


# =====================================================================
# MAIN AREA
# =====================================================================

# -----------------------------------------------------------------
# TELA INICIAL (sem dados extraídos)
# -----------------------------------------------------------------
if "dados_extraidos" not in st.session_state:
    st.markdown("""
    <div style="text-align: center; padding: 4rem 1rem;">
        <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">🏗️ OrçaObra AI</h1>
        <p style="font-size: 1.25rem; color: #666;">
            Transforme plantas baixas em orçamentos detalhados em segundos
        </p>
        <p style="margin-top: 2rem; color: #888;">
            👈 Use a barra lateral para fazer upload da planta e configurar a obra
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Histórico (sempre visível, mesmo sem dados)
    st.header("📁 Histórico de Orçamentos")
    orcamentos_salvos = listar_orcamentos()
    if not orcamentos_salvos:
        st.caption("Nenhum orçamento gerado ainda.")
    else:
        for registro in orcamentos_salvos:
            with st.expander(
                f"{registro['nome_projeto']} — {registro['data_criacao']} — "
                f"R$ {registro['preco_venda']:,.2f}"
            ):
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Área", f"{registro['area_piso']:.0f} m²")
                col_b.metric("Custo Direto", f"R$ {registro['custo_direto']:,.2f}")
                col_c.metric("Preço de Venda", f"R$ {registro['preco_venda']:,.2f}")
                st.caption(
                    f"Padrão: {registro['padrao']} · "
                    f"Cobertura: {registro['tipo_cobertura']} · BDI: {registro['bdi_percentual']:g}%"
                )

                col_x, col_y = st.columns(2)
                with col_x:
                    if registro["caminho_excel"] and os.path.exists(registro["caminho_excel"]):
                        with open(registro["caminho_excel"], "rb") as file:
                            st.download_button(
                                label="📊 Excel",
                                data=file,
                                file_name=os.path.basename(registro["caminho_excel"]),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"download_excel_{registro['id']}",
                                use_container_width=True,
                            )
                    else:
                        st.caption("⚠️ Excel não encontrado.")
                with col_y:
                    if registro.get("caminho_pdf") and os.path.exists(registro["caminho_pdf"]):
                        with open(registro["caminho_pdf"], "rb") as file:
                            st.download_button(
                                label="📄 PDF",
                                data=file,
                                file_name=os.path.basename(registro["caminho_pdf"]),
                                mime="application/pdf",
                                key=f"download_pdf_{registro['id']}",
                                use_container_width=True,
                            )
                    else:
                        st.caption("⚠️ PDF não disponível.")

                chave_confirmar = f"confirmar_exclusao_{registro['id']}"
                if st.session_state.get(chave_confirmar):
                    st.warning(
                        "Tem certeza que deseja excluir este orçamento? "
                        "Os arquivos em disco não são apagados."
                    )
                    col_conf1, col_conf2 = st.columns(2)
                    with col_conf1:
                        if st.button("✅ Sim, excluir", key=f"btn_confirma_excluir_{registro['id']}",
                                     use_container_width=True):
                            excluir_orcamento(registro["id"])
                            st.session_state.pop(chave_confirmar, None)
                            st.rerun()
                    with col_conf2:
                        if st.button("↩️ Cancelar", key=f"btn_cancela_excluir_{registro['id']}",
                                     use_container_width=True):
                            st.session_state.pop(chave_confirmar, None)
                            st.rerun()
                else:
                    if st.button("🗑️ Excluir", key=f"btn_excluir_{registro['id']}",
                                 use_container_width=True):
                        st.session_state[chave_confirmar] = True
                        st.rerun()

    st.stop()


# -----------------------------------------------------------------
# TELA DE EDIÇÃO E ORÇAMENTO (dados extraídos presentes)
# -----------------------------------------------------------------
dados = st.session_state["dados_extraidos"]
confianca = dados.get("confianca", {})

st.header("📊 Revisão dos Dados Extraídos")
st.caption("Confira os valores lidos pela IA antes de gerar o orçamento.")

# --- Cards de resumo ---
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
area_piso_seco = st.number_input(
    "Área Seca — m² (sala, quarto, cozinha)",
    value=float(dados.get("area_piso_seco") or 0), step=0.5, min_value=0.0,
    key="input_area_seca"
)
area_piso_molhado = st.number_input(
    "Área Molhada — m² (banheiro, área de serviço)",
    value=float(dados.get("area_piso_molhado") or 0), step=0.5, min_value=0.0,
    key="input_area_molhada"
)
area_piso_externo = st.number_input(
    "Área Externa — m² (varanda, garagem)",
    value=float(dados.get("area_piso_externo") or 0), step=0.5, min_value=0.0,
    key="input_area_externa"
)

# Recalcula total para o KPI
dados_extracao_preview = DadosExtracao(
    area_piso_seco=area_piso_seco,
    area_piso_molhado=area_piso_molhado,
    area_piso_externo=area_piso_externo,
    metros_parede=0, portas_internas=0, portas_externas=0, janelas=0,
)
area_piso_total_preview = dados_extracao_preview.area_piso_total

with col_kpi1:
    st.metric("Área Total", f"{area_piso_total_preview:.1f} m²")
with col_kpi2:
    st.metric("Padrão", padrao)
with col_kpi3:
    st.metric("Cobertura", estrutura)

st.divider()

# --- Paredes, portas e janelas ---
st.subheader("Paredes, Portas e Janelas")

metros_parede = st.number_input(
    "Paredes Lineares (m)",
    value=float(dados.get("metros_parede") or 0), step=0.5, min_value=0.0,
    key="input_metros_parede"
)
mostrar_badge("metros_parede", confianca)

col_p1, col_p2 = st.columns(2)
with col_p1:
    portas_internas = st.number_input(
        "Portas Internas (un)",
        value=int(dados.get("portas_internas") or 0), step=1, min_value=0,
        key="input_portas_internas"
    )
    mostrar_badge("portas_internas", confianca)
    janelas = st.number_input(
        "Janelas (un)",
        value=int(dados.get("janelas") or 0), step=1, min_value=0,
        key="input_janelas"
    )
    mostrar_badge("janelas", confianca)
with col_p2:
    portas_externas = st.number_input(
        "Portas Externas (un)",
        value=int(dados.get("portas_externas") or 0), step=1, min_value=0,
        key="input_portas_externas"
    )
    mostrar_badge("portas_externas", confianca)

# --- Avisos de confiança baixa ---
campos_baixa_confianca = [
    campo for campo in CAMPOS_EXTRACAO
    if confianca.get(campo, {}).get("nivel") == "baixa"
]
if campos_baixa_confianca:
    st.warning(
        "🔴 A IA teve baixa confiança em algum(ns) campo(s) acima. "
        "Recomendamos conferir esses valores direto na planta antes de prosseguir."
    )

# --- Monta modelo de domínio ---
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

# --- Validação de proporção parede ---
avisos_parede, sugestao_parede = validar_proporcao_parede(area_piso_total, metros_parede)
for aviso in avisos_parede:
    st.error(aviso)

if sugestao_parede and sugestao_parede != metros_parede:
    col_ajuste1, col_ajuste2 = st.columns([1, 3])
    with col_ajuste1:
        if st.button(f"⚡ Ajustar para {sugestao_parede} m", key="btn_ajuste_parede"):
            st.session_state["dados_extraidos"]["metros_parede"] = sugestao_parede
            st.session_state.pop("input_metros_parede", None)
            st.session_state.pop("orcamento_assinatura", None)
            st.rerun()
    with col_ajuste2:
        st.caption("Clique para aplicar a sugestão automaticamente (pode editar depois).")

# --- Validação geral ---
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

st.divider()

# --- Assinatura para recalcular ---
assinatura_atual = (
    padrao, estrutura, area_piso_seco, area_piso_molhado,
    area_piso_externo, metros_parede, portas_internas,
    portas_externas, janelas,
)
if st.session_state.get("orcamento_assinatura") != assinatura_atual:
    st.session_state.pop("materiais_editados", None)
    st.session_state.pop("mao_de_obra_editada", None)
    st.session_state["orcamento_assinatura"] = assinatura_atual

# =====================================================================
# MATERIAIS
# =====================================================================
st.header("📦 Materiais")
st.caption("Edite o preço unitário conforme seu fornecedor.")

materiais_sugeridos = calcular_materiais(dados_extracao, padrao, estrutura)

chave_mat = "materiais_editados"
if chave_mat not in st.session_state:
    st.session_state[chave_mat] = materiais_sugeridos

tabela_mat = st.data_editor(
    st.session_state[chave_mat],
    column_config={
        "Tipo": None,
        "Material": st.column_config.TextColumn("Material", disabled=True),
        "Quantidade": st.column_config.NumberColumn("Quantidade", disabled=True),
        "Preco_Unit": st.column_config.NumberColumn("Preço Unit. (R$)", min_value=0.0, step=0.5),
        "Total": st.column_config.NumberColumn("Total (R$)", disabled=True),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_materiais",
)

materiais_final = []
for item in tabela_mat:
    item = dict(item)
    item["Total"] = round(item["Quantidade"] * item["Preco_Unit"], 2)
    materiais_final.append(item)
st.session_state[chave_mat] = materiais_final

total_materiais = sum(item["Total"] for item in materiais_final)
st.metric("Total de Materiais", f"R$ {total_materiais:,.2f}")

st.divider()

# =====================================================================
# MÃO DE OBRA
# =====================================================================
st.header("👷 Mão de Obra")
st.caption("Valores sugeridos com base em composições SINAPI aproximadas.")

mao_de_obra_sugerida = calcular_mao_de_obra(dados_extracao, estrutura)

chave_mo = "mao_de_obra_editada"
if chave_mo not in st.session_state:
    st.session_state[chave_mo] = mao_de_obra_sugerida

tabela_mo = st.data_editor(
    st.session_state[chave_mo],
    column_config={
        "Tipo": None,
        "Material": st.column_config.TextColumn("Serviço", disabled=True),
        "Quantidade": st.column_config.NumberColumn("Quantidade", disabled=True),
        "Preco_Unit": st.column_config.NumberColumn("Preço Unit. (R$)", min_value=0.0, step=0.5),
        "Total": st.column_config.NumberColumn("Total (R$)", disabled=True),
    },
    hide_index=True,
    use_container_width=True,
    key="editor_mao_de_obra",
)

mao_de_obra_final = []
for item in tabela_mo:
    item = dict(item)
    item["Total"] = round(item["Quantidade"] * item["Preco_Unit"], 2)
    mao_de_obra_final.append(item)
st.session_state[chave_mo] = mao_de_obra_final

total_mao_de_obra = sum(item["Total"] for item in mao_de_obra_final)
st.metric("Total de Mão de Obra", f"R$ {total_mao_de_obra:,.2f}")

st.divider()

# =====================================================================
# BDI
# =====================================================================
st.header("💰 BDI (Benefícios e Despesas Indiretas)")
st.caption(
    "Percentual sobre o custo direto para administração, lucro, impostos e imprevistos."
)

bdi_percentual = st.number_input(
    "BDI (%)", min_value=0.0, max_value=100.0, value=25.0, step=1.0,
    key="input_bdi"
)

st.divider()

# =====================================================================
# GERAR ORÇAMENTO
# =====================================================================
if st.button("🚀 Gerar Orçamento Completo", type="primary", use_container_width=True):
    if not nome_projeto.strip():
        st.error("Informe o nome do projeto/cliente antes de gerar o orçamento.")
    else:
        with st.spinner("Calculando insumos e gerando documentos..."):
            orcamento_final = orcamento_service.montar_orcamento_completo(
                materiais_final, mao_de_obra_final
            )
            custo_direto, preco_venda = orcamento_service.calcular_custo_e_preco(
                orcamento_final, bdi_percentual
            )

            base_nome = orcamento_service.nome_arquivo_seguro(nome_projeto)
            excel_path = os.path.join(PASTA_ORCAMENTOS, f"{base_nome}.xlsx")
            pdf_path = os.path.join(PASTA_ORCAMENTOS, f"{base_nome}.pdf")

            caminho_excel = gerar_excel(orcamento_final, excel_path, bdi_percentual)

            perfil = carregar_perfil()  # recarrega para garantir dados atualizados
            caminho_pdf = gerar_pdf_proposta(
                orcamento_final, pdf_path,
                nome_projeto=nome_projeto,
                estado_uf=LOCAL_OBRA, padrao=padrao,
                tipo_cobertura=estrutura, area_piso=area_piso_total,
                bdi_percentual=bdi_percentual,
                nome_empresa=perfil["nome_empresa"] or "OrçaObra AI",
                contato=perfil["contato"],
                registro=perfil["registro"],
                caminho_logo=perfil["caminho_logo"],
            )

            salvar_orcamento(
                nome_projeto=nome_projeto,
                estado_uf=LOCAL_OBRA,
                padrao=padrao,
                tipo_cobertura=estrutura,
                area_piso=area_piso_total,
                custo_direto=round(custo_direto, 2),
                bdi_percentual=bdi_percentual,
                preco_venda=preco_venda,
                caminho_excel=caminho_excel,
                caminho_pdf=caminho_pdf,
            )

            st.balloons()

            st.header("📊 Resumo do Orçamento")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Área Total", f"{area_piso_total:.0f} m²")
            col_m2.metric("Paredes", f"{metros_parede:.0f} m")
            col_m3.metric("Portas + Janelas", f"{portas_internas + portas_externas + janelas} un")
            col_m4.metric("Preço de Venda", f"R$ {preco_venda:,.2f}")

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1, open(caminho_excel, "rb") as file:
                st.download_button(
                    label="📊 Baixar Excel (uso interno)",
                    data=file,
                    file_name=os.path.basename(caminho_excel),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="btn_download_excel"
                )
            with col_dl2, open(caminho_pdf, "rb") as file:
                st.download_button(
                    label="📄 Baixar PDF (proposta ao cliente)",
                    data=file,
                    file_name=os.path.basename(caminho_pdf),
                    mime="application/pdf",
                    use_container_width=True,
                    key="btn_download_pdf"
                )

st.divider()

# =====================================================================
# HISTÓRICO
# =====================================================================
st.header("📁 Histórico de Orçamentos")

orcamentos_salvos = listar_orcamentos()
if not orcamentos_salvos:
    st.caption("Nenhum orçamento gerado ainda. Seus orçamentos aparecerão aqui automaticamente.")
else:
    for registro in orcamentos_salvos:
        with st.expander(
            f"{registro['nome_projeto']} — {registro['data_criacao']} — "
            f"R$ {registro['preco_venda']:,.2f}"
        ):
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Área", f"{registro['area_piso']:.0f} m²")
            col_b.metric("Custo Direto", f"R$ {registro['custo_direto']:,.2f}")
            col_c.metric("Preço de Venda", f"R$ {registro['preco_venda']:,.2f}")
            st.caption(
                f"Padrão: {registro['padrao']} · "
                f"Cobertura: {registro['tipo_cobertura']} · BDI: {registro['bdi_percentual']:g}%"
            )

            col_x, col_y = st.columns(2)
            with col_x:
                if registro["caminho_excel"] and os.path.exists(registro["caminho_excel"]):
                    with open(registro["caminho_excel"], "rb") as file:
                        st.download_button(
                            label="📊 Baixar Excel",
                            data=file,
                            file_name=os.path.basename(registro["caminho_excel"]),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"download_excel_{registro['id']}",
                            use_container_width=True,
                        )
                else:
                    st.caption("⚠️ Excel não encontrado no disco.")
            with col_y:
                if registro.get("caminho_pdf") and os.path.exists(registro["caminho_pdf"]):
                    with open(registro["caminho_pdf"], "rb") as file:
                        st.download_button(
                            label="📄 Baixar PDF",
                            data=file,
                            file_name=os.path.basename(registro["caminho_pdf"]),
                            mime="application/pdf",
                            key=f"download_pdf_{registro['id']}",
                            use_container_width=True,
                        )
                else:
                    st.caption("⚠️ PDF não disponível (orçamento anterior a essa função).")

            st.write("")
            chave_confirmar = f"confirmar_exclusao_{registro['id']}"
            if st.session_state.get(chave_confirmar):
                st.warning(
                    "Tem certeza que deseja excluir este orçamento do histórico? "
                    "Os arquivos Excel/PDF salvos em disco não são apagados, só o registro na lista."
                )
                col_conf1, col_conf2 = st.columns(2)
                with col_conf1:
                    if st.button("✅ Sim, excluir", key=f"btn_confirma_excluir_{registro['id']}",
                                 use_container_width=True):
                        excluir_orcamento(registro["id"])
                        st.session_state.pop(chave_confirmar, None)
                        st.rerun()
                with col_conf2:
                    if st.button("↩️ Cancelar", key=f"btn_cancela_excluir_{registro['id']}",
                                 use_container_width=True):
                        st.session_state.pop(chave_confirmar, None)
                        st.rerun()
            else:
                if st.button("🗑️ Excluir do histórico", key=f"btn_excluir_{registro['id']}",
                             use_container_width=True):
                    st.session_state[chave_confirmar] = True
                    st.rerun()