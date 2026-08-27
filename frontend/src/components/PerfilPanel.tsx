import { useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useEnviarLogo, usePerfil, useSalvarPerfil } from '@/hooks/use-perfil'
import type { PerfilEmpresaUpdate } from '@/lib/types'

const CAMPOS_VAZIOS: PerfilEmpresaUpdate = {
  nome_empresa: '',
  profissional_responsavel: '',
  telefone: '',
  email: '',
  registro: '',
}

export function PerfilPanel() {
  const { data: perfil } = usePerfil()
  const salvar = useSalvarPerfil()
  const enviarLogo = useEnviarLogo()
  const [form, setForm] = useState<PerfilEmpresaUpdate>(CAMPOS_VAZIOS)

  // Só preenche o form com o que veio do servidor uma vez -- depois
  // disso o usuário é quem controla os campos (não sobrescreve
  // enquanto ele digita).
  useEffect(() => {
    if (perfil) {
      setForm({
        nome_empresa: perfil.nome_empresa,
        profissional_responsavel: perfil.profissional_responsavel,
        telefone: perfil.telefone,
        email: perfil.email,
        registro: perfil.registro,
      })
    }
  }, [perfil])

  function atualizarCampo(campo: keyof PerfilEmpresaUpdate, valor: string) {
    setForm((atual) => ({ ...atual, [campo]: valor }))
  }

  return (
    <div className="flex flex-col gap-2">
      <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
        Sua Empresa
      </p>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="nome_empresa" className="text-xs">
          Nome da Empresa
        </Label>
        <Input
          id="nome_empresa"
          className="h-8 text-xs"
          value={form.nome_empresa}
          onChange={(e) => atualizarCampo('nome_empresa', e.target.value)}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="profissional" className="text-xs">
          Profissional Responsável
        </Label>
        <Input
          id="profissional"
          className="h-8 text-xs"
          value={form.profissional_responsavel}
          onChange={(e) => atualizarCampo('profissional_responsavel', e.target.value)}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="registro" className="text-xs">
          Registro (CREA/CAU/CNPJ)
        </Label>
        <Input
          id="registro"
          className="h-8 text-xs"
          value={form.registro}
          onChange={(e) => atualizarCampo('registro', e.target.value)}
        />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="telefone" className="text-xs">
            Telefone
          </Label>
          <Input
            id="telefone"
            className="h-8 text-xs"
            value={form.telefone}
            onChange={(e) => atualizarCampo('telefone', e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email" className="text-xs">
            E-mail
          </Label>
          <Input
            id="email"
            className="h-8 text-xs"
            value={form.email}
            onChange={(e) => atualizarCampo('email', e.target.value)}
          />
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="logo" className="text-xs">
          Logo (PNG/JPG)
        </Label>
        {perfil?.caminho_logo && (
          <p className="truncate text-[11px] text-muted-foreground">
            Atual: {perfil.caminho_logo.split(/[/\\]/).pop()}
          </p>
        )}
        <Input
          id="logo"
          type="file"
          accept="image/png,image/jpeg"
          className="h-8 text-xs"
          onChange={(e) => {
            const arquivo = e.target.files?.[0]
            if (arquivo) enviarLogo.mutate(arquivo)
          }}
        />
      </div>

      <Button
        size="sm"
        className="mt-1 h-8 text-xs"
        onClick={() => salvar.mutate(form)}
        disabled={salvar.isPending}
      >
        {salvar.isPending ? 'Salvando…' : 'Salvar dados da empresa'}
      </Button>
      {salvar.isSuccess && <p className="text-[11px] text-success">Salvo.</p>}
    </div>
  )
}
