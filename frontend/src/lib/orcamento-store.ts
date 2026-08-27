import { create } from 'zustand'

import type { ItemOrcamento } from '@/lib/types'

function recalcularTotal(item: ItemOrcamento, precoUnit: number): ItemOrcamento {
  return { ...item, Preco_Unit: precoUnit, Total: Math.round(item.Quantidade * precoUnit * 100) / 100 }
}

interface OrcamentoState {
  /** Serializa os inputs que definem os itens sugeridos (padrão, estrutura,
   * áreas, parede, aberturas) -- equivalente à "assinatura" que o Streamlit
   * usa hoje (core/ui_revisao.py) pra saber quando precisa re-sugerir
   * materiais/mão de obra e descartar as edições de preço anteriores. */
  assinatura: string | null
  materiais: ItemOrcamento[]
  maoDeObra: ItemOrcamento[]
  bdi: number
  carregarSugeridos: (assinatura: string, materiais: ItemOrcamento[], maoDeObra: ItemOrcamento[]) => void
  setPrecoMaterial: (index: number, precoUnit: number) => void
  setPrecoMaoDeObra: (index: number, precoUnit: number) => void
  setBdi: (bdi: number) => void
}

export const useOrcamentoStore = create<OrcamentoState>()((set) => ({
  assinatura: null,
  materiais: [],
  maoDeObra: [],
  bdi: 25,
  carregarSugeridos: (assinatura, materiais, maoDeObra) =>
    set((state) => (state.assinatura === assinatura ? {} : { assinatura, materiais, maoDeObra })),
  setPrecoMaterial: (index, precoUnit) =>
    set((state) => ({
      materiais: state.materiais.map((item, i) => (i === index ? recalcularTotal(item, precoUnit) : item)),
    })),
  setPrecoMaoDeObra: (index, precoUnit) =>
    set((state) => ({
      maoDeObra: state.maoDeObra.map((item, i) => (i === index ? recalcularTotal(item, precoUnit) : item)),
    })),
  setBdi: (bdi) => set({ bdi }),
}))
