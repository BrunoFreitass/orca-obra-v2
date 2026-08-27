import { useMutation, useQueryClient } from '@tanstack/react-query'

import { apiPost, apiPostFormData } from '@/lib/api-client'
import type { ItemPreco, SinapiImportarResponse } from '@/lib/types'

export function useImportarSinapi() {
  return useMutation({
    mutationFn: ({ arquivos, mesReferencia }: { arquivos: File[]; mesReferencia: string }) => {
      const formData = new FormData()
      for (const arquivo of arquivos) formData.append('arquivos', arquivo)
      if (mesReferencia) formData.append('mes_referencia', mesReferencia)
      return apiPostFormData<SinapiImportarResponse>('/sinapi/importar', formData)
    },
  })
}

export function useAplicarSinapi() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ valores, mesRef }: { valores: Record<string, number>; mesRef: string }) =>
      apiPost<ItemPreco[]>('/sinapi/aplicar', { valores, mes_ref: mesRef }),
    onSuccess: (itens) => queryClient.setQueryData(['precos'], itens),
  })
}
