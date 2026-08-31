import { Building2, ChevronDown, ChevronRight, Download, FileText, Trash2 } from 'lucide-react'
import { Fragment, useState } from 'react'

import { ConfirmarExclusaoDialog } from '@/components/ConfirmarExclusaoDialog'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useExcluirOrcamento, useHistorico } from '@/hooks/use-historico'
import { urlDownload } from '@/lib/api-client'
import { useExtracaoStore } from '@/lib/extracao-store'
import type { OrcamentoHistorico } from '@/lib/types'

function formatarMoeda(valor: number): string {
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function LinhaQuantitativos({ registro }: { registro: OrcamentoHistorico }) {
  const itens: [string, string][] = [
    ['Área Seca', `${registro.area_piso_seco.toFixed(1)} m²`],
    ['Área Molhada', `${registro.area_piso_molhado.toFixed(1)} m²`],
    ['Área Externa', `${registro.area_piso_externo.toFixed(1)} m²`],
    ['Paredes', `${registro.metros_parede.toFixed(0)} m`],
    ['Portas Int.', `${registro.portas_internas} un`],
    ['Portas Ext.', `${registro.portas_externas} un`],
    ['Janelas', `${registro.janelas} un`],
    ['BDI', `${registro.bdi_percentual.toFixed(0)}%`],
  ]
  return (
    <TableRow className="bg-muted/40 hover:bg-muted/40">
      <TableCell colSpan={7} className="p-0">
        <div className="grid grid-cols-4 gap-x-6 gap-y-2 px-6 py-3 font-mono text-xs sm:grid-cols-8">
          {itens.map(([rotulo, valor]) => (
            <div key={rotulo}>
              <div className="text-muted-foreground">{rotulo}</div>
              <div className="font-medium text-foreground">{valor}</div>
            </div>
          ))}
        </div>
      </TableCell>
    </TableRow>
  )
}

export function Landing() {
  const { data: orcamentos, isLoading, isError } = useHistorico()
  const excluir = useExcluirOrcamento()
  const dadosOriginais = useExtracaoStore((s) => s.dadosOriginais)
  const [expandidoId, setExpandidoId] = useState<number | null>(null)
  const [paraExcluir, setParaExcluir] = useState<OrcamentoHistorico | null>(null)

  return (
    <div className="flex flex-col gap-3">
      {!dadosOriginais && (
        <div className="flex flex-col items-start gap-2 border border-border bg-card p-6">
          <div className="flex items-center gap-2 text-primary">
            <Building2 className="size-5" />
            <span className="font-mono text-sm uppercase tracking-widest">OrçaObra AI</span>
          </div>
          <p className="text-base font-medium">
            Transforme plantas baixas em orçamentos detalhados em segundos.
          </p>
          <p className="text-sm text-muted-foreground">
            Configure sua empresa e o projeto na barra lateral, depois envie a planta baixa em
            "Planta Baixa" para começar.
          </p>
        </div>
      )}

      <h1 className="font-mono text-sm uppercase tracking-wider text-muted-foreground">
        Histórico de Orçamentos
      </h1>

      {isLoading && <p className="text-sm text-muted-foreground">Carregando…</p>}
      {isError && (
        <p className="text-sm text-destructive">
          Não foi possível carregar o histórico. Confira se a API está rodando.
        </p>
      )}
      {orcamentos?.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Nenhum orçamento gerado ainda. Seus orçamentos aparecerão aqui automaticamente.
        </p>
      )}

      {orcamentos && orcamentos.length > 0 && (
        <div className="overflow-x-auto border border-border">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-8" />
                <TableHead>Projeto</TableHead>
                <TableHead>Data</TableHead>
                <TableHead>Padrão</TableHead>
                <TableHead>Cobertura</TableHead>
                <TableHead className="text-right">Área</TableHead>
                <TableHead className="text-right">Preço de Venda</TableHead>
                <TableHead className="w-28 text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orcamentos.map((registro) => {
                const expandido = expandidoId === registro.id
                return (
                  <Fragment key={registro.id}>
                    <TableRow
                      key={registro.id}
                      className="cursor-pointer"
                      onClick={() => setExpandidoId(expandido ? null : registro.id)}
                    >
                      <TableCell>
                        {expandido ? (
                          <ChevronDown className="size-3.5 text-muted-foreground" />
                        ) : (
                          <ChevronRight className="size-3.5 text-muted-foreground" />
                        )}
                      </TableCell>
                      <TableCell className="font-medium">{registro.nome_projeto}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {registro.data_criacao}
                      </TableCell>
                      <TableCell>{registro.padrao}</TableCell>
                      <TableCell>{registro.tipo_cobertura}</TableCell>
                      <TableCell className="text-right font-mono">
                        {registro.area_piso.toFixed(0)} m²
                      </TableCell>
                      <TableCell className="text-right font-mono font-medium">
                        {formatarMoeda(registro.preco_venda)}
                      </TableCell>
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1">
                          <Button variant="ghost" size="icon" className="size-7" asChild>
                            <a
                              href={urlDownload(`/historico/${registro.id}/excel`)}
                              title="Baixar Excel"
                            >
                              <Download className="size-3.5" />
                            </a>
                          </Button>
                          <Button variant="ghost" size="icon" className="size-7" asChild>
                            <a
                              href={urlDownload(`/historico/${registro.id}/pdf`)}
                              title="Baixar PDF"
                            >
                              <FileText className="size-3.5" />
                            </a>
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-7 text-destructive hover:text-destructive"
                            onClick={() => setParaExcluir(registro)}
                            title="Excluir do histórico"
                          >
                            <Trash2 className="size-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                    {expandido && <LinhaQuantitativos key={`${registro.id}-detalhe`} registro={registro} />}
                  </Fragment>
                )
              })}
            </TableBody>
          </Table>
        </div>
      )}

      <ConfirmarExclusaoDialog
        aberto={paraExcluir !== null}
        nomeProjeto={paraExcluir?.nome_projeto ?? ''}
        excluindo={excluir.isPending}
        onCancelar={() => setParaExcluir(null)}
        onConfirmar={() => {
          if (!paraExcluir) return
          excluir.mutate(paraExcluir.id, { onSuccess: () => setParaExcluir(null) })
        }}
      />
    </div>
  )
}
