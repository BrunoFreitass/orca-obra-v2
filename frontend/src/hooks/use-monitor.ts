import { useQuery } from '@tanstack/react-query'

import { apiGet } from '@/lib/api-client'
import type { MonitorStatus } from '@/lib/types'

export function useMonitorStatus() {
  return useQuery({
    queryKey: ['monitor', 'status'],
    queryFn: () => apiGet<MonitorStatus>('/monitor/status'),
    refetchInterval: 60_000, // status de cota vale a pena revalidar sozinho
  })
}
