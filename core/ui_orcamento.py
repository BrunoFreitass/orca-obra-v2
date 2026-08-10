"""Tela de orçamento: materiais, mão de obra, BDI e geração de documentos."""

import os

import streamlit as st

from config import LOCAL_OBRA
from core import orcamento_service, paths
from core.calculator import calcular_mao_de_obra, calcular_materiais
from core.historico import salvar_orcamento
from core.perfil_empresa import carregar_perfil
from core.proposta_pdf import gerar_pdf_proposta
from core.reporter import gerar_excel


def _editor_materiais(dados_extracao, padrao, estrutura):
    """Renderiza o editor de materiais e retorna a lista final."""
    st.header("📦 Materiais")
    st.caption("Edite o preço unitário conforme seu fornecedor. Os totais recalculam automaticamente.")

    materiais_sugeridos = calcular_materiais(dados_extracao, padrao, estrutura)
    chave = "materiais_editados"
    if chave not in st.session_state:
        st.session_state[chave] = materiais_sugeridos

    tabela = st.data_editor(
        st.session_state[chave],
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

    final = []
    for item in tabela:
        item = dict(item)
        item["Total"] = round(item["Quantidade"] * item["Preco_Unit"], 2)
        final.append(item)
    st.session_state[chave] = final

    total = sum(item["Total"] for item in final)
    st.metric("Total de Materiais", f"R$ {total:,.2f}")
    return final


def _editor_mao_de_obra(dados_extracao, estrutura):
    """Renderiza o editor de mão de obra e retorna a lista final."""
    st.divider()
    st.header("👷 Mão de Obra")
    st.caption("Valores sugeridos com base em composições SINAPI aproximadas. Ajuste conforme sua realidade regional.")

    mao_de_obra_sugerida = calcular_mao_de_obra(dados_extracao, estrutura)
    chave = "mao_de_obra_editada"
    if chave not in st.session_state:
        st.session_state[chave] = mao_de_obra_sugerida

    tabela = st.data_editor(
        st.session_state[chave],
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

    final = []
    for item in tabela:
        item = dict(item)
        item["Total"] = round(item["Quantidade"] * item["Preco_Unit"], 2)
        final.append(item)
    st.session_state[chave] = final

    total = sum(item["Total"] for item in final)
    st.metric("Total de Mão de Obra", f"R$ {total:,.2f}")
    return final


def _bdi_input():
    """Renderiza o input de BDI e retorna o percentual."""
    st.divider()
    st.header("💰 BDI (Benefícios e Despesas Indiretas)")
    st.caption("Percentual sobre o custo direto para administração, lucro, impostos e imprevistos.")
    return st.number_input("BDI (%)", min_value=0.0, max_value=100.0, value=25.0, step=1.0, key="input_bdi")


def _gerar_documentos(orcamento_final, bdi_percentual, nome_projeto, padrao, estrutura,
                       area_piso_total, metros_parede, portas_internas, portas_externas, janelas,
                       area_piso_seco, area_piso_molhado, area_piso_externo):
    """Gera Excel, PDF, salva no histórico e renderiza os botões de download."""
    st.divider()
    if not st.button("🚀 Gerar Orçamento Completo", type="primary", use_container_width=True):
        return

    if not nome_projeto.strip():
        st.error("Informe o nome do projeto/cliente antes de gerar o orçamento.")
        return

    with st.spinner("Calculando insumos e gerando documentos..."):
        custo_direto, preco_venda = orcamento_service.calcular_custo_e_preco(
            orcamento_final, bdi_percentual
        )

        base_nome = orcamento_service.nome_arquivo_seguro(nome_projeto)
        excel_path = os.path.join(paths.PASTA_ORCAMENTOS, f"{base_nome}.xlsx")
        pdf_path = os.path.join(paths.PASTA_ORCAMENTOS, f"{base_nome}.pdf")

        caminho_excel = gerar_excel(orcamento_final, excel_path, bdi_percentual)

        perfil = carregar_perfil()

        # Contato com rótulos descritivos para o PDF
        contato_linhas = []
        if perfil.get("profissional_responsavel"):
            contato_linhas.append(f"Profissional Responsável: {perfil['profissional_responsavel']}")
        if perfil.get("telefone"):
            contato_linhas.append(f"Contato: {perfil['telefone']}")
        if perfil.get("email"):
            contato_linhas.append(f"E-mail: {perfil['email']}")

        registro_str = ""
        if perfil.get("registro"):
            registro_str = f"Registro (CREA/CAU/CNPJ): {perfil['registro']}"

        caminho_pdf = gerar_pdf_proposta(
            orcamento_final, pdf_path,
            nome_projeto=nome_projeto,
            estado_uf=LOCAL_OBRA, padrao=padrao,
            tipo_cobertura=estrutura, area_piso=area_piso_total,
            bdi_percentual=bdi_percentual,
            nome_empresa=perfil["nome_empresa"] or "OrçaObra AI",
            contato=contato_linhas,
            registro=registro_str,
            caminho_logo=perfil["caminho_logo"],
        )

        salvar_orcamento(
            nome_projeto=nome_projeto,
            estado_uf=LOCAL_OBRA,
            padrao=padrao,
            tipo_cobertura=estrutura,
            area_piso=area_piso_total,
            area_piso_seco=area_piso_seco,
            area_piso_molhado=area_piso_molhado,
            area_piso_externo=area_piso_externo,
            metros_parede=metros_parede,
            portas_internas=portas_internas,
            portas_externas=portas_externas,
            janelas=janelas,
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


def renderizar_orcamento(dados_extracao, config: dict):
    """Orquestra a tela completa de orçamento."""
    materiais = _editor_materiais(dados_extracao, config["padrao"], config["estrutura"])
    mao_de_obra = _editor_mao_de_obra(dados_extracao, config["estrutura"])
    bdi = _bdi_input()

    orcamento_final = orcamento_service.montar_orcamento_completo(materiais, mao_de_obra)
    _gerar_documentos(
        orcamento_final, bdi,
        nome_projeto=config["nome_projeto"],
        padrao=config["padrao"],
        estrutura=config["estrutura"],
        area_piso_total=dados_extracao.area_piso_total,
        metros_parede=dados_extracao.metros_parede,
        portas_internas=dados_extracao.portas_internas,
        portas_externas=dados_extracao.portas_externas,
        janelas=dados_extracao.janelas,
        area_piso_seco=dados_extracao.area_piso_seco,
        area_piso_molhado=dados_extracao.area_piso_molhado,
        area_piso_externo=dados_extracao.area_piso_externo,
    )
