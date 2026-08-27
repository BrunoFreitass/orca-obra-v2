import { Badge } from '@/components/ui/badge'
import { useMonitorStatus } from '@/hooks/use-monitor'
import { cn } from '@/lib/utils'

const CORES_NIVEL: Record<string, string> = {
  ok: 'text-success border-success/40 bg-success/10',
  alerta: 'text-warning border-warning/40 bg-warning/10',
  critico: 'text-destructive border-destructive/40 bg-destructive/10',
}

export function MonitorBadge() {
  const { data: status } = useMonitorStatus()
  if (!status) return null

  return (
    <Badge
      variant="outline"
      className={cn('font-mono text-[11px] font-normal', CORES_NIVEL[status.nivel])}
    >
      {status.total}/{status.limite} hoje
    </Badge>
  )
}
