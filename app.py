import streamlit as st
import os
from core.vision import extrair_dados_da_planta, ErroExtracaoAmigavel
from core.calculator import calcular_mao_de_obra, calcular_materiais
from core.models import DadosExtracao
from core import orcamento_service
from core.reporter import gerar_excel
from core.proposta_pdf import gerar_pdf_proposta
from core.validacao import validar_dados
from core.historico import inicializar_db, salvar_orcamento, listar_orcamentos
from core.perfil_empresa import carregar_perfil, salvar_perfil
from core import tabela_precos

st.set_page_config(page_title="OrçaObra AI", page_icon="🏗️", layout="centered")

inicializar_db()

PASTA_ORCAMENTOS = "orcamentos_salvos"
os.makedirs(PASTA_ORCAMENTOS, exist_ok=True)

PASTA_PERFIL = "perfil_empresa"
os.makedirs(PASTA_PERFIL, exist_ok=True)

# Mapa de nivel de confianca -> (emoji, texto de ajuda). Usado no
# indicador ao lado de cada campo extraido da planta.
CONFIANCA_VISUAL = {
    "alta": {"emoji": "🟢", "label": "Confiança alta"},
    "media": {"emoji": "🟡", "label": "Confiança média"},
    "baixa": {"emoji": "🔴", "label": "Confiança baixa — revise"},
}

# Os 7 campos agregados que a extracao por ambiente retorna (ver
# core/vision.py). Usado tanto pro aviso de confianca baixa quanto
# como fonte unica da lista de campos, pra nao duplicar em varios lugares.
CAMPOS_EXTRACAO = (
    "area_piso_seco", "area_piso_molhado", "area_piso_externo",
    "metros_parede", "portas_internas", "portas_externas", "janelas",
)


def badge_confianca(campo, confianca):
    """Retorna o texto do badge (emoji + label) e o motivo, pro campo
    informado. Se o campo nao existir no bloco de confianca (defesa
    contra resposta antiga sem esse campo), assume media."""
    info = (confianca or {}).get(campo, {"nivel": "media", "motivo": ""})
    nivel = info.get("nivel", "media")
    visual = CONFIANCA_VISUAL.get(nivel, CONFIANCA_VISUAL["media"])
    return visual, info.get("motivo", "")


def mostrar_badge(campo, confianca):
    visual, motivo = badge_confianca(campo, confianca)
    st.caption(f"{visual['emoji']} {visual['label']}" + (f" — {motivo}" if motivo else ""))


st.title("🏗️ OrçaObra AI")
st.subheader("Transforme plantas baixas em orçamentos em segundos")

# --- Perfil da empresa/profissional (nome, contato, registro, logo) ---
# Usado pra personalizar o PDF de proposta em vez de sair sempre com a
# marca "OrçaObra AI". Fica num expander recolhido, ja que normalmente
# o usuario preenche uma vez e nao mexe mais.
perfil = carregar_perfil()

with st.expander("⚙️ Configurações da Proposta (nome, logo, contato)", expanded=not perfil["nome_empresa"]):
    st.caption("Esses dados aparecem no cabeçalho do PDF enviado ao cliente. Preencha uma vez — fica salvo.")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        nome_empresa_input = st.text_input(
            "Nome da Empresa / Profissional",
            value=perfil["nome_empresa"], placeholder="Ex.: João Silva Engenharia"
        )
        registro_input = st.text_input(
            "Registro (CREA/CAU)", value=perfil["registro"], placeholder="Ex.: CREA-CE 123456"
        )
    with col_p2:
        contato_input = st.text_input(
            "Contato", value=perfil["contato"], placeholder="Ex.: (85) 99999-9999"
        )
        logo_upload = st.file_uploader("Logo (opcional)", type=["png", "jpg", "jpeg"])

    if perfil["caminho_logo"] and os.path.exists(perfil["caminho_logo"]) and not logo_upload:
        st.image(perfil["caminho_logo"], width=100, caption="Logo atual")

    if st.button("💾 Salvar Configurações"):
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
        st.success("Configurações salvas!")
        st.rerun()

st.write("---")

with st.expander("💲 Personalizar Tabela de Preços (avançado)"):
    st.caption(
        "Os preços de material e mão de obra usados no cálculo vêm de uma tabela interna "
        "(SINAPI/IBGE e pesquisa de mercado), que fica desatualizada com o tempo. "
        "Baixe o modelo, edite os preços que quiser na coluna **Preço (R$)** e envie de volta "
        "— o app passa a usar seus valores em todos os orçamentos seguintes."
    )

    caminho_modelo = os.path.join(PASTA_PERFIL, "modelo_tabela_precos.xlsx")
    tabela_precos.gerar_modelo_excel(caminho_modelo)
    with open(caminho_modelo, "rb") as f:
        st.download_button(
            "📥 Baixar modelo com os preços atuais",
            data=f.read(),
            file_name="tabela_precos_orcaobra.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    arquivo_precos = st.file_uploader(
        "📤 Enviar planilha de preços atualizada", type=["xlsx"], key="upload_tabela_precos"
    )
    if arquivo_precos is not None:
        caminho_temp_precos = os.path.join(PASTA_PERFIL, "temp_tabela_precos.xlsx")
        with open(caminho_temp_precos, "wb") as f:
            f.write(arquivo_precos.getbuffer())

        atualizados, avisos = tabela_precos.importar_tabela_excel(caminho_temp_precos)

        for aviso in avisos:
            st.warning(aviso)

        if atualizados:
            st.info(f"{len(atualizados)} preço(s) serão atualizados.")
            if st.button("✅ Aplicar estes novos preços"):
                tabela_precos.salvar_overrides(atualizados)
                st.success("Tabela de preços atualizada! Ela já vale para os próximos orçamentos.")
                st.rerun()
        elif not avisos:
            st.info("Nenhum preço foi alterado em relação ao que já está em uso.")

    overrides_atuais = tabela_precos.carregar_overrides()
    if overrides_atuais:
        st.caption(f"📌 {len(overrides_atuais)} preço(s) customizado(s) em uso atualmente.")
        if st.button("↩️ Restaurar preços padrão (desfazer todas as customizações)"):
            tabela_precos.restaurar_padroes()
            st.success("Preços padrão restaurados.")
            st.rerun()

st.write("---")
st.write("### 🛠️ Configurações da Obra")
st.caption("📍 Atendimento disponível para Boa Vista/RR neste momento.")

nome_projeto = st.text_input(
    "Nome do Projeto / Cliente",
    placeholder="Ex.: Residência Sr. João - Rua das Flores, 123"
)

# Estado fixo -- o OrçaObra atende apenas Boa Vista/RR neste momento
# (ver core/coeficientes.py: FATOR_REGIONAL_RR e PRECO_ACO_RR).
LOCAL_OBRA = "Boa Vista/RR"

col_pad, col_est = st.columns(2)
with col_pad:
    padrao = st.selectbox("Padrão de Acabamento", ["Econômico", "Médio", "Alto Padrão"])
with col_est:
    estrutura = st.selectbox("Tipo de Cobertura", ["Telhado", "Laje"])

st.write("---")

# Campo de Upload na página principal
st.write("### 📂 Upload do Projeto")
st.caption(
    "💡 Dica: plantas com um **Quadro de Áreas** (tabela com a área em m² de cada cômodo) "
    "dão resultados mais precisos que plantas só com cotas lineares nas bordas."
)
arquivo_pdf = st.file_uploader("Arraste ou selecione o PDF da planta baixa", type=["pdf", "jpg", "jpeg", "png"])

if arquivo_pdf is not None:
    st.success("Planta carregada com sucesso!")

    # Salva temporariamente o arquivo enviado
    extensao = os.path.splitext(arquivo_pdf.name)[1]

    arquivo_temp = f"temp_planta{extensao}"

    with open(arquivo_temp, "wb") as f:
        f.write(arquivo_pdf.getbuffer())



    # ============================
    # ANÁLISE COM IA
    # ============================

    if st.button("🔍 Analisar Planta"):

        with st.spinner("Analisando planta com IA..."):

            try:

                dados_extraidos = extrair_dados_da_planta(
                    arquivo_temp
                )

                st.session_state["dados_extraidos"] = dados_extraidos


            except ErroExtracaoAmigavel as e:

                st.error(
                    f"⚠️ {e.mensagem_amigavel}"
                )

                if e.detalhe_tecnico:

                    with st.expander(
                        "Detalhes técnicos (para diagnóstico)"
                    ):
                        st.code(
                            e.detalhe_tecnico
                        )

                st.session_state.pop(
                    "dados_extraidos",
                    None
                )


            except Exception as e:

                st.error(
                    "⚠️ Ocorreu um erro inesperado ao analisar a planta."
                )

                with st.expander(
                    "Detalhes técnicos"
                ):
                    st.code(
                        str(e)
                    )

                st.session_state.pop(
                    "dados_extraidos",
                    None
                )
                
            finally:
                if os.path.exists(arquivo_temp):
                    os.remove(arquivo_temp)

    # Passo 2: mostrar os dados extraidos, editaveis, e permitir gerar o orcamento
    if "dados_extraidos" in st.session_state:
        dados = st.session_state["dados_extraidos"]
        confianca = dados.get("confianca", {})

        st.write("### 📊 Dados Extraídos do Projeto")
        st.caption(
            "Confira os valores lidos pela IA, já separados por tipo de ambiente. O indicador "
            "abaixo de cada campo mostra a confiança da IA — 🟢 achou uma cota escrita na planta, "
            "🟡 estimou visualmente, 🔴 teve pouca base pra decidir. Corrija antes de gerar o orçamento."
        )

        st.write("**Piso, por tipo de ambiente**")
        col1, col2, col3 = st.columns(3)
        with col1:
            area_piso_seco = st.number_input(
                "Área Seca — m² (sala, quarto, cozinha)",
                value=float(dados.get("area_piso_seco", 0)), step=0.5, min_value=0.0
            )
            mostrar_badge("area_piso_seco", confianca)
        with col2:
            area_piso_molhado = st.number_input(
                "Área Molhada — m² (banheiro, área de serviço)",
                value=float(dados.get("area_piso_molhado", 0)), step=0.5, min_value=0.0
            )
            mostrar_badge("area_piso_molhado", confianca)
        with col3:
            area_piso_externo = st.number_input(
                "Área Externa — m² (varanda, garagem)",
                value=float(dados.get("area_piso_externo", 0)), step=0.5, min_value=0.0
            )
            mostrar_badge("area_piso_externo", confianca)

        st.write("**Paredes, portas e janelas**")
        col4, col5 = st.columns(2)
        with col4:
            metros_parede = st.number_input(
                "Paredes Lineares (m)",
                value=float(dados["metros_parede"]), step=0.5, min_value=0.0
            )
            mostrar_badge("metros_parede", confianca)

            portas_internas = st.number_input(
                "Portas Internas (un)",
                value=int(dados.get("portas_internas", 0)), step=1, min_value=0
            )
            mostrar_badge("portas_internas", confianca)
        with col5:
            janelas = st.number_input(
                "Janelas (un)",
                value=int(dados.get("janelas", 0)), step=1, min_value=0
            )
            mostrar_badge("janelas", confianca)

            portas_externas = st.number_input(
                "Portas Externas (un)",
                value=int(dados.get("portas_externas", 0)), step=1, min_value=0
            )
            mostrar_badge("portas_externas", confianca)

        # Alerta agregado se algum campo saiu com confianca baixa --
        # reforca visualmente alem do badge individual, ja que e facil
        # passar batido por um badge sozinho no meio da tela.
        campos_baixa_confianca = [
            campo for campo in CAMPOS_EXTRACAO
            if confianca.get(campo, {}).get("nivel") == "baixa"
        ]
        if campos_baixa_confianca:
            st.warning(
                "🔴 A IA teve baixa confiança em algum(ns) campo(s) acima. "
                "Recomendamos conferir esses valores direto na planta antes de prosseguir."
            )

        # Modelo de dominio com os valores ATUAIS dos campos (editados ou
        # nao). Centraliza area total, area de parede etc. num so lugar,
        # em vez de recalcular em cada funcao que precisa desses numeros.
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

        # Validacao de faixa roda sobre os valores ATUAIS dos campos --
        # assim reage toda vez que o usuario mexe em algum numero, nao so
        # uma vez logo apos a extracao.
        avisos = validar_dados({"area_piso": area_piso_total, "metros_parede": metros_parede,
                                 "portas": dados_extracao.portas_total, "janelas": janelas})
        if avisos:
            st.warning(
                "⚠️ Alguns valores parecem incomuns. Confira antes de gerar o orçamento:\n\n"
                + "\n".join(f"- {aviso}" for aviso in avisos)
            )

        st.write("---")

        # Passo 3: materiais -- valor SUGERIDO com base nos coeficientes
        # de consumo padrao (core/calculator.py), mas editavel, ja que
        # o preco de material varia por fornecedor/regiao/negociacao.
        st.write("### 📦 Materiais")
        st.caption(
            "Quantidades calculadas a partir da planta e do padrão de acabamento escolhido. "
            "Edite o preço unitário conforme seu fornecedor."
        )

        materiais_sugeridos = calcular_materiais(dados_extracao, padrao, estrutura)

        chave_mat = "materiais_editados"
        if chave_mat not in st.session_state:
            st.session_state[chave_mat] = materiais_sugeridos

        tabela_mat = st.data_editor(
            st.session_state[chave_mat],
            column_config={
                "Tipo": None,  # oculta a coluna, e so pra uso interno
                "Material": st.column_config.TextColumn("Material", disabled=True),
                "Quantidade": st.column_config.NumberColumn("Quantidade", disabled=True),
                "Preco_Unit": st.column_config.NumberColumn("Preço Unit. (R$)", min_value=0.0, step=0.5),
                "Total": st.column_config.NumberColumn("Total (R$)", disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            key="editor_materiais",
        )

        # Recalcula o Total de cada linha apos a edicao do usuario, e
        # guarda de volta no session_state para persistir entre reruns.
        materiais_final = []
        for item in tabela_mat:
            item = dict(item)
            item["Total"] = round(item["Quantidade"] * item["Preco_Unit"], 2)
            materiais_final.append(item)
        st.session_state[chave_mat] = materiais_final

        total_materiais = sum(item["Total"] for item in materiais_final)
        st.caption(f"Total de materiais: R$ {total_materiais:,.2f}")

        st.write("---")

        # Passo 4: mao de obra -- valor SUGERIDO, mas sempre editavel,
        # ja que o preco de mao de obra varia por equipe/regiao muito
        # mais do que o de material. Recalculamos a cada rerun para
        # refletir mudancas no estado/padrao/quantitativos acima, mas
        # preservamos edicoes manuais do usuario via session_state.
        st.write("### 👷 Mão de Obra")
        st.caption(
            "Valores sugeridos com base em composições SINAPI aproximadas. "
            "Edite livremente conforme o preço da sua equipe."
        )

        mao_de_obra_sugerida = calcular_mao_de_obra(dados_extracao, estrutura)

        chave_mo = "mao_de_obra_editada"
        # Se ainda nao existe edicao do usuario para esta config, usa a
        # sugestao. Se ja existe, preserva a edicao (nao sobrescreve a
        # cada rerun so porque o usuario mexeu num number_input acima).
        if chave_mo not in st.session_state:
            st.session_state[chave_mo] = mao_de_obra_sugerida

        tabela_mo = st.data_editor(
            st.session_state[chave_mo],
            column_config={
                "Tipo": None,  # oculta a coluna, e so pra uso interno
                "Material": st.column_config.TextColumn("Serviço", disabled=True),
                "Quantidade": st.column_config.NumberColumn("Quantidade", disabled=True),
                "Preco_Unit": st.column_config.NumberColumn("Preço Unit. (R$)", min_value=0.0, step=0.5),
                "Total": st.column_config.NumberColumn("Total (R$)", disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            key="editor_mao_de_obra",
        )

        # Recalcula o Total de cada linha apos a edicao do usuario, e
        # guarda de volta no session_state para persistir entre reruns.
        mao_de_obra_final = []
        for item in tabela_mo:
            item = dict(item)
            item["Total"] = round(item["Quantidade"] * item["Preco_Unit"], 2)
            mao_de_obra_final.append(item)
        st.session_state[chave_mo] = mao_de_obra_final

        total_mao_de_obra = sum(item["Total"] for item in mao_de_obra_final)
        st.caption(f"Total de mão de obra: R$ {total_mao_de_obra:,.2f}")

        st.write("---")

        # Passo 5: BDI -- percentual aplicado sobre o custo direto
        # (material + mao de obra) para chegar ao preco de venda.
        # 25% e uma referencia comum em obra residencial pequena, mas
        # varia MUITO conforme a empresa/negociacao -- por isso e um
        # campo livre, nao um valor fixo.
        st.write("### 💰 BDI (Benefícios e Despesas Indiretas)")
        st.caption(
            "Percentual aplicado sobre o custo direto para cobrir administração, "
            "lucro, impostos e imprevistos. Defina como 0% se quiser ver apenas o custo direto."
        )
        bdi_percentual = st.number_input(
            "BDI (%)", min_value=0.0, max_value=100.0, value=25.0, step=1.0
        )

        st.write("---")

        if st.button("🚀 Gerar Orçamento Completo"):
            if not nome_projeto.strip():
                st.error("Informe o nome do projeto/cliente antes de gerar o orçamento (campo no topo da página).")
            else:
                with st.spinner("Calculando insumos e gerando documentos..."):
                    # Toda a logica de negocio (materiais + mao de obra,
                    # custo direto, preco de venda, nome de arquivo) vive em
                    # core/orcamento_service.py -- app.py so orquestra a tela.
                    orcamento_final = orcamento_service.montar_orcamento_completo(
                        materiais_final, mao_de_obra_final
                    )
                    custo_direto, preco_venda = orcamento_service.calcular_custo_e_preco(
                        orcamento_final, bdi_percentual
                    )

                    # Nome de arquivo UNICO por orcamento (timestamp), pra nao
                    # sobrescrever orcamentos anteriores e manter o historico
                    # sempre com os arquivos correspondentes disponiveis pra download.
                    base_nome = orcamento_service.nome_arquivo_seguro(nome_projeto)
                    excel_path = os.path.join(PASTA_ORCAMENTOS, f"{base_nome}.xlsx")
                    pdf_path = os.path.join(PASTA_ORCAMENTOS, f"{base_nome}.pdf")

                    # Excel: uso interno, detalhamento completo linha a linha
                    caminho_excel = gerar_excel(orcamento_final, excel_path, bdi_percentual)

                    # PDF: proposta pra enviar ao cliente, com capa e totais por
                    # servico, personalizada com o perfil salvo (nome/logo/contato)
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

                    # Salva o registro no historico (banco local historico.db)
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

                    # Dashboard-resumo: visao rapida dos numeros principais
                    # do orcamento recem-gerado, antes dos botoes de download.
                    st.write("### 📊 Resumo do Orçamento")
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    col_m1.metric("Área Total", f"{area_piso_total:.0f} m²")
                    col_m2.metric("Paredes", f"{metros_parede:.0f} m")
                    col_m3.metric("Portas + Janelas", f"{portas_internas + portas_externas + janelas} un")
                    col_m4.metric("Preço de Venda", f"R$ {preco_venda:,.2f}")

                    # Dois downloads lado a lado: Excel (uso interno) e PDF (cliente)
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        with open(caminho_excel, "rb") as file:
                            st.download_button(
                                label="📊 Baixar Excel (uso interno)",
                                data=file,
                                file_name=os.path.basename(caminho_excel),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                            )
                    with col_dl2:
                        with open(caminho_pdf, "rb") as file:
                            st.download_button(
                                label="📄 Baixar PDF (proposta ao cliente)",
                                data=file,
                                file_name=os.path.basename(caminho_pdf),
                                mime="application/pdf",
                                use_container_width=True,
                            )

st.write("---")

# --- Historico de orcamentos ja gerados ---
st.write("### 📁 Histórico de Orçamentos")

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
