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


class ErroExtracao(BaseModel):
    mensagem_amigavel: str
    detalhe_tecnico: str | None = None


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
    Quantidade: float
    Preco_Unit: float
    Total: float
    Fase: str


class OrcamentoCalcularRequest(BaseModel):
    area_piso_seco: float = 0
    area_piso_molhado: float = 0
    area_piso_externo: float = 0
    metros_parede: float = 0
    portas_internas: int = 0
    portas_externas: int = 0
    janelas: int = 0
    padrao: str
    estrutura: str


class OrcamentoGerarRequest(BaseModel):
    materiais: list[ItemOrcamento]
    mao_de_obra: list[ItemOrcamento]
    bdi_percentual: float
    nome_projeto: str
    padrao: str
    estrutura: str
    local_obra: str
    area_piso_seco: float = 0
    area_piso_molhado: float = 0
    area_piso_externo: float = 0
    metros_parede: float = 0
    portas_internas: int = 0
    portas_externas: int = 0
    janelas: int = 0


class OrcamentoGerarResponse(BaseModel):
    custo_direto: float
    preco_venda: float
    caminho_excel: str
    caminho_pdf: str
    historico_id: int
