import { Moon, Sun } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

import { MonitorBadge } from '@/components/MonitorBadge'
import { PainelColapsavel } from '@/components/PainelColapsavel'
import { PerfilPanel } from '@/components/PerfilPanel'
import { PrecosPanel } from '@/components/PrecosPanel'
import { ProjetoPanel } from '@/components/ProjetoPanel'
import { SinapiPanel } from '@/components/SinapiPanel'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { useThemeStore } from '@/lib/theme-store'

const NAV_ITEMS = [
  { to: '/', label: 'Histórico' },
  { to: '/revisao', label: 'Revisão' },
  { to: '/orcamento', label: 'Orçamento' },
]

export function AppShell() {
  const tema = useThemeStore((s) => s.tema)
  const alternarTema = useThemeStore((s) => s.alternarTema)

  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      {/* Barra de ferramentas -- densa, com borda em vez de sombra */}
      <header className="flex h-12 shrink-0 items-center gap-4 border-b border-border bg-card px-4">
        <span className="font-mono text-xs font-medium uppercase tracking-widest text-primary">
          OrçaObra AI
        </span>
        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                cn(
                  'rounded-sm px-2 py-1 text-xs font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                  isActive && 'bg-accent text-accent-foreground',
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="flex-1" />
        <MonitorBadge />
        <Button variant="ghost" size="icon" className="size-7" onClick={alternarTema}>
          {tema === 'claro' ? <Moon className="size-4" /> : <Sun className="size-4" />}
        </Button>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Painel lateral persistente -- empresa, projeto, preços e SINAPI. */}
        <aside className="w-64 shrink-0 overflow-y-auto border-r border-border bg-sidebar p-3">
          <PerfilPanel />
          <Separator className="my-3" />
          <PainelColapsavel titulo="Projeto" abertoPorPadrao>
            <ProjetoPanel />
          </PainelColapsavel>
          <Separator className="my-1" />
          <PainelColapsavel titulo="Preços Customizados">
            <PrecosPanel />
          </PainelColapsavel>
          <Separator className="my-1" />
          <PainelColapsavel titulo="Importar SINAPI oficial">
            <SinapiPanel />
          </PainelColapsavel>
        </aside>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
