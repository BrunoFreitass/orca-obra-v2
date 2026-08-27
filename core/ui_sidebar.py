"""Sidebar do OrçaObra AI: empresa, projeto, planta, preços e monitor."""

import os
import tempfile
from pathlib import Path

import streamlit as st

from config import LOCAL_OBRA
from core import paths, sinapi_import, tabela_precos
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
        # 4b. IMPORTAR SINAPI OFICIAL
        # -----------------------------------------------------------------
        with st.expander("📊 Importar SINAPI oficial", expanded=False):
            st.caption(
                "Baixe o ZIP do mês para RR no site da Caixa (Preços de Insumos "
                "e Composições → RR → versão Não Desonerado) e envie aqui o(s) "
                "arquivo(s) .xlsx extraído(s)."
            )
            arquivos_sinapi = st.file_uploader(
                "Relatório(s) do SINAPI (Insumos e/ou Composições)",
                type=["xlsx"], accept_multiple_files=True, label_visibility="collapsed",
                key="upload_sinapi",
            )
            mes_manual = st.text_input(
                "Mês de referência (AAAA-MM) — só se não for detectado automaticamente",
                placeholder="Ex.: 2026-08", key="input_mes_sinapi",
            )

            if arquivos_sinapi:
                with tempfile.TemporaryDirectory() as tmpdir:
                    caminhos_temp = []
                    for arquivo in arquivos_sinapi:
                        caminho = Path(tmpdir) / arquivo.name
                        caminho.write_bytes(arquivo.getbuffer())
                        caminhos_temp.append(caminho)

                    precos, avisos, mes_ref = sinapi_import.importar(
                        caminhos_temp, mes_referencia=mes_manual or None,
                    )

                avisos_sem_codigo = [a for a in avisos if "ainda sem código mapeado" in a]
                avisos_mes = [a for a in avisos if "mês de referência" in a]
                avisos_relevantes = [
                    a for a in avisos if a not in avisos_sem_codigo and a not in avisos_mes
                ]

                for aviso in avisos_relevantes:
                    st.warning(aviso, icon="⚠️")
                if avisos_sem_codigo:
                    st.caption(
                        f"ℹ️ {len(avisos_sem_codigo)} item(ns) do motor de cálculo ainda sem "
                        f"código SINAPI mapeado em `sinapi_codigos.py` — fora do escopo desta "
                        f"importação, continuam no valor padrão/override atual."
                    )

                if precos and mes_ref:
                    precos_padrao = {
                        chave: preco for chave, _, _, preco in tabela_precos._itens_editaveis()
                    }
                    st.info(f"{len(precos)} preço(s) prontos para atualizar (ref. {mes_ref}):")
                    for chave, dado in precos.items():
                        atual = tabela_precos.obter_preco(chave, precos_padrao[chave]).valor
                        st.caption(f"**{chave}**: R$ {atual:.2f} → R$ {dado['valor']:.2f}")
                    if st.button(
                        "✅ Aplicar preços do SINAPI", use_container_width=True,
                        key="btn_aplicar_sinapi",
                    ):
                        valores = {chave: dado["valor"] for chave, dado in precos.items()}
                        tabela_precos.salvar_overrides(
                            valores,
                            fonte=f"SINAPI oficial (CAIXA/IBGE) - ref. {mes_ref}",
                            data_ref=mes_ref,
                        )
                        st.success("Preços do SINAPI aplicados!")
                        st.rerun()
                elif precos and not mes_ref:
                    st.warning(
                        "Não consegui identificar o mês de referência pelo nome do "
                        "arquivo — preencha o campo acima para gravar os preços.",
                        icon="⚠️",
                    )
                elif not avisos:
                    st.info("Nenhum item pronto para atualizar.")

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
