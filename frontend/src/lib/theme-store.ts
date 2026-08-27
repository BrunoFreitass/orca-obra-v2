import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Tema = 'claro' | 'escuro'

interface ThemeState {
  tema: Tema
  alternarTema: () => void
}

function aplicarClasseNoHtml(tema: Tema) {
  document.documentElement.classList.toggle('dark', tema === 'escuro')
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      tema: 'claro',
      alternarTema: () => {
        const novoTema: Tema = get().tema === 'claro' ? 'escuro' : 'claro'
        aplicarClasseNoHtml(novoTema)
        set({ tema: novoTema })
      },
    }),
    {
      name: 'orcaobra-tema',
      onRehydrateStorage: () => (state) => {
        if (state) aplicarClasseNoHtml(state.tema)
      },
    },
  ),
)
