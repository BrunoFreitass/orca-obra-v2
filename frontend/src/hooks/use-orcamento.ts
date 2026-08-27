import { useMutation, useQuery } from '@tanstack/react-query'

import { apiPost } from '@/lib/api-client'
import type {
  ItemOrcamento,
  OrcamentoCalcularRequest,
  OrcamentoGerarRequest,
  OrcamentoGerarResponse,
} from '@/lib/types'

/** A queryKey incluir todo o corpo (padrão, estrutura, áreas, parede,
 * aberturas) dispara o recálculo automaticamente quando qualquer um
 * desses inputs muda -- mesmo mecanismo já usado em use-revisao.ts. */
export function useMateriais(corpo: OrcamentoCalcularRequest | null) {
  return useQuery({
    queryKey: ['orcamento', 'materiais', corpo],
    queryFn: () => apiPost<ItemOrcamento[]>('/orcamento/materiais', corpo),
    enabled: corpo !== null,
  })
}

export function useMaoDeObra(corpo: OrcamentoCalcularRequest | null) {
  return useQuery({
    queryKey: ['orcamento', 'mao-de-obra', corpo],
    queryFn: () => apiPost<ItemOrcamento[]>('/orcamento/mao-de-obra', corpo),
    enabled: corpo !== null,
  })
}

export function useGerarOrcamento() {
  return useMutation({
    mutationFn: (corpo: OrcamentoGerarRequest) => apiPost<OrcamentoGerarResponse>('/orcamento/gerar', corpo),
  })
}
