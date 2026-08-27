import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  useAplicarPrecos,
  useImportarPlanilhaPrecos,
  usePrecos,
  useRestaurarPrecos,
} from '@/hooks/use-precos'
import { urlDownload } from '@/lib/api-client'
import type { PrecosImportarResponse } from '@/lib/types'

export function PrecosPanel() {
  const { data: precos } = usePrecos()
  const importar = useImportarPlanilhaPrecos()
  const aplicar = useAplicarPrecos()
  const restaurar = useRestaurarPrecos()
  const [preview, setPreview] = useState<PrecosImportarResponse | null>(null)

  const overridesAtivos = precos?.filter((p) => p.customizado).length ?? 0
  const numAtualizados = preview ? Object.keys(preview.atualizados).length : 0

  return (
    <div className="flex flex-col gap-2.5">
      <Button variant="outline" size="sm" className="h-8 text-xs" asChild>
        <a href={urlDownload('/precos/modelo')}>Baixar modelo Excel</a>
      </Button>

      <Input
        type="file"
        accept=".xlsx"
        className="h-8 text-xs"
        onChange={(e) => {
          const arquivo = e.target.files?.[0]
          if (!arquivo) return
          importar.mutate(arquivo, { onSuccess: setPreview })
        }}
      />

      {preview?.avisos.map((aviso, i) => (
        <p key={i} className="text-[11px] text-warning">
          ⚠ {aviso}
        </p>
      ))}

      {numAtualizados > 0 && (
        <>
          <p className="text-xs text-muted-foreground">{numAtualizados} preço(s) alterado(s).</p>
          <Button
            size="sm"
            className="h-8 text-xs"
            disabled={aplicar.isPending}
            onClick={() =>
              preview && aplicar.mutate(preview.atualizados, { onSuccess: () => setPreview(null) })
            }
          >
            {aplicar.isPending ? 'Aplicando…' : 'Aplicar preços'}
          </Button>
        </>
      )}
      {preview && numAtualizados === 0 && preview.avisos.length === 0 && (
        <p className="text-xs text-muted-foreground">Nenhuma mudança detectada.</p>
      )}

      {overridesAtivos > 0 && (
        <>
          <p className="text-[11px] text-muted-foreground">
            {overridesAtivos} preço(s) customizado(s)
          </p>
          <Button
            variant="outline"
            size="sm"
            className="h-8 text-xs"
            disabled={restaurar.isPending}
            onClick={() => restaurar.mutate()}
          >
            Restaurar padrão
          </Button>
        </>
      )}
    </div>
  )
}
