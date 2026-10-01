"""Testes de core/vision.py -- normalizacao da resposta da IA nos 7 campos
agregados (CAMPOS_AGREGADOS em core/models.py) e na confianca, sem chamar
a API real. Classificacao de erro do Gemini, monitor de cota e confianca
malformada estao em tests/test_bugs_auditoria.py."""
import pytest

from config import DADOS_MOCK
from core import vision
from core.models import CAMPOS_AGREGADOS


@pytest.fixture
def resposta_ia(monkeypatch):
    """Simula a resposta da IA sem mock nem cache; devolve uma funcao que
    define o JSON que o Gemini "retornou"."""
    monkeypatch.setattr(vision, "MOCK_AI", False)
    monkeypatch.setattr(vision, "USE_CACHE", False)

    def definir(dados):
        monkeypatch.setattr(vision, "_chamar_gemini_e_obter_json", lambda *_a: dados)

    return definir


def test_mock_devolve_dados_fixos_sem_layout(monkeypatch):
    monkeypatch.setattr(vision, "MOCK_AI", True)
    dados = vision.extrair_dados_da_planta("planta.png")
    assert dados is DADOS_MOCK
    assert "layout" not in dados
    assert all(campo in dados for campo in CAMPOS_AGREGADOS)


def test_prompt_nao_pede_mais_geometria():
    assert "layout" not in vision.PROMPT_EXTRACAO
    assert "GEOMETRIA" not in vision.PROMPT_EXTRACAO
    for campo in CAMPOS_AGREGADOS:
        assert f'"{campo}"' in vision.PROMPT_EXTRACAO


def test_campos_ausentes_ou_null_viram_zero(resposta_ia):
    resposta_ia({"area_piso_seco": 50, "metros_parede": 40, "janelas": None})

    dados = vision.extrair_dados_da_planta("planta.png")

    assert dados["area_piso_seco"] == 50
    assert dados["janelas"] == 0
    assert dados["portas_internas"] == 0


def test_confianca_ausente_recebe_media_em_todos_os_campos(resposta_ia):
    resposta_ia({"area_piso_seco": 50, "metros_parede": 40})

    dados = vision.extrair_dados_da_planta("planta.png")

    assert set(dados["confianca"]) == set(CAMPOS_AGREGADOS)
    assert dados["confianca"]["janelas"]["nivel"] == "media"


def test_confianca_informada_pela_ia_e_preservada(resposta_ia):
    resposta_ia({
        "area_piso_seco": 50, "metros_parede": 40,
        "confianca": {"area_piso_seco": {"nivel": "alta", "motivo": "cota escrita"}},
    })

    dados = vision.extrair_dados_da_planta("planta.png")

    assert dados["confianca"]["area_piso_seco"] == {"nivel": "alta", "motivo": "cota escrita"}


def test_parede_subestimada_marca_confianca_baixa(resposta_ia):
    # 100 m² de piso pede ao menos 55 m de parede.
    resposta_ia({"area_piso_seco": 100, "metros_parede": 30,
                 "confianca": {"metros_parede": {"nivel": "alta", "motivo": "x"}}})

    dados = vision.extrair_dados_da_planta("planta.png")

    assert dados["confianca"]["metros_parede"]["nivel"] == "baixa"
    assert dados["metros_parede"] == 30  # avisa, mas nao substitui o valor


def test_parede_plausivel_mantem_confianca(resposta_ia):
    resposta_ia({"area_piso_seco": 100, "metros_parede": 80,
                 "confianca": {"metros_parede": {"nivel": "alta", "motivo": "x"}}})

    dados = vision.extrair_dados_da_planta("planta.png")

    assert dados["confianca"]["metros_parede"]["nivel"] == "alta"


def test_resultado_e_salvo_e_reaproveitado_do_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(vision, "MOCK_AI", False)
    monkeypatch.setattr(vision, "USE_CACHE", True)
    monkeypatch.setattr(vision.cache, "CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(vision, "_registrar_chamada_sem_falhar", lambda **_kw: None)
    chamadas = []

    def gemini(*_a):
        chamadas.append(1)
        return {"area_piso_seco": 50, "metros_parede": 40}

    monkeypatch.setattr(vision, "_chamar_gemini_e_obter_json", gemini)
    planta = tmp_path / "planta.png"
    planta.write_bytes(b"planta")

    primeira = vision.extrair_dados_da_planta(str(planta))
    segunda = vision.extrair_dados_da_planta(str(planta))

    assert primeira == segunda
    assert len(chamadas) == 1
