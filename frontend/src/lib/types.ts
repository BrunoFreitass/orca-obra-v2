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
