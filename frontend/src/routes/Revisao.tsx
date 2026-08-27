import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { BadgeConfianca } from '@/components/BadgeConfianca'
import { TextoMarkdownLeve } from '@/components/TextoMarkdownLeve'
import { useAvaliarRevisao } from '@/hooks/use-revisao'
import { useExtracaoStore } from '@/lib/extracao-store'
import { useProjetoStore } from '@/lib/projeto-store'
import type { DadosRevisao } from '@/lib/types'

const LOCAL_OBRA = 'Boa Vista/RR'

const NIVEL_ESTILO: Record<string, string> = {
  alta: 'border-success/40 bg-success/10 text-success',
  media: 'border-warning/40 bg-warning/10 text-warning',
  baixa: 'border-destructive/40 bg-destructive/10 text-destructive',
}

function CampoNumerico({
  label,
  campo,
  ajuda,
}: {
  label: string
  campo: keyof DadosRevisao
  ajuda?: string
}) {
  const valor = useExtracaoStore((s) => s.valores[campo])
  const setCampo = useExtracaoStore((s) => s.setCampo)
  const confianca = useExtracaoStore((s) => s.dadosOriginais?.confianca[campo])

  return (
    <div className="flex flex-col gap-1">
      <Label className="text-xs">{label}</Label>
      <Input
        type="number"
        step="0.5"
        min="0"
        className="h-8 text-xs"
        value={valor}
        onChange={(e) => setCampo(campo, Number(e.target.value))}
        title={ajuda}
      />
      <BadgeConfianca info={confianca} />
    </div>
  )
}

export function Revisao() {
  const dadosOriginais = useExtracaoStore((s) => s.dadosOriginais)
  const valores = useExtracaoStore((s) => s.valores)
  const confirmado = useExtracaoStore((s) => s.confirmado)
  const setCampo = useExtracaoStore((s) => s.setCampo)
  const confirmar = useExtracaoStore((s) => s.confirmar)
  const reabrir = useExtracaoStore((s) => s.reabrir)
  const { padrao, estrutura } = useProjetoStore()

  const dadosCompletos = dadosOriginais ? { ...valores, confianca: dadosOriginais.confianca } : null
  const { data: avaliacao } = useAvaliarRevisao(dadosCompletos)

  if (!dadosOriginais) {
    return (
      <div className="flex flex-col gap-2">
        <h1 className="font-mono text-sm uppercase tracking-wider text-muted-foreground">
          Revisão dos Dados Extraídos
        </h1>
        <p className="text-sm text-muted-foreground">
          Envie uma planta baixa na sidebar e clique em "Analisar Planta com IA" pra começar.
        </p>
      </div>
    )
  }

  return (
    <div className="flex max-w-3xl flex-col gap-4">
      <div>
        <h1 className="font-mono text-sm uppercase tracking-wider text-muted-foreground">
          Revisão dos Dados Extraídos
        </h1>
        <p className="text-sm text-muted-foreground">
          Confira os valores lidos pela IA antes de gerar o orçamento. Ajuste se necessário.
        </p>
      </div>

      {avaliacao && (
        <div
          className={`border-l-2 px-4 py-2.5 text-sm font-medium ${NIVEL_ESTILO[avaliacao.indice_confianca.nivel]}`}
        >
          {avaliacao.indice_confianca.emoji} {avaliacao.indice_confianca.mensagem}
        </div>
      )}

      <div className="grid grid-cols-3 gap-3">
        <div className="border border-border p-3">
          <p className="text-[11px] uppercase text-muted-foreground">Padrão selecionado</p>
          <p className="mt-1 font-medium">{padrao}</p>
        </div>
        <div className="border border-border p-3">
          <p className="text-[11px] uppercase text-muted-foreground">Cobertura</p>
          <p className="mt-1 font-medium">{estrutura}</p>
        </div>
        <div className="border border-border p-3">
          <p className="text-[11px] uppercase text-muted-foreground">Local da obra</p>
          <p className="mt-1 font-medium">{LOCAL_OBRA}</p>
        </div>
      </div>

      {confirmado && (
        <div className="flex flex-col gap-2 border border-success/40 bg-success/10 p-3">
          <p className="text-sm text-success">✅ Dados confirmados. Revise abaixo se necessário.</p>
          <div className="grid grid-cols-4 gap-3 font-mono text-xs">
            <div>
              <div className="text-muted-foreground">Área Total</div>
              <div className="font-medium">{avaliacao?.area_piso_total.toFixed(1) ?? '—'} m²</div>
            </div>
            <div>
              <div className="text-muted-foreground">Paredes</div>
              <div className="font-medium">{valores.metros_parede.toFixed(1)} m</div>
            </div>
            <div>
              <div className="text-muted-foreground">Portas</div>
              <div className="font-medium">{valores.portas_internas + valores.portas_externas} un</div>
            </div>
            <div>
              <div className="text-muted-foreground">Janelas</div>
              <div className="font-medium">{valores.janelas} un</div>
            </div>
          </div>
          <Button variant="outline" size="sm" className="h-8 w-fit text-xs" onClick={reabrir}>
            ✏️ Reabrir para edição
          </Button>
        </div>
      )}

      <div className="flex flex-col gap-3">
        <div className="border border-border p-3">
          <p className="mb-2 text-xs font-medium">🏠 Áreas de Piso (m²)</p>
          <div className="grid grid-cols-3 gap-3">
            <CampoNumerico label="Área Seca" campo="area_piso_seco" ajuda="Sala, quartos, cozinha, corredores" />
            <CampoNumerico label="Área Molhada" campo="area_piso_molhado" ajuda="Banheiros, área de serviço" />
            <CampoNumerico label="Área Externa" campo="area_piso_externo" ajuda="Varanda, garagem" />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Área total de piso: {avaliacao?.area_piso_total.toFixed(1) ?? '—'} m²
          </p>
        </div>

        <div className="border border-border p-3">
          <p className="mb-2 text-xs font-medium">🧱 Vedação</p>
          <CampoNumerico label="Metros lineares de parede" campo="metros_parede" />
        </div>

        <div className="border border-border p-3">
          <p className="mb-2 text-xs font-medium">🚪 Aberturas (unidades)</p>
          <div className="grid grid-cols-3 gap-3">
            <CampoNumerico label="Portas Internas" campo="portas_internas" />
            <CampoNumerico label="Portas Externas" campo="portas_externas" />
            <CampoNumerico label="Janelas" campo="janelas" />
          </div>
        </div>
      </div>

      {avaliacao?.avisos_parede.map((aviso, i) => (
        <div key={i} className="whitespace-pre-line border-l-2 border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          <TextoMarkdownLeve texto={aviso} />
        </div>
      ))}

      {avaliacao?.sugestao_parede != null && avaliacao.sugestao_parede !== valores.metros_parede && (
        <div className="flex items-center gap-3">
          <Button
            size="sm"
            className="h-8 text-xs"
            onClick={() => setCampo('metros_parede', avaliacao.sugestao_parede!)}
          >
            ⚡ Ajustar para {avaliacao.sugestao_parede.toFixed(0)} m
          </Button>
          <p className="text-xs text-muted-foreground">
            Clique para aplicar a sugestão automaticamente (pode editar depois).
          </p>
        </div>
      )}

      {avaliacao && avaliacao.avisos_gerais.length > 0 && (
        <div className="border-l-2 border-warning/40 bg-warning/10 p-3 text-sm text-warning">
          ⚠️ Alguns valores parecem incomuns. Confira antes de gerar o orçamento:
          <ul className="mt-1 list-disc pl-4">
            {avaliacao.avisos_gerais.map((aviso, i) => (
              <li key={i}>{aviso}</li>
            ))}
          </ul>
        </div>
      )}

      {!confirmado && (
        <div>
          <Button className="h-9 text-xs" onClick={confirmar}>
            ✅ Confirmar Dados e Prosseguir
          </Button>
          <p className="mt-1 text-xs text-muted-foreground">
            Após confirmar, os campos serão recolhidos e você poderá focar no orçamento.
          </p>
        </div>
      )}
    </div>
  )
}
