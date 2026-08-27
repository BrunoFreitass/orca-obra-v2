import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useProjetoStore } from '@/lib/projeto-store'
import type { Padrao, TipoCobertura } from '@/lib/types'

const PADROES: Padrao[] = ['Econômico', 'Médio', 'Alto Padrão']
const COBERTURAS: TipoCobertura[] = ['Telhado', 'Laje']

export function ProjetoPanel() {
  const { nomeProjeto, cliente, padrao, estrutura, setNomeProjeto, setCliente, setPadrao, setEstrutura } =
    useProjetoStore()

  return (
    <div className="flex flex-col gap-2.5">
      <div className="flex flex-col gap-1.5">
        <Label className="text-xs">Nome do projeto</Label>
        <Input
          className="h-8 text-xs"
          placeholder="Ex.: Residência Sr. João"
          value={nomeProjeto}
          onChange={(e) => setNomeProjeto(e.target.value)}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <Label className="text-xs">Cliente</Label>
        <Input
          className="h-8 text-xs"
          placeholder="Ex.: João da Silva"
          value={cliente}
          onChange={(e) => setCliente(e.target.value)}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <Label className="text-xs">Padrão de acabamento</Label>
        <Select value={padrao} onValueChange={(v) => setPadrao(v as Padrao)}>
          <SelectTrigger className="h-8 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PADROES.map((p) => (
              <SelectItem key={p} value={p}>
                {p}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label className="text-xs">Tipo de cobertura</Label>
        <Select value={estrutura} onValueChange={(v) => setEstrutura(v as TipoCobertura)}>
          <SelectTrigger className="h-8 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {COBERTURAS.map((c) => (
              <SelectItem key={c} value={c}>
                {c}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
