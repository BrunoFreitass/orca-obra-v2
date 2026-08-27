import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiGet, apiPost, apiPostFormData } from '@/lib/api-client'
import type { ItemPreco, PrecosImportarResponse } from '@/lib/types'

const CHAVE_PRECOS = ['precos'] as const

export function usePrecos() {
  return useQuery({
    queryKey: CHAVE_PRECOS,
    queryFn: () => apiGet<ItemPreco[]>('/precos'),
  })
}

export function useImportarPlanilhaPrecos() {
  return useMutation({
    mutationFn: (arquivo: File) => {
      const formData = new FormData()
      formData.append('arquivo', arquivo)
      return apiPostFormData<PrecosImportarResponse>('/precos/importar', formData)
    },
  })
}

export function useAplicarPrecos() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (valores: Record<string, number>) =>
      apiPost<ItemPreco[]>('/precos/aplicar', { valores }),
    onSuccess: (itens) => queryClient.setQueryData(CHAVE_PRECOS, itens),
  })
}

export function useRestaurarPrecos() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => apiPost<ItemPreco[]>('/precos/restaurar', {}),
    onSuccess: (itens) => queryClient.setQueryData(CHAVE_PRECOS, itens),
  })
}
