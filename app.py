"""OrçaObra AI — Orquestrador principal.

A interface foi modularizada em core/ui_*.py para facilitar manutenção:
  - ui_config.py    → tema claro/escuro + CSS dinâmico
  - ui_sidebar.py   → sidebar (empresa, projeto, planta, preços, monitor)
  - ui_revisao.py   → revisão dos dados extraídos da planta
  - ui_orcamento.py → materiais, mão de obra, BDI, geração de docs
  - ui_historico.py → componente reutilizável de histórico
"""

import streamlit as st

from config import LOCAL_OBRA
from core import paths
from core.historico import inicializar_db
from core.monitor_api import inicializar_tabela_monitor
from core.ui_config import injetar_css
from core.ui_historico import renderizar_historico
from core.ui_orcamento import renderizar_orcamento
from core.ui_revisao import renderizar_revisao
from core.ui_sidebar import renderizar_sidebar

# =====================================================================
# INICIALIZAÇÃO
# =====================================================================
st.set_page_config(
    page_title="OrçaObra AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inicializar_db()
inicializar_tabela_monitor()
paths.garantir_diretorios()
injetar_css()

# =====================================================================
# SIDEBAR — retorna configurações selecionadas
# =====================================================================
config = renderizar_sidebar()

# =====================================================================
# MAIN AREA
# =====================================================================

# -----------------------------------------------------------------
# TELA INICIAL (sem dados extraídos)
# -----------------------------------------------------------------
if "dados_extraidos" not in st.session_state:
    c = "#1F4E78" if not st.session_state.get("tema_escuro") else "#4A9EFF"
    t = "#666666" if not st.session_state.get("tema_escuro") else "#A0A0A0"
    st.markdown(f"""
    <div style="text-align: center; padding: 4rem 1rem;">
        <h1 style="font-size: 3rem; margin-bottom: 0.5rem; color: {c};">🏗️ OrçaObra AI</h1>
        <p style="font-size: 1.25rem; color: {t};">
            Transforme plantas baixas em orçamentos detalhados em segundos
        </p>
        <p style="margin-top: 2rem; color: {t};">
            👈 Configure sua empresa, o projeto e envie a planta na barra lateral
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    renderizar_historico()
    st.stop()


# -----------------------------------------------------------------
# TELA DE EDIÇÃO E ORÇAMENTO (dados extraídos presentes)
# -----------------------------------------------------------------
dados = st.session_state["dados_extraidos"]

# Revisão dos dados → retorna modelo de domínio validado
dados_extracao = renderizar_revisao(
    dados_extraidos=dados,
    padrao=config["padrao"],
    estrutura=config["estrutura"],
    local_obra=LOCAL_OBRA,
)

# Orçamento completo (materiais + mão de obra + BDI + geração)
renderizar_orcamento(dados_extracao, config)

st.divider()
renderizar_historico()
