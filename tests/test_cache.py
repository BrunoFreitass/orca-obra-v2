"""Testes de core/cache.py -- a chave inclui modelo e versao do prompt."""
import hashlib

from config import GEMINI_MODEL
from core import cache, vision


def test_mesmo_arquivo_e_contexto_reaproveita_resposta(monkeypatch, tmp_path):
    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path))
    planta = tmp_path / "planta.png"
    planta.write_bytes(b"planta")

    cache.salvar_cache(str(planta), {"area_piso_seco": 10}, "modelo-a:v1")

    assert cache.buscar_cache(str(planta), "modelo-a:v1") == {"area_piso_seco": 10}


def test_trocar_modelo_ou_prompt_nao_devolve_resultado_velho(monkeypatch, tmp_path):
    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path))
    planta = tmp_path / "planta.png"
    planta.write_bytes(b"planta")

    cache.salvar_cache(str(planta), {"area_piso_seco": 10}, "modelo-a:v1")

    assert cache.buscar_cache(str(planta), "modelo-b:v1") is None
    assert cache.buscar_cache(str(planta), "modelo-a:v2") is None


def test_contexto_da_extracao_usa_modelo_e_hash_do_prompt():
    versao = hashlib.sha256(vision.PROMPT_EXTRACAO.encode("utf-8")).hexdigest()[:12]
    assert f"{GEMINI_MODEL}:{versao}" == vision._CONTEXTO_CACHE
