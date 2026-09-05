import { useMutation } from '@tanstack/react-query'

import { ApiError, apiPostFormData } from '@/lib/api-client'
import type { DadosExtraidos, ErroExtracaoDetalhe, LayoutGeometria } from '@/lib/types'

export function useAnalisarPlanta() {
  return useMutation({
    mutationFn: (arquivo: File) => {
      const formData = new FormData()
      formData.append('planta', arquivo)
      return apiPostFormData<DadosExtraidos>('/extracao', formData)
    },
  })
}

/** Fallback opcional acionado pelo usuário na tela de Revisão quando a
 * extração oficial não conseguiu montar a geometria 3D -- gera uma
 * aproximação ilustrativa (ver core.vision.gerar_layout_ilustrativo),
 * sem a válvula de segurança da extração oficial. Nunca afeta os campos
 * do orçamento. */
export function useGerarLayoutIlustrativo() {
  return useMutation({
    mutationFn: (arquivo: File) => {
      const formData = new FormData()
      formData.append('planta', arquivo)
      return apiPostFormData<LayoutGeometria>('/extracao/layout-ilustrativo', formData)
    },
  })
}

/** api/routers/extracao.py manda um detail estruturado
 * (ErroExtracaoDetalhe) pros erros 422 -- extrai isso de volta, com
 * fallback genérico pra qualquer outro tipo de falha (rede, 500, etc). */
export function extrairDetalheErro(erro: unknown): ErroExtracaoDetalhe {
  if (erro instanceof ApiError) {
    const detail = erro.detail
    if (detail && typeof detail === 'object' && 'mensagem_amigavel' in detail) {
      return detail as ErroExtracaoDetalhe
    }
    return { mensagem_amigavel: String(detail), detalhe_tecnico: null }
  }
  return { mensagem_amigavel: 'Erro inesperado na análise.', detalhe_tecnico: String(erro) }
}
