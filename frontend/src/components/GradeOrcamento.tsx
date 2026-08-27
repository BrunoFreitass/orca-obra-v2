import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatarMoeda } from '@/lib/utils'
import type { ItemOrcamento } from '@/lib/types'

interface Props {
  titulo: string
  itens: ItemOrcamento[]
  onEditarPreco: (index: number, precoUnit: number) => void
}

/** Grade editável de materiais/mão de obra -- Quantidade e Total são
 * calculados (somente leitura), só o Preço Unit. é editável, igual ao
 * st.data_editor de core/ui_orcamento.py. */
export function GradeOrcamento({ titulo, itens, onEditarPreco }: Props) {
  const total = itens.reduce((soma, item) => soma + item.Total, 0)

  return (
    <div className="border border-border p-3">
      <p className="mb-2 text-xs font-medium">{titulo}</p>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Item</TableHead>
              <TableHead className="text-right">Quantidade</TableHead>
              <TableHead className="text-right">Preço Unit. (R$)</TableHead>
              <TableHead className="text-right">Total (R$)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {itens.map((item, i) => (
              <TableRow key={`${item.Material}-${i}`} className="hover:bg-transparent">
                <TableCell className="text-xs">{item.Material}</TableCell>
                <TableCell className="text-right font-mono text-xs">{item.Quantidade}</TableCell>
                <TableCell className="text-right">
                  <Input
                    type="number"
                    step="0.5"
                    min="0"
                    className="ml-auto h-7 w-24 text-right text-xs"
                    value={item.Preco_Unit}
                    onChange={(e) => onEditarPreco(i, Number(e.target.value))}
                  />
                </TableCell>
                <TableCell className="text-right font-mono text-xs">{formatarMoeda(item.Total)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <p className="mt-2 text-right text-xs font-medium">
        Total: <span className="font-mono">{formatarMoeda(total)}</span>
      </p>
    </div>
  )
}
