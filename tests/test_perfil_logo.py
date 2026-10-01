"""Logo da empresa guardada no Postgres (base64 em configuracoes), pra
sobreviver ao disco efêmero do Render. O banco é simulado por um dict."""
import io
import os

import fitz
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api.main import app
from api.routers import historico as historico_router
from core import paths, perfil_empresa


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), "blue").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def banco(monkeypatch, tmp_path):
    configuracoes = {}
    monkeypatch.setattr(paths, "PASTA_PERFIL", str(tmp_path))
    monkeypatch.setattr(perfil_empresa, "salvar_configuracao", lambda chave, valor: configuracoes.update({chave: valor}) or True)
    monkeypatch.setattr(perfil_empresa, "obter_configuracao", configuracoes.get)
    return configuracoes


def test_logo_vai_pro_banco_e_volta_depois_do_redeploy(banco, tmp_path):
    conteudo = _png()
    caminho_local = perfil_empresa.salvar_logo(conteudo, ".png")
    os.remove(caminho_local)  # redeploy: disco local apagado

    with perfil_empresa.arquivo_logo(caminho_local) as caminho:
        assert caminho != caminho_local
        with open(caminho, "rb") as f:
            assert f.read() == conteudo
    assert not os.path.exists(caminho)  # temporário removido ao sair


def test_sem_banco_usa_arquivo_local(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "PASTA_PERFIL", str(tmp_path))
    monkeypatch.setattr(perfil_empresa, "salvar_configuracao", lambda _chave, _valor: False)
    monkeypatch.setattr(perfil_empresa, "obter_configuracao", lambda _chave: None)

    caminho_local = perfil_empresa.salvar_logo(_png(), ".png")

    with perfil_empresa.arquivo_logo(caminho_local) as caminho:
        assert caminho == caminho_local


def test_salvar_logo_remove_a_anterior(banco, tmp_path):
    perfil_empresa.salvar_logo(b"jpg antigo", ".jpg")
    perfil_empresa.salvar_logo(_png(), ".png")
    assert [p.name for p in tmp_path.iterdir()] == ["logo.png"]
    assert banco["logo_empresa"]["extensao"] == ".png"


def test_pdf_do_historico_usa_logo_do_banco(banco, monkeypatch, tmp_path):
    perfil_empresa.salvar_logo(_png(), ".png")
    registro = {
        "nome_projeto": "Casa", "estado_uf": "Boa Vista/RR", "padrao": "Médio",
        "tipo_cobertura": "Telhado", "area_piso": 50, "bdi_percentual": 0, "cliente": "",
        "data_criacao": "05/03/2025 14:30",
        "orcamento_json": [{"Tipo": "Material", "Material": "Bloco", "Quantidade": 2, "Preco_Unit": 10.0, "Total": 20.0, "Fase": "Estrutura"}],
    }
    perfil = {
        "nome_empresa": "", "profissional_responsavel": "", "telefone": "", "email": "",
        "registro": "", "caminho_logo": "/opt/render/project/src/perfil_empresa/logo.png",  # caminho velho
    }
    monkeypatch.setattr(historico_router, "buscar_orcamento", lambda _id: registro)
    monkeypatch.setattr(historico_router, "carregar_perfil", lambda: perfil)
    monkeypatch.setenv("AUTH_DISABLED", "true")

    resposta = TestClient(app).get("/api/historico/1/pdf")

    assert resposta.status_code == 200
    with fitz.open(stream=resposta.content, filetype="pdf") as doc:
        assert doc[0].get_images()
