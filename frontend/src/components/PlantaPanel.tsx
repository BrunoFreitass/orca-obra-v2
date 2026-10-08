import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { extrairDetalheErro, useAnalisarPlanta } from '@/hooks/use-extracao'
import { useExtracaoStore } from '@/lib/extracao-store'

export function PlantaPanel() {
  const navigate = useNavigate()
  const analisar = useAnalisarPlanta()
  const setDadosOriginais = useExtracaoStore((s) => s.setDadosOriginais)
  const [arquivo, setArquivo] = useState<File | null>(null)

  return (
    <div className="flex flex-col gap-2">
      <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
        Planta Baixa
      </p>
      <p className="text-[11px] text-muted-foreground">
        PDF, JPG ou PNG. Plantas com Quadro de Áreas dão resultados mais precisos.
      </p>

      <Input
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        className="h-8 text-xs"
        onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
      />

      {arquivo && (
        <Button
          size="sm"
          className="h-8 text-xs"
          disabled={analisar.isPending}
          onClick={() =>
            analisar.mutate(arquivo, {
              onSuccess: (dados) => {
                setDadosOriginais(dados)
                navigate('/revisao')
              },
            })
          }
        >
          {analisar.isPending ? 'Analisando…' : 'Analisar Planta com IA'}
        </Button>
      )}

      {analisar.isError && (
        <p className="text-[11px] text-destructive">
          {extrairDetalheErro(analisar.error).mensagem_amigavel}
        </p>
      )}
    </div>
  )
}
