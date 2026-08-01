"""Testes de core/orcamento_service.py -- soma de custo direto, BDI,
e montagem do orcamento final."""

from core import orcamento_service


class TestCalcularCustoEPreco:
    def test_bdi_zero_preco_venda_igual_ao_custo_direto(self):
        itens = [{"Total": 1000.0}, {"Total": 500.0}]
        custo, venda = orcamento_service.calcular_custo_e_preco(itens, bdi_percentual=0)
        assert custo == 1500.0
        assert venda == 1500.0

    def test_bdi_25_por_cento(self):
        itens = [{"Total": 1000.0}]
        custo, venda = orcamento_service.calcular_custo_e_preco(itens, bdi_percentual=25)
        assert custo == 1000.0
        assert venda == 1250.0

    def test_lista_vazia_nao_quebra(self):
        custo, venda = orcamento_service.calcular_custo_e_preco([], bdi_percentual=25)
        assert custo == 0.0
        assert venda == 0.0

    def test_arredonda_a_duas_casas(self):
        itens = [{"Total": 33.333}, {"Total": 33.333}]
        custo, venda = orcamento_service.calcular_custo_e_preco(itens, bdi_percentual=10)
        assert custo == 66.67  # 66.666 arredondado
        assert venda == round(66.67 * 1.10, 2)


class TestMontarOrcamentoCompleto:
    def test_junta_materiais_e_mao_de_obra_preservando_ordem(self):
        materiais = [{"Tipo": "Material", "Material": "Bloco"}]
        mao_de_obra = [{"Tipo": "Mão de Obra", "Material": "Alvenaria"}]
        resultado = orcamento_service.montar_orcamento_completo(materiais, mao_de_obra)
        assert resultado == materiais + mao_de_obra
        assert resultado[0]["Tipo"] == "Material"
        assert resultado[1]["Tipo"] == "Mão de Obra"

    def test_nao_altera_as_listas_originais(self):
        # Editar o resultado nao deveria vazar de volta pras listas de
        # origem (evita bug sutil de estado compartilhado no Streamlit,
        # onde app.py guarda materiais/mao_de_obra em st.session_state).
        materiais = [{"Total": 10}]
        mao_de_obra = [{"Total": 20}]
        resultado = orcamento_service.montar_orcamento_completo(materiais, mao_de_obra)
        resultado.append({"Total": 999})
        assert len(materiais) == 1
        assert len(mao_de_obra) == 1


class TestNomeArquivoSeguro:
    def test_remove_caracteres_invalidos(self):
        nome = orcamento_service.nome_arquivo_seguro("Rua Oito, 447 / Jardim Tropical")
        # nao deve conter barra nem virgula
        assert "/" not in nome
        assert "," not in nome

    def test_sempre_comeca_com_timestamp_de_14_digitos(self):
        nome = orcamento_service.nome_arquivo_seguro("Teste")
        carimbo = nome.split("_")[0] + "_" + nome.split("_")[1]
        assert len(carimbo) == 15  # AAAAMMDD_HHMMSS
        assert carimbo.replace("_", "").isdigit()

    def test_respeita_o_limite_de_caracteres(self):
        nome_longo = "A" * 100
        resultado = orcamento_service.nome_arquivo_seguro(nome_longo, limite=10)
        # 10 caracteres do nome + o carimbo de tempo na frente
        parte_nome = resultado.split("_", 2)[-1]
        assert len(parte_nome) <= 10
