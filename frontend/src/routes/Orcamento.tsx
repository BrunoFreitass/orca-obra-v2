import { useEffect } from 'react'

import { GradeOrcamento } from '@/components/GradeOrcamento'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useGerarOrcamento, useMaoDeObra, useMateriais } from '@/hooks/use-orcamento'
import { ApiError, urlDownload } from '@/lib/api-client'
import { LOCAL_OBRA } from '@/lib/constants'
import { useExtracaoStore } from '@/lib/extracao-store'
import { useOrcamentoStore } from '@/lib/orcamento-store'
import { useProjetoStore } from '@/lib/projeto-store'
import { formatarMoeda } from '@/lib/utils'

export function Orcamento() {
  const dadosOriginais = useExtracaoStore((s) => s.dadosOriginais)
  const valores = useExtracaoStore((s) => s.valores)
  const { nomeProjeto, padrao, estrutura } = useProjetoStore()

  const corpo = dadosOriginais ? { ...valores, padrao, estrutura } : null
  const { data: materiaisSugeridos } = useMateriais(corpo)
  const { data: maoDeObraSugerida } = useMaoDeObra(corpo)

  const {
    materiais,
    maoDeObra,
    bdi,
    carregarSugeridos,
    setPrecoMaterial,
    setPrecoMaoDeObra,
    setBdi,
  } = useOrcamentoStore()

  const assinatura = corpo ? JSON.stringify(corpo) : null
  useEffect(() => {
    if (assinatura && materiaisSugeridos && maoDeObraSugerida) {
      carregarSugeridos(assinatura, materiaisSugeridos, maoDeObraSugerida)
    }
  }, [assinatura, materiaisSugeridos, maoDeObraSugerida, carregarSugeridos])

  const gerar = useGerarOrcamento()

  const custoDireto = materiais.reduce((s, i) => s + i.Total, 0) + maoDeObra.reduce((s, i) => s + i.Total, 0)
  const precoVenda = custoDireto * (1 + bdi / 100)

  if (!dadosOriginais) {
    return (
      <div className="flex flex-col gap-2">
        <h1 className="font-mono text-sm uppercase tracking-wider text-muted-foreground">Orçamento</h1>
        <p className="text-sm text-muted-foreground">
          Envie uma planta baixa na sidebar e clique em "Analisar Planta com IA" pra começar.
        </p>
      </div>
    )
  }

  return (
    <div className="flex max-w-4xl flex-col gap-4">
      <div>
        <h1 className="font-mono text-sm uppercase tracking-wider text-muted-foreground">Orçamento</h1>
        <p className="text-sm text-muted-foreground">
          Edite o preço unitário conforme seu fornecedor. Os totais recalculam automaticamente.
        </p>
      </div>

      <GradeOrcamento titulo="📦 Materiais" itens={materiais} onEditarPreco={setPrecoMaterial} />
      <GradeOrcamento titulo="👷 Mão de Obra" itens={maoDeObra} onEditarPreco={setPrecoMaoDeObra} />

      <div className="border border-border p-3">
        <p className="mb-2 text-xs font-medium">💰 BDI (Benefícios e Despesas Indiretas)</p>
        <p className="mb-2 text-xs text-muted-foreground">
          Percentual sobre o custo direto para administração, lucro, impostos e imprevistos.
        </p>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            min="0"
            max="100"
            step="1"
            className="h-8 w-24 text-xs"
            value={bdi}
            onChange={(e) => setBdi(Number(e.target.value))}
          />
          <span className="text-xs text-muted-foreground">%</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="border border-border p-3">
          <p className="text-[11px] uppercase text-muted-foreground">Custo Direto</p>
          <p className="mt-1 font-mono font-medium">{formatarMoeda(custoDireto)}</p>
        </div>
        <div className="border border-border p-3">
          <p className="text-[11px] uppercase text-muted-foreground">BDI</p>
          <p className="mt-1 font-mono font-medium">{bdi.toFixed(0)}%</p>
        </div>
        <div className="border border-success/40 bg-success/10 p-3">
          <p className="text-[11px] uppercase text-muted-foreground">Preço de Venda</p>
          <p className="mt-1 font-mono font-medium text-success">{formatarMoeda(precoVenda)}</p>
        </div>
      </div>

      <div>
        <Button
          className="h-9 text-xs"
          disabled={gerar.isPending || !nomeProjeto.trim()}
          onClick={() =>
            gerar.mutate({
              ...valores,
              materiais,
              mao_de_obra: maoDeObra,
              bdi_percentual: bdi,
              nome_projeto: nomeProjeto,
              padrao,
              estrutura,
              local_obra: LOCAL_OBRA,
            })
          }
        >
          {gerar.isPending ? 'Gerando…' : '🚀 Gerar Orçamento Completo'}
        </Button>
        {!nomeProjeto.trim() && (
          <p className="mt-1 text-xs text-warning">
            Informe o nome do projeto/cliente na sidebar antes de gerar.
          </p>
        )}
        {gerar.isError && (
          <p className="mt-1 text-xs text-destructive">
            {gerar.error instanceof ApiError && typeof gerar.error.detail === 'string'
              ? gerar.error.detail
              : 'Erro ao gerar orçamento.'}
          </p>
        )}
      </div>

      {gerar.data && (
        <div className="flex flex-col gap-2 border border-success/40 bg-success/10 p-3">
          <p className="text-sm text-success">✅ Orçamento gerado com sucesso!</p>
          <div className="grid grid-cols-4 gap-3 font-mono text-xs">
            <div>
              <div className="text-muted-foreground">Área Total</div>
              <div className="font-medium">
                {(valores.area_piso_seco + valores.area_piso_molhado + valores.area_piso_externo).toFixed(1)} m²
              </div>
            </div>
            <div>
              <div className="text-muted-foreground">Paredes</div>
              <div className="font-medium">{valores.metros_parede.toFixed(0)} m</div>
            </div>
            <div>
              <div className="text-muted-foreground">Portas + Janelas</div>
              <div className="font-medium">
                {valores.portas_internas + valores.portas_externas + valores.janelas} un
              </div>
            </div>
            <div>
              <div className="text-muted-foreground">Preço de Venda</div>
              <div className="font-medium">{formatarMoeda(gerar.data.preco_venda)}</div>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="h-8 text-xs" asChild>
              <a href={urlDownload(`/historico/${gerar.data.historico_id}/excel`)}>
                📊 Baixar Excel (uso interno)
              </a>
            </Button>
            <Button variant="outline" size="sm" className="h-8 text-xs" asChild>
              <a href={urlDownload(`/historico/${gerar.data.historico_id}/pdf`)}>
                📄 Baixar PDF (proposta ao cliente)
              </a>
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
