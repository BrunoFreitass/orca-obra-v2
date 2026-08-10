"""Componente de histórico de orçamentos — reutilizado na tela inicial
(e depois do orçamento gerado)."""

import os

import streamlit as st

from core.historico import excluir_orcamento, listar_orcamentos


def renderizar_historico():
    """Renderiza a seção de histórico completa."""
    st.header("📁 Histórico de Orçamentos")

    orcamentos_salvos = listar_orcamentos()
    if not orcamentos_salvos:
        st.caption("Nenhum orçamento gerado ainda. Seus orçamentos aparecerão aqui automaticamente.")
        return

    for registro in orcamentos_salvos:
        # Título do expander com versão dos coeficientes (se houver)
        versao = registro.get("versao_coeficientes", "")
        sufixo_versao = f" · 📋 v{versao}" if versao else ""

        with st.expander(
            f"{registro['nome_projeto']} — {registro['data_criacao']} — "
            f"R$ {registro['preco_venda']:,.2f}{sufixo_versao}"
        ):
            # Métricas principais
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Área", f"{registro['area_piso']:.0f} m²")
            col_b.metric("Custo Direto", f"R$ {registro['custo_direto']:,.2f}")
            col_c.metric("Preço de Venda", f"R$ {registro['preco_venda']:,.2f}")

            # Detalhes de quantitativos (novos campos)
            st.caption(
                f"Padrão: {registro['padrao']} · "
                f"Cobertura: {registro['tipo_cobertura']} · BDI: {registro['bdi_percentual']:g}%"
            )

            # Se tiver os novos campos, mostra em grid
            tem_detalhes = any(
                registro.get(k, 0) not in (0, 0.0, None, "")
                for k in ["area_piso_seco", "area_piso_molhado", "area_piso_externo",
                          "metros_parede", "portas_internas", "portas_externas", "janelas"]
            )
            if tem_detalhes:
                with st.container(border=True):
                    st.markdown("**📐 Quantitativos da Planta**")
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("Área Seca", f"{registro.get('area_piso_seco', 0):.1f} m²")
                        st.metric("Área Molhada", f"{registro.get('area_piso_molhado', 0):.1f} m²")
                    with c2:
                        st.metric("Área Externa", f"{registro.get('area_piso_externo', 0):.1f} m²")
                        st.metric("Paredes", f"{registro.get('metros_parede', 0):.0f} m")
                    with c3:
                        st.metric("Portas Int.", f"{registro.get('portas_internas', 0)} un")
                        st.metric("Portas Ext.", f"{registro.get('portas_externas', 0)} un")
                    with c4:
                        st.metric("Janelas", f"{registro.get('janelas', 0)} un")

            # Botões de download
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
