"""Confiança da extração e validação de metragem de parede
(core/confianca.py, core/validacao.py) -- avalia tudo de uma vez pra
evitar 3 idas-e-voltas separadas a cada edição de campo na tela."""
from fastapi import APIRouter

from api.schemas import RevisaoAvaliarRequest, RevisaoAvaliarResponse
from core.confianca import calcular_indice_confianca, validar_proporcao_parede
from core.models import DadosExtracao
from core.validacao import validar_dados

router = APIRouter(prefix="/api/revisao", tags=["revisao"])


@router.post("/avaliar", response_model=RevisaoAvaliarResponse)
def avaliar(corpo: RevisaoAvaliarRequest) -> dict:
    dados = DadosExtracao(
        area_piso_seco=corpo.area_piso_seco,
        area_piso_molhado=corpo.area_piso_molhado,
        area_piso_externo=corpo.area_piso_externo,
        metros_parede=corpo.metros_parede,
        portas_internas=corpo.portas_internas,
        portas_externas=corpo.portas_externas,
        janelas=corpo.janelas,
    )
    confianca_bruta = {campo: valor.model_dump() for campo, valor in corpo.confianca.items()}

    avisos_parede, sugestao_parede = validar_proporcao_parede(
        dados.area_piso_total, corpo.metros_parede, corpo.portas_internas
    )
    avisos_gerais = validar_dados({
        "area_piso": dados.area_piso_total,
        "metros_parede": corpo.metros_parede,
        "portas": dados.portas_total,
        "janelas": corpo.janelas,
    })

    return {
        "area_piso_total": dados.area_piso_total,
        "indice_confianca": calcular_indice_confianca(confianca_bruta),
        "avisos_parede": avisos_parede,
        "sugestao_parede": sugestao_parede,
        "avisos_gerais": avisos_gerais,
    }
