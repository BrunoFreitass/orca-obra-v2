"""Testes de core/tabela_precos.py -- ciclo de download/edicao/upload
da planilha de precos customizados."""
import os

import pytest
from openpyxl import Workbook

from core import tabela_precos as tp
from core.coeficientes import PRECO_CIMENTO_SACO, PRECO_AREIA_M3


@pytest.fixture(autouse=True)
def sem_overrides_salvos():
    """Garante que cada teste comeca e termina sem nenhum override
    salvo em disco -- os testes nao devem se afetar uns aos outros,
    nem deixar lixo no arquivo real usado pelo app."""
    tp.restaurar_padroes()
    yield
    tp.restaurar_padroes()


def _planilha_com(linhas):
    wb = Workbook()
    ws = wb.active
    ws.append(["Chave", "Categoria", "Item", "Preço (R$)", "Fonte", "Data"])
    for linha in linhas:
        ws.append(linha)
    return wb


class TestObterPreco:
    def test_sem_override_retorna_o_padrao(self):
        preco = tp.obter_preco("cimento", PRECO_CIMENTO_SACO)
        assert preco.valor == PRECO_CIMENTO_SACO.valor
        assert preco.fonte == PRECO_CIMENTO_SACO.fonte

    def test_com_override_retorna_o_valor_customizado(self):
        tp.salvar_overrides({"cimento": 50.0})
        preco = tp.obter_preco("cimento", PRECO_CIMENTO_SACO)
        assert preco.valor == 50.0
        assert preco.fonte == "Tabela de preços enviada pelo usuário"

    def test_chave_sem_override_nao_e_afetada_por_override_de_outra_chave(self):
        tp.salvar_overrides({"cimento": 50.0})
        preco_areia = tp.obter_preco("areia", PRECO_AREIA_M3)
        # areia nao foi customizada -- deve continuar no padrao
        assert preco_areia.fonte != "Tabela de preços enviada pelo usuário"


class TestImportarTabelaExcel:
    def test_valor_alterado_entra_em_atualizados(self, tmp_path):
        caminho = tmp_path / "planilha.xlsx"
        _planilha_com([["cimento", "Material", "Cimento", 50.0, "", ""]]).save(caminho)
        atualizados, avisos = tp.importar_tabela_excel(str(caminho))
        assert atualizados == {"cimento": 50.0}

    def test_valor_igual_ao_atual_nao_entra_em_atualizados(self, tmp_path):
        caminho = tmp_path / "planilha.xlsx"
        _planilha_com([["cimento", "Material", "Cimento", PRECO_CIMENTO_SACO.valor, "", ""]]).save(caminho)
        atualizados, avisos = tp.importar_tabela_excel(str(caminho))
        assert atualizados == {}

    def test_chave_desconhecida_gera_aviso_e_e_ignorada(self, tmp_path):
        caminho = tmp_path / "planilha.xlsx"
        _planilha_com([["nao_existe", "Material", "Fantasma", 99, "", ""]]).save(caminho)
        atualizados, avisos = tp.importar_tabela_excel(str(caminho))
        assert atualizados == {}
        assert any("desconhecida" in a for a in avisos)

    def test_valor_nao_numerico_gera_aviso_e_e_ignorado(self, tmp_path):
        caminho = tmp_path / "planilha.xlsx"
        _planilha_com([["cimento", "Material", "Cimento", "abc", "", ""]]).save(caminho)
        atualizados, avisos = tp.importar_tabela_excel(str(caminho))
        assert atualizados == {}
        assert any("não numérico" in a for a in avisos)

    def test_valor_zero_ou_negativo_gera_aviso_e_e_ignorado(self, tmp_path):
        caminho = tmp_path / "planilha.xlsx"
        _planilha_com([["cimento", "Material", "Cimento", 0, "", ""]]).save(caminho)
        atualizados, avisos = tp.importar_tabela_excel(str(caminho))
        assert atualizados == {}
        assert any("zero ou negativo" in a for a in avisos)

    def test_item_ausente_na_planilha_gera_aviso(self, tmp_path):
        caminho = tmp_path / "planilha.xlsx"
        _planilha_com([["cimento", "Material", "Cimento", 50.0, "", ""]]).save(caminho)
        _, avisos = tp.importar_tabela_excel(str(caminho))
        assert any("não apareceram na planilha enviada" in a for a in avisos)


class TestRestaurarPadroes:
    def test_remove_o_arquivo_de_overrides(self):
        tp.salvar_overrides({"cimento": 50.0})
        assert os.path.exists(tp.CAMINHO_OVERRIDES)
        tp.restaurar_padroes()
        assert not os.path.exists(tp.CAMINHO_OVERRIDES)

    def test_chamar_sem_overrides_existentes_nao_quebra(self):
        tp.restaurar_padroes()
        tp.restaurar_padroes()  # chamar de novo nao deve gerar erro
