import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface Props {
  aberto: boolean
  nomeProjeto: string
  excluindo: boolean
  onConfirmar: () => void
  onCancelar: () => void
}

/** Confirmação em dois passos pra excluir um orçamento do histórico --
 * mesma cautela que a tela do Streamlit já tem (não é uma ação
 * reversível: o registro some do banco). */
export function ConfirmarExclusaoDialog({ aberto, nomeProjeto, excluindo, onConfirmar, onCancelar }: Props) {
  return (
    <Dialog open={aberto} onOpenChange={(open) => !open && onCancelar()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Excluir orçamento?</DialogTitle>
          <DialogDescription>
            "{nomeProjeto}" será removido do histórico. Os arquivos Excel/PDF já gerados
            continuam no disco, mas o registro não pode ser recuperado depois.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onCancelar} disabled={excluindo}>
            Cancelar
          </Button>
          <Button variant="destructive" onClick={onConfirmar} disabled={excluindo}>
            {excluindo ? 'Excluindo…' : 'Sim, excluir'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
