"""Testes de core/vision.py -- normalizacao defensiva do bloco opcional
'layout' (geometria). O orcamento nunca depende deste campo (ver
CAMPOS_AGREGADOS em core/vision.py), entao qualquer formato inesperado
precisa cair em fallback seguro (disponivel: False) sem lancar excecao."""
from core.vision import _normalizar_layout


def _comodo(**overrides):
    base = {"nome": "Sala", "tipo_piso": "seco", "x": 0.0, "y": 0.0, "largura": 5.0, "comprimento": 4.0}
    base.update(overrides)
    return base


def _parede(**overrides):
    base = {"x1": 0.0, "y1": 0.0, "x2": 5.0, "y2": 0.0}
    base.update(overrides)
    return base


def _layout_valido():
    return {
        "disponivel": True,
        "motivo_indisponivel": "",
        "comodos": [_comodo()],
        "paredes": [_parede()],
        "aberturas": [{"tipo": "janela", "parede_index": 0, "posicao": 0.5}],
    }


class TestLayoutAusente:
    def test_chave_layout_ausente_cai_em_fallback(self):
        dados = {"area_piso_seco": 20.0}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is False
        assert resultado["layout"]["comodos"] == []
        assert resultado["layout"]["paredes"] == []
        assert resultado["layout"]["aberturas"] == []

    def test_layout_none_cai_em_fallback(self):
        dados = {"layout": None}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is False

    def test_ia_declarou_disponivel_false_preserva_motivo(self):
        # Caso esperado do passo 8 do prompt: a IA decide nao arriscar
        # geometria e explica o porque -- isso deve ser preservado.
        dados = {
            "layout": {
                "disponivel": False,
                "motivo_indisponivel": "Comodos em formato L, retangulo nao representa bem",
                "comodos": [],
                "paredes": [],
                "aberturas": [],
            }
        }
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is False
        assert "formato L" in resultado["layout"]["motivo_indisponivel"]


class TestLayoutMalformado:
    def test_comodo_sem_largura_cai_em_fallback(self):
        layout = _layout_valido()
        del layout["comodos"][0]["largura"]
        dados = {"layout": layout}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is False
        assert resultado["layout"]["comodos"] == []

    def test_comodo_com_tipo_piso_invalido_cai_em_fallback(self):
        layout = _layout_valido()
        layout["comodos"][0]["tipo_piso"] = "molhadinho"
        dados = {"layout": layout}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is False

    def test_comodo_com_largura_zero_cai_em_fallback(self):
        layout = _layout_valido()
        layout["comodos"][0]["largura"] = 0
        dados = {"layout": layout}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is False

    def test_parede_sem_coordenada_cai_em_fallback(self):
        layout = _layout_valido()
        del layout["paredes"][0]["x2"]
        dados = {"layout": layout}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is False

    def test_abertura_com_parede_index_inexistente_cai_em_fallback(self):
        layout = _layout_valido()
        layout["aberturas"][0]["parede_index"] = 5  # so existe indice 0
        dados = {"layout": layout}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is False

    def test_abertura_com_posicao_fora_de_0_1_cai_em_fallback(self):
        layout = _layout_valido()
        layout["aberturas"][0]["posicao"] = 1.5
        dados = {"layout": layout}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is False

    def test_abertura_com_tipo_invalido_cai_em_fallback(self):
        layout = _layout_valido()
        layout["aberturas"][0]["tipo"] = "porta_secreta"
        dados = {"layout": layout}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is False

    def test_comodos_nao_e_lista_cai_em_fallback(self):
        layout = _layout_valido()
        layout["comodos"] = "nao é uma lista"
        dados = {"layout": layout}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is False

    def test_sem_comodos_ou_paredes_cai_em_fallback(self):
        layout = _layout_valido()
        layout["comodos"] = []
        dados = {"layout": layout}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is False


class TestLayoutValido:
    def test_layout_valido_e_preservado(self):
        dados = {"layout": _layout_valido()}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is True
        assert resultado["layout"]["comodos"] == [_comodo()]
        assert resultado["layout"]["paredes"] == [_parede()]
        assert resultado["layout"]["aberturas"][0]["tipo"] == "janela"

    def test_layout_valido_com_multiplos_comodos_e_paredes(self):
        layout = {
            "disponivel": True,
            "motivo_indisponivel": "",
            "comodos": [
                _comodo(nome="Sala", tipo_piso="seco"),
                _comodo(nome="Banheiro", tipo_piso="molhado", x=5.0),
            ],
            "paredes": [
                _parede(),
                _parede(x1=5.0, x2=5.0, y2=4.0),
            ],
            "aberturas": [
                {"tipo": "porta_interna", "parede_index": 1, "posicao": 0.0},
                {"tipo": "porta_externa", "parede_index": 0, "posicao": 1.0},
            ],
        }
        dados = {"layout": layout}
        resultado = _normalizar_layout(dados)
        assert resultado["layout"]["disponivel"] is True
        assert len(resultado["layout"]["comodos"]) == 2
        assert len(resultado["layout"]["paredes"]) == 2
