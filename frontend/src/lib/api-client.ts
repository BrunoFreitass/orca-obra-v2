/** Cliente HTTP fino pra API do OrçaObra AI -- todas as chamadas passam
 * por aqui pra centralizar tratamento de erro e base URL. Em dev, o
 * Vite faz proxy de /api pra localhost:8000 (ver vite.config.ts); em
 * produção, front e API são a mesma origem. */

export class ApiError extends Error {
  status: number
  /** api/*.py às vezes manda um detail estruturado (dict), não só
   * string (ex: /extracao manda {mensagem_amigavel, detalhe_tecnico}).
   * Guardado bruto aqui pra quem precisar dos campos, sem round-trip
   * de JSON.stringify/parse pela `message` (que é sempre string). */
  detail: unknown

  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : JSON.stringify(detail))
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function tratarResposta<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const corpo = await res.json().catch(() => null)
    throw new ApiError(res.status, corpo?.detail ?? `Erro ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export async function apiGet<T>(caminho: string): Promise<T> {
  return tratarResposta<T>(await fetch(`/api${caminho}`))
}

export async function apiDelete(caminho: string): Promise<void> {
  await tratarResposta<void>(await fetch(`/api${caminho}`, { method: 'DELETE' }))
}

export async function apiPut<T>(caminho: string, corpo: unknown): Promise<T> {
  return tratarResposta<T>(
    await fetch(`/api${caminho}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(corpo),
    }),
  )
}

export async function apiPost<T>(caminho: string, corpo: unknown): Promise<T> {
  return tratarResposta<T>(
    await fetch(`/api${caminho}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(corpo),
    }),
  )
}

export async function apiPostFormData<T>(caminho: string, formData: FormData): Promise<T> {
  return tratarResposta<T>(await fetch(`/api${caminho}`, { method: 'POST', body: formData }))
}

/** Monta a URL de download (Excel/PDF) -- usada em <a href> direto, não
 * via fetch, pra deixar o navegador cuidar do download. */
export function urlDownload(caminho: string): string {
  return `/api${caminho}`
}
