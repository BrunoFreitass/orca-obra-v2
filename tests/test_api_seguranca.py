import base64
import contextlib
import io

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from PIL import Image

from api.main import app
from api.routers import perfil as perfil_router
from api.routers import precos as precos_router
from api.routers import sinapi as sinapi_router
from core import perfil_empresa

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sem_auth(monkeypatch):
    monkeypatch.setenv("AUTH_DISABLED", "true")


def _basic(usuario, senha):
    token = base64.b64encode(f"{usuario}:{senha}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _xlsx_vazio() -> bytes:
    buffer = io.BytesIO()
    Workbook().save(buffer)
    return buffer.getvalue()


def _imagem(formato: str) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buffer, format=formato)
    return buffer.getvalue()


class TestAutenticacao:
    @pytest.fixture(autouse=True)
    def _credenciais(self, monkeypatch):
        monkeypatch.delenv("AUTH_DISABLED", raising=False)
        monkeypatch.setenv("APP_USER", "admin")
        monkeypatch.setenv("APP_PASSWORD", "s3nha")

    def test_sem_credencial_retorna_401_com_www_authenticate(self, client):
        resposta = client.get("/api/precos")
        assert resposta.status_code == 401
        assert resposta.headers["WWW-Authenticate"] == 'Basic realm="OrcaObra"'

    def test_credencial_errada_retorna_401(self, client):
        assert client.get("/api/precos", headers=_basic("admin", "errada")).status_code == 401
        assert client.get("/api/precos", headers=_basic("outro", "s3nha")).status_code == 401

    def test_cabecalho_malformado_retorna_401(self, client):
        assert client.get("/api/precos", headers={"Authorization": "Basic %%%"}).status_code == 401
        assert client.get("/api/precos", headers={"Authorization": "Bearer x"}).status_code == 401

    def test_credencial_certa_retorna_200(self, client):
        assert client.get("/api/precos", headers=_basic("admin", "s3nha")).status_code == 200

    def test_health_sem_credencial_retorna_200(self, client):
        assert client.get("/api/health").status_code == 200

    def test_sem_app_user_e_sem_auth_disabled_retorna_503(self, client, monkeypatch):
        monkeypatch.delenv("APP_USER")
        resposta = client.get("/api/precos", headers=_basic("admin", "s3nha"))
        assert resposta.status_code == 503
        assert "APP_USER" in resposta.json()["detail"]

    def test_auth_disabled_libera_sem_credencial(self, client, monkeypatch):
        monkeypatch.delenv("APP_USER")
        monkeypatch.setenv("AUTH_DISABLED", "true")
        assert client.get("/api/precos").status_code == 200


def test_headers_de_seguranca_em_toda_resposta(client, monkeypatch):
    monkeypatch.delenv("AUTH_DISABLED", raising=False)
    monkeypatch.setenv("APP_USER", "admin")
    monkeypatch.setenv("APP_PASSWORD", "s3nha")
    for resposta in (client.get("/api/health"), client.get("/api/precos")):
        assert resposta.headers["X-Content-Type-Options"] == "nosniff"
        assert resposta.headers["X-Frame-Options"] == "DENY"
        assert resposta.headers["Referrer-Policy"] == "same-origin"


@pytest.mark.usefixtures("sem_auth")
class TestUploadSinapi:
    @pytest.fixture
    def pasta_upload(self, monkeypatch, tmp_path):
        """TemporaryDirectory fixo e sem limpeza, pra inspecionar o que foi gravado."""
        pasta = tmp_path / "base" / "upload"
        pasta.mkdir(parents=True)
        monkeypatch.setattr(sinapi_router.tempfile, "TemporaryDirectory", lambda: contextlib.nullcontext(str(pasta)))
        return pasta

    @pytest.mark.parametrize("nome", ["../../evil.xlsx", "/tmp/evil.xlsx", "..\\..\\evil.xlsx"])
    def test_filename_malicioso_nao_escreve_fora_do_tmpdir(self, client, pasta_upload, nome):
        resposta = client.post("/api/sinapi/importar", files={"arquivos": (nome, _xlsx_vazio(), XLSX)})
        assert resposta.status_code == 200
        gravados = list(pasta_upload.parent.parent.rglob("*.xlsx"))
        assert len(gravados) == 1
        assert gravados[0].parent == pasta_upload
        assert gravados[0].name == "arquivo_0_evil.xlsx"

    def test_mes_de_referencia_continua_vindo_do_nome(self, client, pasta_upload):
        resposta = client.post(
            "/api/sinapi/importar", files={"arquivos": ("SINAPI_2025_08.xlsx", _xlsx_vazio(), XLSX)}
        )
        assert resposta.status_code == 200
        assert resposta.json()["mes_ref"] == "2025-08"

    def test_rejeita_extensao_diferente_de_xlsx(self, client):
        resposta = client.post("/api/sinapi/importar", files={"arquivos": ("x.xls", b"abc", XLSX)})
        assert resposta.status_code == 400

    def test_rejeita_mais_de_5_arquivos(self, client):
        arquivos = [("arquivos", (f"a{i}.xlsx", _xlsx_vazio(), XLSX)) for i in range(6)]
        assert client.post("/api/sinapi/importar", files=arquivos).status_code == 400

    def test_rejeita_arquivo_grande(self, client, monkeypatch):
        monkeypatch.setattr(sinapi_router, "MAX_TAMANHO_ARQUIVO", 10)
        resposta = client.post("/api/sinapi/importar", files={"arquivos": ("a.xlsx", _xlsx_vazio(), XLSX)})
        assert resposta.status_code == 413

    def test_xlsx_invalido_retorna_400(self, client):
        resposta = client.post("/api/sinapi/importar", files={"arquivos": ("a.xlsx", b"nao e zip", XLSX)})
        assert resposta.status_code == 400
        assert "mensagem_amigavel" in resposta.json()["detail"]


@pytest.mark.usefixtures("sem_auth")
class TestUploadPrecos:
    def test_xlsx_invalido_retorna_400(self, client):
        resposta = client.post("/api/precos/importar", files={"arquivo": ("a.xlsx", b"nao e zip", XLSX)})
        assert resposta.status_code == 400
        assert "mensagem_amigavel" in resposta.json()["detail"]

    def test_rejeita_arquivo_grande(self, client, monkeypatch):
        monkeypatch.setattr(precos_router, "MAX_TAMANHO_PLANILHA", 10)
        resposta = client.post("/api/precos/importar", files={"arquivo": ("a.xlsx", _xlsx_vazio(), XLSX)})
        assert resposta.status_code == 413


@pytest.mark.usefixtures("sem_auth")
class TestUploadLogo:
    @pytest.fixture(autouse=True)
    def _isola_perfil(self, monkeypatch, tmp_path):
        """Sem isso o perfil iria pro banco (DATABASE_URL do .env) e pro
        perfil_empresa.json real."""
        monkeypatch.setattr(perfil_empresa.paths, "PASTA_PERFIL", str(tmp_path))
        perfil = {
            "nome_empresa": "", "profissional_responsavel": "", "telefone": "",
            "email": "", "registro": "", "caminho_logo": "",
        }
        monkeypatch.setattr(perfil_router, "carregar_perfil", lambda: dict(perfil))
        monkeypatch.setattr(perfil_router, "salvar_perfil", lambda **dados: dados)
        monkeypatch.setattr(perfil_empresa, "salvar_configuracao", lambda _chave, _valor: False)

    @pytest.mark.parametrize("formato,extensao", [("PNG", ".png"), ("JPEG", ".jpg")])
    def test_aceita_png_e_jpeg_pelo_conteudo(self, client, tmp_path, formato, extensao):
        # Nome enviado com extensão enganosa: vale o formato real detectado.
        resposta = client.post("/api/perfil/logo", files={"logo": ("logo.html", _imagem(formato), "text/html")})
        assert resposta.status_code == 200
        assert resposta.json()["caminho_logo"].endswith(f"logo{extensao}")
        assert [p.name for p in tmp_path.iterdir()] == [f"logo{extensao}"]

    def test_remove_logo_anterior(self, client, tmp_path):
        (tmp_path / "logo.svg").write_text("<svg/>")
        client.post("/api/perfil/logo", files={"logo": ("a.png", _imagem("PNG"), "image/png")})
        assert [p.name for p in tmp_path.iterdir()] == ["logo.png"]

    def test_rejeita_conteudo_que_nao_e_imagem(self, client, tmp_path):
        resposta = client.post("/api/perfil/logo", files={"logo": ("logo.png", b"<html></html>", "image/png")})
        assert resposta.status_code == 400
        assert list(tmp_path.iterdir()) == []

    def test_rejeita_formato_fora_de_png_jpeg(self, client):
        resposta = client.post("/api/perfil/logo", files={"logo": ("logo.gif", _imagem("GIF"), "image/gif")})
        assert resposta.status_code == 400

    def test_rejeita_logo_acima_de_2mb(self, client):
        grande = b"\x89PNG" + b"0" * (2 * 1024 * 1024)
        assert client.post("/api/perfil/logo", files={"logo": ("logo.png", grande, "image/png")}).status_code == 413


@pytest.mark.usefixtures("sem_auth")
def test_extracao_rejeita_planta_acima_de_20mb(client, monkeypatch):
    from api.routers import extracao

    monkeypatch.setattr(extracao, "MAX_UPLOAD_SIZE", 10)
    resposta = client.post("/api/extracao", files={"planta": ("p.png", b"0" * 100, "image/png")})
    assert resposta.status_code == 413
