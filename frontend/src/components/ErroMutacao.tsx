import { extrairDetalheErro } from '@/hooks/use-extracao'

/** Mensagem de falha de uma mutation (upload, aplicar, salvar…) -- `erro`
 * é o `.error` da mutation, null quando não houve falha. */
export function ErroMutacao({ erro }: { erro: unknown }) {
  if (!erro) return null
  return <p className="text-[11px] text-destructive">{extrairDetalheErro(erro).mensagem_amigavel}</p>
}
