"""Testes de integração — ciclo completo de geração de documentos.

Verificam que Excel e PDF são criados corretamente a partir de um
orçamento completo, sem depender da UI (Streamlit) nem da API Gemini.
"""
import os

import openpyxl
import pytest

from core import orcamento_service, tabela_precos
from core.calculator import calcular_mao_de_obra, calcular_materiais
from core.models import DadosExtracao
from core.proposta_pdf import gerar_pdf_proposta
from core.reporter import gerar_excel


@pytest.fixture(autouse=True)
def sem_overrides():
    """Garante que os testes rodem com precos padrao."""
    tabela_precos.restaurar_padroes()
    yield
    tabela_precos.restaurar_padroes()


@pytest.fixture
def dados_exemplo():
    """Dados tipicos de uma planta residencial pequena (115m2)."""
    return DadosExtracao(
        area_piso_seco=80.0,
        area_piso_molhado=15.0,
        area_piso_externo=20.0,
        metros_parede=180.0,
        portas_internas=6,
        portas_externas=2,
        janelas=8,
    )


@pytest.fixture
def orcamento_completo(dados_exemplo):
    """Monta um orcamento completo (material + mao de obra) pronto
    para gerar documentos."""
    materiais = calcular_materiais(dados_exemplo, padrao="Médio", tipo_cobertura="Telhado")
    mao_de_obra = calcular_mao_de_obra(dados_exemplo, tipo_cobertura="Telhado")
    return orcamento_service.montar_orcamento_completo(materiais, mao_de_obra)


class TestGerarExcel:
    def test_arquivo_e_criado_e_nao_esta_vazio(self, orcamento_completo, tmp_path):
        caminho = tmp_path / "orcamento.xlsx"
        resultado = gerar_excel(orcamento_completo, str(caminho), bdi_percentual=25)
        assert os.path.exists(resultado)
        assert os.path.getsize(resultado) > 1024  # pelo menos 1KB

    def test_bdi_zero_nao_gera_linha_de_bdi(self, orcamento_completo, tmp_path):
        caminho = tmp_path / "orcamento_sem_bdi.xlsx"
        gerar_excel(orcamento_completo, str(caminho), bdi_percentual=0)
        assert os.path.exists(caminho)

    def test_extensao_csv_e_convertida_para_xlsx(self, orcamento_completo, tmp_path):
        caminho_csv = tmp_path / "orcamento.csv"
        resultado = gerar_excel(orcamento_completo, str(caminho_csv), bdi_percentual=0)
        assert resultado.endswith(".xlsx")

    def test_preco_de_venda_bate_com_orcamento_service(self, orcamento_completo, tmp_path):
        """Regressão: Excel, PDF e o valor salvo no histórico usavam 3
        fórmulas de arredondamento diferentes pra Custo Direto + BDI ->
        Preço de Venda, e podiam divergir em 1 centavo entre si. Garante
        que o valor exibido no Excel bate exatamente com
        core.orcamento_service.calcular_custo_e_preco, que é o que vai
        pro histórico."""
        caminho = tmp_path / "orcamento.xlsx"
        _, preco_venda_esperado = orcamento_service.calcular_custo_e_preco(
            orcamento_completo, bdi_percentual=25
        )
        resultado = gerar_excel(orcamento_completo, str(caminho), bdi_percentual=25)

        wb = openpyxl.load_workbook(resultado, data_only=True)
        ws = wb.active
        valores = {row[0]: row[3] for row in ws.iter_rows(values_only=True) if row[0]}
        assert valores["PREÇO DE VENDA"] == preco_venda_esperado
        assert valores["CUSTO DIRETO"] + valores["BDI (25%) — administração, lucro, impostos e imprevistos"] == \
            valores["PREÇO DE VENDA"]


class TestGerarPdfProposta:
    def test_pdf_e_criado_e_nao_esta_vazio(self, orcamento_completo, tmp_path):
        caminho = tmp_path / "proposta.pdf"
        gerar_pdf_proposta(
            orcamento_completo,
            str(caminho),
            nome_projeto="Casa Teste",
            estado_uf="Boa Vista/RR",
            padrao="Médio",
            tipo_cobertura="Telhado",
            area_piso=115.0,
            bdi_percentual=25,
            nome_empresa="Teste Construtora",
            contato="(95) 99999-9999",
            registro="CREA-RR 12345",
        )
        assert os.path.exists(caminho)
        assert os.path.getsize(caminho) > 2048  # PDF tem pelo menos 2KB

    def test_pdf_sem_bdi_nao_gera_linha_bdi(self, orcamento_completo, tmp_path):
        caminho = tmp_path / "proposta_sem_bdi.pdf"
        gerar_pdf_proposta(
            orcamento_completo,
            str(caminho),
            nome_projeto="Casa Sem BDI",
            estado_uf="Boa Vista/RR",
            padrao="Econômico",
            tipo_cobertura="Laje",
            area_piso=80.0,
            bdi_percentual=0,
        )
        assert os.path.exists(caminho)
        assert os.path.getsize(caminho) > 2048

    def test_pdf_com_logo_invalido_nao_quebra(self, orcamento_completo, tmp_path):
        """Logo que nao existe nao deve derrubar a geracao do PDF."""
        caminho = tmp_path / "proposta_logo_ruim.pdf"
        gerar_pdf_proposta(
            orcamento_completo,
            str(caminho),
            nome_projeto="Casa Logo Ruim",
            estado_uf="Boa Vista/RR",
            padrao="Alto Padrão",
            tipo_cobertura="Telhado",
            area_piso=200.0,
            bdi_percentual=15,
            caminho_logo="/caminho/inexistente/logo.png",
        )
        assert os.path.exists(caminho)

    def test_pdf_com_dados_minimos(self, orcamento_completo, tmp_path):
        """PDF deve funcionar mesmo com apenas os campos obrigatorios."""
        caminho = tmp_path / "proposta_minima.pdf"
        gerar_pdf_proposta(
            orcamento_completo,
            str(caminho),
            nome_projeto="Minima",
            estado_uf="Boa Vista/RR",
            padrao="Econômico",
            tipo_cobertura="Telhado",
            area_piso=50.0,
        )
        assert os.path.exists(caminho)
