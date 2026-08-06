"""Configuração de tema (claro/escuro) e CSS dinâmico."""

import streamlit as st


def tema_atual() -> str:
    """Retorna 'escuro' ou 'claro' baseado no session_state."""
    return "escuro" if st.session_state.get("tema_escuro", False) else "claro"


CORES = {
    "claro": {
        "bg": "#FFFFFF",
        "bg_sec": "#F8F9FA",
        "text": "#2C3E50",
        "text_sec": "#666666",
        "primary": "#1F4E78",
        "primary_hover": "#163A5A",
        "accent": "#4472A8",
        "border": "#E9ECEF",
        "card": "#FFFFFF",
        "success": "#2E7D32",
        "warning": "#F9A825",
        "error": "#C62828",
        "metric_bg": "#F8F9FA",
        "input_bg": "#FFFFFF",
        "input_border": "#D1D5DB",
    },
    "escuro": {
        "bg": "#0E1117",
        "bg_sec": "#1A1D24",
        "text": "#E0E0E0",
        "text_sec": "#A0A0A0",
        "primary": "#4A9EFF",
        "primary_hover": "#3A8EEF",
        "accent": "#6BB3FF",
        "border": "#2A2D35",
        "card": "#161A21",
        "success": "#4CAF50",
        "warning": "#FFC107",
        "error": "#EF5350",
        "metric_bg": "#1A1D24",
        "input_bg": "#1E2128",
        "input_border": "#3A3D45",
    },
}


def css_dinamico() -> str:
    """Gera a tag <style> completa baseada no tema ativo."""
    c = CORES[tema_atual()]
    return f"""
    <style>
        .stApp {{ background-color: {c["bg"]}; color: {c["text"]}; }}
        h1, h2, h3, h4, h5, h6 {{ color: {c["primary"]} !important; font-weight: 600; }}
        p, li, span, label, .stMarkdown {{ color: {c["text"]}; }}

        section[data-testid="stSidebar"] > div {{ background-color: {c["bg_sec"]}; padding-top: 1rem; }}
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{ color: {c["primary"]} !important; }}
        section[data-testid="stSidebar"] .stMarkdown p {{ color: {c["text_sec"]}; }}

        div[data-testid="stMetric"] {{
            background: {c["metric_bg"]};
            border-radius: 12px;
            padding: 16px;
            border: 1px solid {c["border"]};
        }}
        div[data-testid="stMetric"] > div:first-child {{ font-weight: 600 !important; color: {c["primary"]} !important; }}
        div[data-testid="stMetric"] > div:nth-child(2) {{ color: {c["text"]}; }}

        .stButton>button[kind="primary"] {{
            background-color: {c["primary"]};
            color: white;
            border-radius: 8px;
            height: 3em;
            font-weight: 600;
            width: 100%;
            border: none;
            transition: background-color 0.2s ease;
        }}
        .stButton>button[kind="primary"]:hover {{ background-color: {c["primary_hover"]}; }}
        .stButton>button {{ border-radius: 8px; color: {c["text"]}; border: 1px solid {c["border"]}; }}

        .stTextInput input,
        .stNumberInput input,
        .stSelectbox > div > div,
        .stFileUploader > div > div {{
            background-color: {c["input_bg"]} !important;
            color: {c["text"]} !important;
            border: 1px solid {c["input_border"]} !important;
            border-radius: 6px;
        }}
        .stTextInput label,
        .stNumberInput label,
        .stSelectbox label,
        .stFileUploader label {{ color: {c["text_sec"]} !important; }}

        div[data-testid="stContainer"] {{
            background-color: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: 10px;
            padding: 1rem;
        }}

        details {{
            background-color: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: 8px;
        }}
        summary {{ color: {c["text"]}; font-weight: 500; }}

        .stAlert {{ border-radius: 8px !important; }}

        .stDataFrame {{
            background-color: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: 8px;
        }}
        .stDataFrame th {{ background-color: {c["bg_sec"]} !important; color: {c["primary"]} !important; }}
        .stDataFrame td {{ color: {c["text"]} !important; }}

        .stCaption {{ color: {c["text_sec"]} !important; }}
        hr {{ border-color: {c["border"]}; }}

        .stDownloadButton>button {{
            background-color: {c["bg_sec"]};
            color: {c["text"]};
            border: 1px solid {c["border"]};
            border-radius: 8px;
        }}
        .stDownloadButton>button:hover {{
            background-color: {c["border"]};
            border-color: {c["primary"]};
        }}

        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: {c["bg"]}; }}
        ::-webkit-scrollbar-thumb {{ background: {c["border"]}; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: {c["input_border"]}; }}
    </style>
    """


def injetar_css():
    """Aplica o CSS dinâmico na página."""
    st.markdown(css_dinamico(), unsafe_allow_html=True)


def toggle_tema():
    """Renderiza o toggle de tema na sidebar e gerencia o estado."""
    tema = st.toggle("🌙 Tema Escuro", value=st.session_state.get("tema_escuro", False), key="toggle_tema")
    if tema != st.session_state.get("tema_escuro", False):
        st.session_state["tema_escuro"] = tema
        st.rerun()
