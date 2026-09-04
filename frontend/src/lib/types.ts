/** Espelhos TypeScript de api/schemas.py -- mantidos em sincronia manual
 * por enquanto (sem geração automática de tipos ainda). */

export interface OrcamentoHistorico {
  id: number
  data_criacao: string
  nome_projeto: string
  estado_uf: string
  padrao: string
  tipo_cobertura: string
  area_piso: number
  area_piso_seco: number
  area_piso_molhado: number
  area_piso_externo: number
  metros_parede: number
  portas_internas: number
  portas_externas: number
  janelas: number
  custo_direto: number
  bdi_percentual: number
  preco_venda: number
  versao_coeficientes: string
}

export interface PerfilEmpresa {
  nome_empresa: string
  profissional_responsavel: string
  telefone: string
  email: string
  registro: string
  caminho_logo: string
}

export type PerfilEmpresaUpdate = Omit<PerfilEmpresa, 'caminho_logo'>

export interface MonitorStatus {
  nivel: 'ok' | 'alerta' | 'critico'
  emoji: string
  mensagem: string
  total: number
  limite: number
  uso_percentual: number
  sucessos: number
  falhas: number
  caches: number
}

export interface ItemPreco {
  chave: string
  categoria: string
  rotulo: string
  valor: number
  fonte: string
  data_ref: string
  customizado: boolean
}

export interface PrecosImportarResponse {
  atualizados: Record<string, number>
  avisos: string[]
}

export interface SinapiItemPreco {
  valor: number
  descricao: string
}

export interface SinapiImportarResponse {
  precos: Record<string, SinapiItemPreco>
  avisos: string[]
  mes_ref: string | null
}

export type Padrao = 'Econômico' | 'Médio' | 'Alto Padrão'
export type TipoCobertura = 'Telhado' | 'Laje'

// --- Fase 3: Extração e Revisão ------------------------------------------

export type NivelConfianca = 'alta' | 'media' | 'baixa'

export interface ConfiancaCampo {
  nivel: NivelConfianca
  motivo: string
}

export const CAMPOS_EXTRACAO = [
  'area_piso_seco',
  'area_piso_molhado',
  'area_piso_externo',
  'metros_parede',
  'portas_internas',
  'portas_externas',
  'janelas',
] as const

export type CampoExtracao = (typeof CAMPOS_EXTRACAO)[number]

export interface DadosRevisao {
  area_piso_seco: number
  area_piso_molhado: number
  area_piso_externo: number
  metros_parede: number
  portas_internas: number
  portas_externas: number
  janelas: number
}

// --- Geometria opcional (layout 3D) --------------------------------------
// Espelha core/vision.py::LAYOUT_VAZIO / PROMPT_EXTRACAO passo 8. Aditivo:
// nunca obrigatório em nenhum lugar do fluxo de revisão/orçamento -- se a
// IA não retornar geometria confiável, `disponivel` vem false e as 3
// listas vêm vazias (nunca ausentes).
export type TipoPiso = 'seco' | 'molhado' | 'externo'
export type TipoAbertura = 'porta_interna' | 'porta_externa' | 'janela'

export interface ComodoLayout {
  nome: string
  tipo_piso: TipoPiso
  x: number
  y: number
  largura: number
  comprimento: number
}

export interface ParedeLayout {
  x1: number
  y1: number
  x2: number
  y2: number
}

export interface AberturaLayout {
  tipo: TipoAbertura
  /** Índice na lista `paredes` deste mesmo layout. */
  parede_index: number
  /** 0.0 = extremidade (x1,y1) da parede referenciada, 1.0 = (x2,y2). */
  posicao: number
}

export interface LayoutGeometria {
  disponivel: boolean
  motivo_indisponivel: string
  comodos: ComodoLayout[]
  paredes: ParedeLayout[]
  aberturas: AberturaLayout[]
}

export interface DadosExtraidos extends DadosRevisao {
  confianca: Partial<Record<CampoExtracao, ConfiancaCampo>>
  /** Ausente em respostas antigas (cache anterior a essa mudança) --
   * tratar igual a `disponivel: false`. */
  layout?: LayoutGeometria
}

export interface ErroExtracaoDetalhe {
  mensagem_amigavel: string
  detalhe_tecnico: string | null
}

export interface IndiceConfianca {
  percentual: number
  nivel: NivelConfianca
  cor: string
  emoji: string
  mensagem: string
}

export interface RevisaoAvaliarResponse {
  area_piso_total: number
  indice_confianca: IndiceConfianca
  avisos_parede: string[]
  sugestao_parede: number | null
  avisos_gerais: string[]
}

// --- Fase 4: Orçamento ----------------------------------------------------

export interface ItemOrcamento {
  Tipo: string
  Material: string
  Quantidade: number
  Preco_Unit: number
  Total: number
  Fase: string
}

export interface OrcamentoCalcularRequest extends DadosRevisao {
  padrao: Padrao
  estrutura: TipoCobertura
}

export interface OrcamentoGerarRequest extends DadosRevisao {
  materiais: ItemOrcamento[]
  mao_de_obra: ItemOrcamento[]
  bdi_percentual: number
  nome_projeto: string
  padrao: Padrao
  estrutura: TipoCobertura
  local_obra: string
}

export interface OrcamentoGerarResponse {
  custo_direto: number
  preco_venda: number
  historico_id: number
}
