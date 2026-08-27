"""Espelhos pydantic dos modelos de core/models.py e respostas da API.
Preenchido conforme cada fase liga suas rotas -- ver
C:\\Users\\bruno\\.claude\\plans\\immutable-rolling-volcano.md."""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


# --- Fase 1: Histórico -------------------------------------------------

class OrcamentoHistorico(BaseModel):
    id: int
    data_criacao: str
    nome_projeto: str
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
    caminho_excel: str
    caminho_pdf: str | None = None


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
