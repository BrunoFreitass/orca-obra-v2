import type { ConfiancaCampo } from '@/lib/types'

const VISUAL: Record<string, { emoji: string; label: string }> = {
  alta: { emoji: '🟢', label: 'Confiança alta' },
  media: { emoji: '🟡', label: 'Confiança média' },
  baixa: { emoji: '🔴', label: 'Confiança baixa — revise' },
}

export function BadgeConfianca({ info }: { info: ConfiancaCampo | undefined }) {
  const nivel = info?.nivel ?? 'media'
  const visual = VISUAL[nivel] ?? VISUAL.media
  return (
    <p className="text-[11px] text-muted-foreground">
      {visual.emoji} {visual.label}
      {info?.motivo ? ` — ${info.motivo}` : ''}
    </p>
  )
}
