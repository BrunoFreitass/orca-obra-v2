import { create } from 'zustand'

import type { Padrao, TipoCobertura } from '@/lib/types'

/** Dados do projeto -- igual ao Streamlit hoje, isso NÃO é persistido no
 * servidor (só sessão), é reinserido a cada visita. "cliente" existe no
 * form original mas nunca é usado em nenhum cálculo/documento -- mantido
 * aqui só por paridade visual, sem inventar uso novo pra ele. */
interface ProjetoState {
  nomeProjeto: string
  cliente: string
  padrao: Padrao
  estrutura: TipoCobertura
  confirmado: boolean
  setNomeProjeto: (valor: string) => void
  setCliente: (valor: string) => void
  setPadrao: (valor: Padrao) => void
  setEstrutura: (valor: TipoCobertura) => void
  confirmar: () => void
  reabrir: () => void
}

export const useProjetoStore = create<ProjetoState>()((set) => ({
  nomeProjeto: '',
  cliente: '',
  padrao: 'Econômico',
  estrutura: 'Telhado',
  confirmado: false,
  setNomeProjeto: (nomeProjeto) => set({ nomeProjeto }),
  setCliente: (cliente) => set({ cliente }),
  setPadrao: (padrao) => set({ padrao }),
  setEstrutura: (estrutura) => set({ estrutura }),
  confirmar: () => set({ confirmado: true }),
  reabrir: () => set({ confirmado: false }),
}))
