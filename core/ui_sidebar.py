"""Sidebar do OrçaObra AI: empresa, projeto, planta, preços e monitor."""

import os
import tempfile

import streamlit as st

from config import LOCAL_OBRA
from core import paths, tabela_precos
from core.monitor_api import status_cota
from core.perfil_empresa import carregar_perfil, salvar_perfil
from core.ui_config import toggle_tema
from core.vision import ErroExtracaoAmigavel, extrair_dados_da_planta


def _limpar_estado_extracao():
    """Limpa os campos de input e confirmação após nova extração."""
    for chave in (
        "input_area_seca", "input_area_molhada", "input_area_externa",
        "input_metros_parede", "parede_key_versao", "input_portas_internas",
        "input_portas_externas", "input_janelas",
        "materiais_editados", "mao_de_obra_editada",
        "orcamento_assinatura", "dados_revisao_confirmados",
    ):
        st.session_state.pop(chave, None)


def renderizar_sidebar():
    """Renderiza toda a sidebar e retorna os dados de configuração atuais."""
    with st.sidebar:
        st.title("🏗️ OrçaObra AI")
        st.caption(f"📍 {LOCAL_OBRA}")

        toggle_tema()
        st.divider()

        # -----------------------------------------------------------------
        # 1. EMPRESA
        # -----------------------------------------------------------------
        perfil = carregar_perfil()
        empresa_confirmada = st.session_state.get("empresa_confirmada", False)
        wrapper_empresa = st.expander if empresa_confirmada else (
            lambda titulo, **kw: st.container(border=True)
        )
        if not empresa_confirmada:
            st.subheader("🏢 Sua Empresa")

        with wrapper_empresa("🏢 Sua Empresa", expanded=False):
            nome_empresa_input = st.text_input(
                "Nome da Empresa",
                value=perfil["nome_empresa"],
                key="input_nome_empresa",
                placeholder="Ex.: Construtora Silva",
            )
            profissional_input = st.text_input(
                "Profissional Responsável",
                value=perfil["profissional_responsavel"],
                key="input_profissional",
                placeholder="Ex.: Eng. João Silva",
            )
            registro_input = st.text_input(
                "Registro (CREA/CAU/CNPJ)",
                value=perfil["registro"],
                key="input_registro",
                placeholder="Ex.: CREA-RR 12345",
            )
            col_tel, col_email = st.columns(2)
            with col_tel:
                telefone_input = st.text_input(
                    "Telefone",
                    value=perfil["telefone"],
                    key="input_telefone",
                    placeholder="(95) 99999-9999",
                )
            with col_email:
                email_input = st.text_input(
                    "E-mail",
                    value=perfil["email"],
                    key="input_email",
                    placeholder="contato@empresa.com",
                )
            logo_upload = st.file_uploader(
                "Logo (PNG/JPG)", type=["png", "jpg", "jpeg"], key="upload_logo"
            )
            if perfil["caminho_logo"] and os.path.exists(perfil["caminho_logo"]) and not logo_upload:
                st.image(perfil["caminho_logo"], width=80)

            if st.button("💾 Salvar dados da empresa", use_container_width=True, key="btn_salvar_perfil"):
                caminho_logo_final = perfil["caminho_logo"]
                if logo_upload is not None:
                    extensao = os.path.splitext(logo_upload.name)[1]
                    caminho_logo_final = os.path.join(paths.PASTA_PERFIL, f"logo{extensao}")
                    with open(caminho_logo_final, "wb") as f:
                        f.write(logo_upload.getbuffer())
                salvar_perfil(
                    nome_empresa=nome_empresa_input,
                    profissional_responsavel=profissional_input,
                    telefone=telefone_input,
                    email=email_input,
                    registro=registro_input,
                    caminho_logo=caminho_logo_final,
                )
                st.session_state["empresa_confirmada"] = True
                st.success("Dados da empresa salvos!")
                st.rerun()

        st.divider()

        # -----------------------------------------------------------------
        # 2. PROJETO
        # -----------------------------------------------------------------
        projeto_confirmado = st.session_state.get("projeto_confirmado", False)
        wrapper_projeto = st.expander if projeto_confirmado else (
            lambda titulo, **kw: st.container(border=True)
        )
        if not projeto_confirmado:
            st.subheader("🛠️ Projeto")

        with wrapper_projeto("🛠️ Projeto", expanded=False):
            nome_projeto = st.text_input(
                "Nome do projeto",
                placeholder="Ex.: Residência Sr. João",
                key="input_nome_projeto",
            )
            cliente = st.text_input(
                "Cliente",
                placeholder="Ex.: João da Silva",
                key="input_cliente",
            )
            padrao = st.selectbox(
                "Padrão de acabamento",
                ["Econômico", "Médio", "Alto Padrão"],
                key="select_padrao",
            )
            estrutura = st.selectbox(
                "Tipo de cobertura",
                ["Telhado", "Laje"],
                key="select_estrutura",
            )

            if st.button("💾 Salvar dados do projeto", use_container_width=True, key="btn_salvar_projeto"):
                st.session_state["projeto_confirmado"] = True
                st.rerun()

        st.divider()

        # -----------------------------------------------------------------
        # 3. PLANTA BAIXA
        # -----------------------------------------------------------------
        st.subheader("📂 Planta Baixa")
        st.caption("PDF, JPG ou PNG. Plantas com **Quadro de Áreas** dão resultados mais precisos.")
        arquivo_pdf = st.file_uploader(
            "Selecione o arquivo da planta",
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

            if st.button("🔍 Analisar Planta com IA", type="primary", use_container_width=True):
                with st.spinner("Analisando com IA..."):
                    try:
                        dados_extraidos = extrair_dados_da_planta(arquivo_temp)
                        st.session_state["dados_extraidos"] = dados_extraidos
                        _limpar_estado_extracao()
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

        # -----------------------------------------------------------------
        # 4. PREÇOS CUSTOMIZADOS
        # -----------------------------------------------------------------
        with st.expander("💲 Preços Customizados", expanded=False):
            caminho_modelo = os.path.join(paths.PASTA_PERFIL, "modelo_tabela_precos.xlsx")
            tabela_precos.gerar_modelo_excel(caminho_modelo)
            with open(caminho_modelo, "rb") as f:
                st.download_button(
                    "📥 Baixar modelo Excel",
                    data=f.read(),
                    file_name="tabela_precos_orcaobra.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="btn_download_modelo",
                )

            arquivo_precos = st.file_uploader(
                "📤 Enviar planilha atualizada", type=["xlsx"], label_visibility="collapsed",
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
                        if st.button("✅ Aplicar preços", use_container_width=True, key="btn_aplicar_precos"):
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

        st.divider()

        # -----------------------------------------------------------------
        # 5. MONITOR DE API
        # -----------------------------------------------------------------
        cota = status_cota()
        if cota["nivel"] == "critico":
            st.error(cota["mensagem"], icon="🔴")
        elif cota["nivel"] == "alerta":
            st.warning(cota["mensagem"], icon="🟡")
        else:
            st.success(cota["mensagem"], icon="🟢")

    return {
        "nome_projeto": nome_projeto,
        "cliente": cliente,
        "padrao": padrao,
        "estrutura": estrutura,
    }
