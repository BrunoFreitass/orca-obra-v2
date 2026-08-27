"""Materiais, mão de obra e geração de orçamento (calculator.py,
orcamento_service.py) -- rotas adicionadas na Fase 4."""
from fastapi import APIRouter, HTTPException

from api.schemas import (
    ItemOrcamento,
    OrcamentoCalcularRequest,
    OrcamentoGerarRequest,
    OrcamentoGerarResponse,
)
from core.calculator import calcular_mao_de_obra, calcular_materiais
from core.models import DadosExtracao
from core.orcamento_service import gerar_orcamento_completo, montar_orcamento_completo

router = APIRouter(prefix="/api/orcamento", tags=["orcamento"])


def _dados_extracao(corpo) -> DadosExtracao:
    return DadosExtracao(
        area_piso_seco=corpo.area_piso_seco,
        area_piso_molhado=corpo.area_piso_molhado,
        area_piso_externo=corpo.area_piso_externo,
        metros_parede=corpo.metros_parede,
        portas_internas=corpo.portas_internas,
        portas_externas=corpo.portas_externas,
        janelas=corpo.janelas,
    )


@router.post("/materiais", response_model=list[ItemOrcamento])
def materiais(corpo: OrcamentoCalcularRequest) -> list[dict]:
    return calcular_materiais(_dados_extracao(corpo), corpo.padrao, corpo.estrutura)


@router.post("/mao-de-obra", response_model=list[ItemOrcamento])
def mao_de_obra(corpo: OrcamentoCalcularRequest) -> list[dict]:
    return calcular_mao_de_obra(_dados_extracao(corpo), corpo.estrutura)


@router.post("/gerar", response_model=OrcamentoGerarResponse)
def gerar(corpo: OrcamentoGerarRequest) -> dict:
    if not corpo.nome_projeto.strip():
        raise HTTPException(
            status_code=400,
            detail="Informe o nome do projeto/cliente antes de gerar o orçamento.",
        )

    orcamento_final = montar_orcamento_completo(
        [item.model_dump() for item in corpo.materiais],
        [item.model_dump() for item in corpo.mao_de_obra],
    )
    dados = _dados_extracao(corpo)

    return gerar_orcamento_completo(
        orcamento_final, corpo.bdi_percentual, corpo.nome_projeto, corpo.padrao,
        corpo.estrutura, dados.area_piso_total, corpo.metros_parede,
        corpo.portas_internas, corpo.portas_externas, corpo.janelas,
        corpo.area_piso_seco, corpo.area_piso_molhado, corpo.area_piso_externo,
        corpo.local_obra,
    )
