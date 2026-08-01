"""Modelos de dominio do OrcaObra AI.

Antes desta refatoracao, os dados extraidos da planta (area_piso_seco,
metros_parede, portas etc.) viajavam como dict solto entre vision.py,
app.py e calculator.py -- e cada funcao que precisava da area total ou
da area de parede repetia as mesmas 4-5 linhas de "dados.get(...)".
Este modulo centraliza essas regras num unico lugar.
"""

from dataclasses import dataclass, field
from typing import Dict, List

# Pe direito padrao (m) usado para converter metros lineares de parede
# em area vertical de parede. Antes esse "2.8" estava duplicado dentro
# de calcular_materiais() E calcular_mao_de_obra() em calculator.py.
ALTURA_PAREDE_PADRAO = 2.8


@dataclass
class DadosExtracao:
    """Os 7 campos agregados extraidos de uma planta baixa (pela IA, em
    core/vision.py, ou editados manualmente na tela), mais o bloco de
    confianca por campo.
    """

    area_piso_seco: float = 0.0
    area_piso_molhado: float = 0.0
    area_piso_externo: float = 0.0
    metros_parede: float = 0.0
    portas_internas: int = 0
    portas_externas: int = 0
    janelas: int = 0
    confianca: Dict = field(default_factory=dict)

    @property
    def area_piso_total(self) -> float:
        return self.area_piso_seco + self.area_piso_molhado + self.area_piso_externo

    @property
    def portas_total(self) -> int:
        return self.portas_internas + self.portas_externas

    @property
    def area_parede(self) -> float:
        """Area vertical de parede (m2), assumindo o pe direito padrao."""
        return self.metros_parede * ALTURA_PAREDE_PADRAO

    def area_cobertura(self, tipo_cobertura: str) -> float:
        """Area de cobertura (m2). Telhado tem fator 1.15 sobre a area de
        piso pra cobrir o beiral/inclinacao; laje usa a area de piso direto."""
        fator = 1.15 if tipo_cobertura == "Telhado" else 1.0
        return round(self.area_piso_total * fator, 2)

    @classmethod
    def from_dict(cls, dados: dict) -> "DadosExtracao":
        """Converte o dict cru (vindo do Gemini em core/vision.py, do
        modo mock, ou dos campos editados na tela) para o modelo de
        dominio. Aceita chaves faltando (usa 0 como default), do mesmo
        jeito que o codigo anterior fazia com dados.get(...)."""
        return cls(
            area_piso_seco=float(dados.get("area_piso_seco", 0) or 0),
            area_piso_molhado=float(dados.get("area_piso_molhado", 0) or 0),
            area_piso_externo=float(dados.get("area_piso_externo", 0) or 0),
            metros_parede=float(dados.get("metros_parede", 0) or 0),
            portas_internas=int(dados.get("portas_internas", 0) or 0),
            portas_externas=int(dados.get("portas_externas", 0) or 0),
            janelas=int(dados.get("janelas", 0) or 0),
            confianca=dados.get("confianca", {}),
        )


@dataclass
class ItemOrcamento:
    """Uma linha do orcamento (material ou mao de obra)."""

    tipo: str
    material: str
    quantidade: float
    preco_unit: float

    @property
    def total(self) -> float:
        return round(self.quantidade * self.preco_unit, 2)

    def to_dict(self) -> dict:
        """Formato dict (Tipo/Material/Quantidade/Preco_Unit/Total) que
        core/reporter.py e core/proposta_pdf.py ja esperam receber --
        mantem compatibilidade sem precisar reescrever esses dois
        modulos agora."""
        return {
            "Tipo": self.tipo,
            "Material": self.material,
            "Quantidade": self.quantidade,
            "Preco_Unit": self.preco_unit,
            "Total": self.total,
        }


def itens_para_dicts(itens: List[ItemOrcamento]) -> List[dict]:
    return [item.to_dict() for item in itens]
