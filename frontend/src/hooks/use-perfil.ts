import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiGet, apiPostFormData, apiPut } from '@/lib/api-client'
import type { PerfilEmpresa, PerfilEmpresaUpdate } from '@/lib/types'

const CHAVE_PERFIL = ['perfil'] as const

export function usePerfil() {
  return useQuery({
    queryKey: CHAVE_PERFIL,
    queryFn: () => apiGet<PerfilEmpresa>('/perfil'),
  })
}

export function useSalvarPerfil() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (dados: PerfilEmpresaUpdate) => apiPut<PerfilEmpresa>('/perfil', dados),
    onSuccess: (perfil) => queryClient.setQueryData(CHAVE_PERFIL, perfil),
  })
}

export function useEnviarLogo() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (arquivo: File) => {
      const formData = new FormData()
      formData.append('logo', arquivo)
      return apiPostFormData<PerfilEmpresa>('/perfil/logo', formData)
    },
    onSuccess: (perfil) => queryClient.setQueryData(CHAVE_PERFIL, perfil),
  })
}
