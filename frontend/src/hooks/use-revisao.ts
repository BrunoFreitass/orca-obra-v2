import { useQuery } from '@tanstack/react-query'

import { apiPost } from '@/lib/api-client'
import type { DadosExtraidos, RevisaoAvaliarResponse } from '@/lib/types'

/** Recalcula índice de confiança + avisos de parede/gerais toda vez que
 * um dos valores muda -- a queryKey incluir os valores é o que dispara
 * o recálculo automaticamente (equivalente à "assinatura" que o
 * Streamlit usa hoje pra saber quando os dados mudaram). */
export function useAvaliarRevisao(dados: DadosExtraidos | null) {
  return useQuery({
    queryKey: ['revisao', 'avaliar', dados],
    queryFn: () => apiPost<RevisaoAvaliarResponse>('/revisao/avaliar', dados),
    enabled: dados !== null,
  })
}
