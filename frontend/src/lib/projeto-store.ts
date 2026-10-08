import { create } from 'zustand'

import type { Padrao, TipoCobertura } from '@/lib/types'

/** Dados do projeto -- NÃO são persistidos no servidor (só sessão), são
 * reinseridos a cada visita. "cliente" não entra em nenhum cálculo, mas
 * vai pro PDF da proposta e pro histórico. */
interface ProjetoState {
  nomeProjeto: string
  cliente: string
  padrao: Padrao
  estrutura: TipoCobertura
  setNomeProjeto: (valor: string) => void
  setCliente: (valor: string) => void
  setPadrao: (valor: Padrao) => void
  setEstrutura: (valor: TipoCobertura) => void
}

export const useProjetoStore = create<ProjetoState>()((set) => ({
  nomeProjeto: '',
  cliente: '',
  padrao: 'Econômico',
  estrutura: 'Telhado',
  setNomeProjeto: (nomeProjeto) => set({ nomeProjeto }),
  setCliente: (cliente) => set({ cliente }),
  setPadrao: (padrao) => set({ padrao }),
  setEstrutura: (estrutura) => set({ estrutura }),
}))
