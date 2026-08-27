import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import type { ReactNode } from 'react'

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'

interface Props {
  titulo: string
  children: ReactNode
  abertoPorPadrao?: boolean
}

/** Painel técnico recolhível -- equivalente ao st.expander do Streamlit,
 * mas sem a "cara de card" (sem borda arredondada/sombra, só um
 * cabeçalho denso com seta). Usado nos painéis da sidebar. */
export function PainelColapsavel({ titulo, children, abertoPorPadrao = false }: Props) {
  const [aberto, setAberto] = useState(abertoPorPadrao)

  return (
    <Collapsible open={aberto} onOpenChange={setAberto}>
      <CollapsibleTrigger className="flex w-full items-center gap-1.5 py-1.5 text-left font-mono text-[11px] uppercase tracking-wider text-muted-foreground hover:text-foreground">
        <ChevronRight className={`size-3 shrink-0 transition-transform ${aberto ? 'rotate-90' : ''}`} />
        {titulo}
      </CollapsibleTrigger>
      <CollapsibleContent className="flex flex-col gap-2 pt-1 pb-2 pl-4.5">
        {children}
      </CollapsibleContent>
    </Collapsible>
  )
}
