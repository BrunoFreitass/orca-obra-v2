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
  caminho_excel: string
  caminho_pdf: string | null
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

export interface DadosExtraidos extends DadosRevisao {
  confianca: Partial<Record<CampoExtracao, ConfiancaCampo>>
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
