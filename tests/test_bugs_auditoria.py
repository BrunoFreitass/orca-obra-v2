"""Regressões dos bugs apontados na auditoria (fase 2). Cada classe
reproduz um bug; nenhum teste aqui toca banco ou API real."""
from datetime import datetime
from zoneinfo import ZoneInfo

import fitz
import pytest
import requests
from fastapi.testclient import TestClient

from api.main import app
from api.routers import historico as historico_router
from core import historico, monitor_api, orcamento_service, vision
from core.proposta_pdf import gerar_pdf_proposta


class _ConexaoFalsa:
    """Imita o `with _conectar() as conn` do psycopg, guardando o último execute."""

    def __init__(self, linha=None):
        self.linha = linha
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, _sql, params=None):
        self.params = params
        return self

    def fetchone(self):
        return self.linha


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("AUTH_DISABLED", "true")
    return TestClient(app)


def _item(**overrides):
    base = {"Tipo": "Material", "Material": "Bloco", "Quantidade": 2, "Preco_Unit": 10.0, "Total": 20.0, "Fase": "Estrutura"}
    base.update(overrides)
    return base


def _corpo_gerar(**overrides):
    base = {
        "materiais": [_item()], "mao_de_obra": [], "bdi_percentual": 0,
        "nome_projeto": "Casa", "padrao": "Médio", "estrutura": "Telhado",
        "local_obra": "Boa Vista/RR", "area_piso_seco": 50,
    }
    base.update(overrides)
    return base


# --- 1. Total vindo do cliente --------------------------------------------

class TestTotalRecalculadoNoServidor:
    def test_total_do_cliente_e_ignorado(self, client, monkeypatch):
        salvo = {}
        monkeypatch.setattr(orcamento_service, "salvar_orcamento", lambda **kw: salvo.update(kw) or 1)

        corpo = _corpo_gerar(materiais=[_item(Quantidade=2, Preco_Unit=10.0, Total=999999.0)])
        resposta = client.post("/api/orcamento/gerar", json=corpo)

        assert resposta.status_code == 200
        assert resposta.json()["custo_direto"] == 20.0
        assert salvo["custo_direto"] == 20.0
        assert salvo["orcamento_json"][0]["Total"] == 20.0

    def test_total_arredondado_a_duas_casas(self, client, monkeypatch):
        salvo = {}
        monkeypatch.setattr(orcamento_service, "salvar_orcamento", lambda **kw: salvo.update(kw) or 1)

        corpo = _corpo_gerar(materiais=[_item(Quantidade=3, Preco_Unit=3.333, Total=0)])
        client.post("/api/orcamento/gerar", json=corpo)

        assert salvo["orcamento_json"][0]["Total"] == 10.0


# --- 2. Validação de schemas -----------------------------------------------

class TestValidacaoSchemas:
    @pytest.mark.parametrize("campo,valor", [("padrao", "Luxo"), ("estrutura", "Palha")])
    def test_padrao_ou_estrutura_invalido_retorna_422(self, client, campo, valor):
        corpo = {"area_piso_seco": 50, "padrao": "Médio", "estrutura": "Telhado", campo: valor}
        assert client.post("/api/orcamento/materiais", json=corpo).status_code == 422
        assert client.post("/api/orcamento/mao-de-obra", json=corpo).status_code == 422

    @pytest.mark.parametrize("campo", [
        "area_piso_seco", "area_piso_molhado", "area_piso_externo", "metros_parede",
        "portas_internas", "portas_externas", "janelas",
    ])
    def test_valores_negativos_retornam_422(self, client, campo):
        corpo = {"padrao": "Médio", "estrutura": "Telhado", campo: -1}
        assert client.post("/api/orcamento/materiais", json=corpo).status_code == 422
        assert client.post("/api/orcamento/gerar", json=_corpo_gerar(**{campo: -1})).status_code == 422

    @pytest.mark.parametrize("campo", ["Quantidade", "Preco_Unit"])
    def test_item_negativo_retorna_422(self, client, campo):
        corpo = _corpo_gerar(materiais=[_item(**{campo: -5})])
        assert client.post("/api/orcamento/gerar", json=corpo).status_code == 422

    @pytest.mark.parametrize("bdi", [-1, 101])
    def test_bdi_fora_de_0_a_100_retorna_422(self, client, bdi):
        assert client.post("/api/orcamento/gerar", json=_corpo_gerar(bdi_percentual=bdi)).status_code == 422

    @pytest.mark.parametrize("campo", ["nome_projeto", "cliente"])
    def test_texto_longo_demais_retorna_422(self, client, campo):
        assert client.post("/api/orcamento/gerar", json=_corpo_gerar(**{campo: "x" * 201})).status_code == 422


# --- 3. Monitor de cota ----------------------------------------------------

class TestMonitorCota:
    def test_total_nao_conta_cache(self, monkeypatch):
        linha = {"total": 10, "sucessos": 3, "falhas": 2, "caches": 5}
        monkeypatch.setattr(monitor_api, "_conectar", lambda: _ConexaoFalsa(linha))

        resumo = monitor_api.resumo_periodo()

        assert resumo["total"] == 5
        assert resumo["caches"] == 5

    def test_registro_com_banco_fora_nao_derruba_extracao_em_cache(self, monkeypatch):
        def falha(**_kw):
            raise RuntimeError("banco fora")

        monkeypatch.setattr(vision, "MOCK_AI", False)
        monkeypatch.setattr(vision, "USE_CACHE", True)
        monkeypatch.setattr(vision.cache, "buscar_cache", lambda _c: {"area_piso_seco": 10})
        monkeypatch.setattr(vision, "registrar_chamada", falha)

        assert vision.extrair_dados_da_planta("planta.png") == {"area_piso_seco": 10}

    def test_registro_com_banco_fora_nao_derruba_resposta_do_gemini(self, monkeypatch):
        def falha(**_kw):
            raise RuntimeError("banco fora")

        monkeypatch.setattr(vision, "GEMINI_API_KEYS", ["chave"])
        monkeypatch.setattr(vision, "_preparar_imagem", lambda _c: b"img")
        monkeypatch.setattr(vision, "registrar_chamada", falha)
        resultado_gemini = {"candidates": [{"content": {"parts": [{"text": '{"area_piso_seco": 10}'}]}}]}
        monkeypatch.setattr(vision, "_chamar_gemini_com_uma_chave", lambda *_a: (resultado_gemini, None))

        assert vision._chamar_gemini_e_obter_json("prompt", "planta.png")["area_piso_seco"] == 10


# --- 4. Classificação de erro do Gemini ------------------------------------

class TestClassificacaoErroGemini:
    @pytest.fixture(autouse=True)
    def _sem_espera(self, monkeypatch):
        monkeypatch.setattr(vision.time, "sleep", lambda _s: None)

    def test_resposta_nao_json_e_resposta_invalida(self, monkeypatch):
        class RespostaHtml:
            text = "<html>502 Bad Gateway</html>"

            def json(self):
                raise requests.exceptions.JSONDecodeError("Expecting value", self.text, 0)

        monkeypatch.setattr(vision.requests, "post", lambda *_a, **_kw: RespostaHtml())

        resultado, erro = vision._chamar_gemini_com_uma_chave("chave", "prompt", "img")

        assert resultado is None
        assert erro["status"] == "RESPOSTA_INVALIDA"
        assert "502 Bad Gateway" in erro["bruto"]

    def test_falha_de_conexao_continua_erro_de_rede(self, monkeypatch):
        def sem_rede(*_a, **_kw):
            raise requests.exceptions.ConnectionError("sem rede")

        monkeypatch.setattr(vision.requests, "post", sem_rede)

        _, erro = vision._chamar_gemini_com_uma_chave("chave", "prompt", "img")

        assert erro["status"] == "ERRO_DE_REDE"


# --- 5. Confiança malformada vinda da IA -----------------------------------

class TestConfiancaMalformada:
    @pytest.fixture(autouse=True)
    def _sem_mock_nem_cache(self, monkeypatch):
        monkeypatch.setattr(vision, "MOCK_AI", False)
        monkeypatch.setattr(vision, "USE_CACHE", False)

    @pytest.mark.parametrize("confianca", [
        "alta",
        ["metros_parede"],
        {"metros_parede": "baixa", "janelas": None},
    ])
    def test_confianca_fora_do_formato_nao_quebra(self, monkeypatch, confianca):
        # metros_parede baixo de propósito: força o caminho que lê confianca["metros_parede"].
        dados_ia = {"area_piso_seco": 100, "metros_parede": 10, "confianca": confianca}
        monkeypatch.setattr(vision, "_chamar_gemini_e_obter_json", lambda *_a: dados_ia)

        dados = vision.extrair_dados_da_planta("planta.png")

        assert all(isinstance(v, dict) for v in dados["confianca"].values())
        assert dados["confianca"]["metros_parede"]["nivel"] == "baixa"
        assert dados["confianca"]["janelas"]["nivel"] == "media"


# --- 7. Data do PDF regenerado pelo histórico ------------------------------

def _texto_pdf(caminho) -> str:
    with fitz.open(caminho) as doc:
        return "".join(pagina.get_text() for pagina in doc)


_ITENS_PDF = [_item(Total=20.0)]


class TestDataDoPdf:
    def test_pdf_usa_data_informada(self, tmp_path):
        caminho = tmp_path / "p.pdf"
        gerar_pdf_proposta(
            _ITENS_PDF, str(caminho), nome_projeto="Casa", estado_uf="Boa Vista/RR",
            padrao="Médio", tipo_cobertura="Telhado", area_piso=50, data_emissao="05/03/2025",
        )
        assert "05/03/2025" in _texto_pdf(caminho)

    def test_pdf_do_historico_usa_data_de_criacao(self, client, monkeypatch, tmp_path):
        registro = {
            "nome_projeto": "Casa", "estado_uf": "Boa Vista/RR", "padrao": "Médio",
            "tipo_cobertura": "Telhado", "area_piso": 50, "bdi_percentual": 0,
            "cliente": "", "data_criacao": "05/03/2025 14:30", "orcamento_json": _ITENS_PDF,
        }
        perfil = {
            "nome_empresa": "", "profissional_responsavel": "", "telefone": "",
            "email": "", "registro": "", "caminho_logo": "",
        }
        monkeypatch.setattr(historico_router, "buscar_orcamento", lambda _id: registro)
        monkeypatch.setattr(historico_router, "carregar_perfil", lambda: perfil)

        resposta = client.get("/api/historico/1/pdf")

        assert resposta.status_code == 200
        caminho = tmp_path / "h.pdf"
        caminho.write_bytes(resposta.content)
        assert "05/03/2025" in _texto_pdf(caminho)


# --- 8. Fuso horário do histórico ------------------------------------------

def test_historico_grava_data_no_fuso_de_boa_vista(monkeypatch):
    conexao = _ConexaoFalsa({"id": 1})
    monkeypatch.setattr(historico, "_conectar", lambda: conexao)
    fuso = ZoneInfo("America/Boa_Vista")

    antes = datetime.now(fuso).strftime("%d/%m/%Y %H:%M")
    historico.salvar_orcamento(
        nome_projeto="Casa", estado_uf="Boa Vista/RR", padrao="Médio", tipo_cobertura="Telhado",
        area_piso=50, custo_direto=100, bdi_percentual=0, preco_venda=100, orcamento_json=[],
    )
    depois = datetime.now(fuso).strftime("%d/%m/%Y %H:%M")

    assert conexao.params[0] in (antes, depois)
