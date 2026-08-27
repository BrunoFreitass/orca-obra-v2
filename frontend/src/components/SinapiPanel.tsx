import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAplicarSinapi, useImportarSinapi } from '@/hooks/use-sinapi'
import type { SinapiImportarResponse } from '@/lib/types'

export function SinapiPanel() {
  const importar = useImportarSinapi()
  const aplicar = useAplicarSinapi()
  const [mesReferencia, setMesReferencia] = useState('')
  const [resultado, setResultado] = useState<SinapiImportarResponse | null>(null)

  const avisosSemCodigo = resultado?.avisos.filter((a) => a.includes('ainda sem código mapeado')) ?? []
  const avisosMes = resultado?.avisos.filter((a) => a.includes('mês de referência')) ?? []
  const avisosRelevantes =
    resultado?.avisos.filter((a) => !avisosSemCodigo.includes(a) && !avisosMes.includes(a)) ?? []
  const numPrecos = resultado ? Object.keys(resultado.precos).length : 0

  return (
    <div className="flex flex-col gap-2.5">
      <p className="text-[11px] text-muted-foreground">
        Baixe o ZIP do mês para RR no site da Caixa (Preços de Insumos e Composições → RR →
        versão Não Desonerado) e envie aqui o(s) arquivo(s) .xlsx extraído(s).
      </p>

      <Input
        type="file"
        accept=".xlsx"
        multiple
        className="h-8 text-xs"
        onChange={(e) => {
          const arquivos = Array.from(e.target.files ?? [])
          if (arquivos.length === 0) return
          importar.mutate({ arquivos, mesReferencia }, { onSuccess: setResultado })
        }}
      />

      <div className="flex flex-col gap-1.5">
        <label className="text-xs text-muted-foreground">
          Mês de referência (AAAA-MM) — só se não for detectado automaticamente
        </label>
        <Input
          className="h-8 text-xs"
          placeholder="Ex.: 2026-08"
          value={mesReferencia}
          onChange={(e) => setMesReferencia(e.target.value)}
        />
      </div>

      {avisosRelevantes.map((aviso, i) => (
        <p key={i} className="text-[11px] text-warning">
          ⚠ {aviso}
        </p>
      ))}
      {avisosSemCodigo.length > 0 && (
        <p className="text-[11px] text-muted-foreground">
          ℹ {avisosSemCodigo.length} item(ns) do motor de cálculo ainda sem código SINAPI
          mapeado — fora do escopo desta importação.
        </p>
      )}

      {resultado && numPrecos > 0 && resultado.mes_ref && (
        <>
          <p className="text-xs text-muted-foreground">
            {numPrecos} preço(s) prontos para atualizar (ref. {resultado.mes_ref}):
          </p>
          <div className="flex flex-col gap-0.5 font-mono text-[11px]">
            {Object.entries(resultado.precos).map(([chave, dado]) => (
              <div key={chave}>
                <span className="font-medium">{chave}</span>: R$ {dado.valor.toFixed(2)}
              </div>
            ))}
          </div>
          <Button
            size="sm"
            className="h-8 text-xs"
            disabled={aplicar.isPending}
            onClick={() => {
              if (!resultado.mes_ref) return
              const valores = Object.fromEntries(
                Object.entries(resultado.precos).map(([chave, dado]) => [chave, dado.valor]),
              )
              aplicar.mutate(
                { valores, mesRef: resultado.mes_ref },
                { onSuccess: () => setResultado(null) },
              )
            }}
          >
            {aplicar.isPending ? 'Aplicando…' : 'Aplicar preços do SINAPI'}
          </Button>
        </>
      )}
      {resultado && numPrecos > 0 && !resultado.mes_ref && (
        <p className="text-[11px] text-warning">
          Não consegui identificar o mês de referência pelo nome do arquivo — preencha o campo
          acima para gravar os preços.
        </p>
      )}
    </div>
  )
}
