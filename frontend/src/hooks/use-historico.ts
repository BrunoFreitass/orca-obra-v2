import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiDelete, apiGet } from '@/lib/api-client'
import type { OrcamentoHistorico } from '@/lib/types'

const CHAVE_HISTORICO = ['historico'] as const

export function useHistorico() {
  return useQuery({
    queryKey: CHAVE_HISTORICO,
    queryFn: () => apiGet<OrcamentoHistorico[]>('/historico'),
  })
}

export function useExcluirOrcamento() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => apiDelete(`/historico/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: CHAVE_HISTORICO }),
  })
}
