import { create } from 'zustand'

import type { DadosExtraidos, DadosRevisao, LayoutGeometria } from '@/lib/types'

interface ExtracaoState {
  /** Resultado bruto da extração (inclui confiança) -- não muda depois
   * de extraído, só serve de referência pros badges por campo. */
  dadosOriginais: DadosExtraidos | null
  /** Valores editáveis pelo usuário na tela de revisão. */
  valores: DadosRevisao
  confirmado: boolean
  /** Arquivo original da planta -- guardado pra permitir reenviar pro
   * endpoint de visualização 3D ilustrativa (POST /extracao/layout-ilustrativo)
   * sem pedir upload de novo. */
  arquivo: File | null
  /** true quando dadosOriginais.layout veio do fallback ilustrativo
   * (gerar_layout_ilustrativo), não da extração oficial -- controla o
   * aviso de "aproximado/não verificado" no frontend. */
  layoutEhIlustrativo: boolean
  setDadosOriginais: (dados: DadosExtraidos) => void
  setArquivo: (arquivo: File | null) => void
  setLayoutIlustrativo: (layout: LayoutGeometria) => void
  setCampo: (campo: keyof DadosRevisao, valor: number) => void
  confirmar: () => void
  reabrir: () => void
  limpar: () => void
}

const VALORES_VAZIOS: DadosRevisao = {
  area_piso_seco: 0,
  area_piso_molhado: 0,
  area_piso_externo: 0,
  metros_parede: 0,
  portas_internas: 0,
  portas_externas: 0,
  janelas: 0,
}

export const useExtracaoStore = create<ExtracaoState>()((set) => ({
  dadosOriginais: null,
  valores: VALORES_VAZIOS,
  confirmado: false,
  arquivo: null,
  layoutEhIlustrativo: false,
  setDadosOriginais: (dados) =>
    set({
      dadosOriginais: dados,
      valores: {
        area_piso_seco: dados.area_piso_seco,
        area_piso_molhado: dados.area_piso_molhado,
        area_piso_externo: dados.area_piso_externo,
        metros_parede: dados.metros_parede,
        portas_internas: dados.portas_internas,
        portas_externas: dados.portas_externas,
        janelas: dados.janelas,
      },
      confirmado: false,
      layoutEhIlustrativo: false,
    }),
  setArquivo: (arquivo) => set({ arquivo }),
  setLayoutIlustrativo: (layout) =>
    set((state) => ({
      dadosOriginais: state.dadosOriginais ? { ...state.dadosOriginais, layout } : state.dadosOriginais,
      layoutEhIlustrativo: true,
    })),
  setCampo: (campo, valor) =>
    set((state) => ({ valores: { ...state.valores, [campo]: valor }, confirmado: false })),
  confirmar: () => set({ confirmado: true }),
  reabrir: () => set({ confirmado: false }),
  limpar: () =>
    set({ dadosOriginais: null, valores: VALORES_VAZIOS, confirmado: false, arquivo: null, layoutEhIlustrativo: false }),
}))
