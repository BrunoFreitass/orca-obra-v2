"""Espelhos pydantic dos modelos de core/models.py e respostas da API."""
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


# --- Fase 1: Histórico -------------------------------------------------

class OrcamentoHistorico(BaseModel):
    id: int
    data_criacao: str
    nome_projeto: str
    cliente: str = ""
    estado_uf: str
    padrao: str
    tipo_cobertura: str
    area_piso: float
    area_piso_seco: float
    area_piso_molhado: float
    area_piso_externo: float
    metros_parede: float
    portas_internas: int
    portas_externas: int
    janelas: int
    custo_direto: float
    bdi_percentual: float
    preco_venda: float
    versao_coeficientes: str


# --- Fase 1: Perfil da empresa ------------------------------------------

class PerfilEmpresa(BaseModel):
    nome_empresa: str
    profissional_responsavel: str
    telefone: str
    email: str
    registro: str
    caminho_logo: str


class PerfilEmpresaUpdate(BaseModel):
    nome_empresa: str
    profissional_responsavel: str
    telefone: str
    email: str
    registro: str


# --- Fase 1: Monitor de cota --------------------------------------------

class MonitorStatus(BaseModel):
    nivel: str
    emoji: str
    mensagem: str
    total: int
    limite: int
    uso_percentual: float
    sucessos: int
    falhas: int
    caches: int


# --- Fase 2: Preços customizados ----------------------------------------

class ItemPreco(BaseModel):
    chave: str
    categoria: str
    rotulo: str
    valor: float
    fonte: str
    data_ref: str
    customizado: bool


class PrecosImportarResponse(BaseModel):
    atualizados: dict[str, float]
    avisos: list[str]


class PrecosAplicarRequest(BaseModel):
    valores: dict[str, float]


# --- Fase 2: Importação SINAPI -------------------------------------------

class SinapiItemPreco(BaseModel):
    valor: float
    descricao: str


class SinapiImportarResponse(BaseModel):
    precos: dict[str, SinapiItemPreco]
    avisos: list[str]
    mes_ref: str | None


class SinapiAplicarRequest(BaseModel):
    valores: dict[str, float]
    mes_ref: str


# --- Fase 3: Extração e Revisão ------------------------------------------

class ConfiancaCampo(BaseModel):
    nivel: str = "media"
    motivo: str = ""


class DadosExtraidos(BaseModel):
    area_piso_seco: float = 0
    area_piso_molhado: float = 0
    area_piso_externo: float = 0
    metros_parede: float = 0
    portas_internas: int = 0
    portas_externas: int = 0
    janelas: int = 0
    confianca: dict[str, ConfiancaCampo] = {}


class IndiceConfianca(BaseModel):
    percentual: int
    nivel: str
    cor: str
    emoji: str
    mensagem: str


class RevisaoAvaliarRequest(BaseModel):
    confianca: dict[str, ConfiancaCampo] = {}
    area_piso_seco: float = 0
    area_piso_molhado: float = 0
    area_piso_externo: float = 0
    metros_parede: float = 0
    portas_internas: int = 0
    portas_externas: int = 0
    janelas: int = 0


class RevisaoAvaliarResponse(BaseModel):
    area_piso_total: float
    indice_confianca: IndiceConfianca
    avisos_parede: list[str]
    sugestao_parede: float | None
    avisos_gerais: list[str]


# --- Fase 4: Orçamento (materiais, mão de obra, geração) ------------------

class ItemOrcamento(BaseModel):
    """Espelha o dict que core/calculator.py e core/models.py::ItemOrcamento.to_dict()
    já produzem -- chaves capitalizadas de propósito, pra core/reporter.py e
    core/proposta_pdf.py aceitarem esses itens sem nenhuma conversão."""

    Tipo: str
    Material: str
    Quantidade: float = Field(ge=0)
    Preco_Unit: float = Field(ge=0)
    # Recalculado no servidor em /api/orcamento/gerar -- o valor enviado
    # pelo cliente é ignorado.
    Total: float
    Fase: str


# Valores aceitos por core/coeficientes.py e core/calculator.py -- qualquer
# outro dava KeyError (500) no cálculo.
Padrao = Literal["Econômico", "Médio", "Alto Padrão"]
Estrutura = Literal["Telhado", "Laje"]


class OrcamentoCalcularRequest(BaseModel):
    area_piso_seco: float = Field(default=0, ge=0)
    area_piso_molhado: float = Field(default=0, ge=0)
    area_piso_externo: float = Field(default=0, ge=0)
    metros_parede: float = Field(default=0, ge=0)
    portas_internas: int = Field(default=0, ge=0)
    portas_externas: int = Field(default=0, ge=0)
    janelas: int = Field(default=0, ge=0)
    padrao: Padrao
    estrutura: Estrutura


class OrcamentoGerarRequest(BaseModel):
    materiais: list[ItemOrcamento]
    mao_de_obra: list[ItemOrcamento]
    bdi_percentual: float = Field(ge=0, le=100)
    nome_projeto: str = Field(max_length=200)
    cliente: str = Field(default="", max_length=200)
    padrao: Padrao
    estrutura: Estrutura
    local_obra: str
    area_piso_seco: float = Field(default=0, ge=0)
    area_piso_molhado: float = Field(default=0, ge=0)
    area_piso_externo: float = Field(default=0, ge=0)
    metros_parede: float = Field(default=0, ge=0)
    portas_internas: int = Field(default=0, ge=0)
    portas_externas: int = Field(default=0, ge=0)
    janelas: int = Field(default=0, ge=0)


class OrcamentoGerarResponse(BaseModel):
    custo_direto: float
    preco_venda: float
    historico_id: int
