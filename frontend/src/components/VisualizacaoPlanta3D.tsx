import { OrbitControls, PerspectiveCamera } from '@react-three/drei'
import { Canvas } from '@react-three/fiber'
import { Component, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { Button } from '@/components/ui/button'
import {
  ALTURA_JANELA_M,
  ALTURA_PAREDE_MAQUETE_M,
  ALTURA_PAREDE_REAL_M,
  ALTURA_PORTA_M,
  ESPESSURA_PAREDE_M,
  PEITORIL_JANELA_M,
} from '@/lib/constants'
import { isWebGLDisponivel } from '@/lib/webgl'
import type { AberturaLayout, ComodoLayout, LayoutGeometria, ParedeLayout } from '@/lib/types'

const MENSAGEM_BASE =
  'Os valores numéricos acima continuam válidos normalmente, mesmo sem a pré-visualização 3D.'

const COR_PISO: Record<ComodoLayout['tipo_piso'], string> = {
  seco: '#d8c6a1',
  molhado: '#7fb3d5',
  externo: '#93c47d',
}

const ROTULO_TIPO_PISO: Record<ComodoLayout['tipo_piso'], string> = {
  seco: 'Área seca',
  molhado: 'Área molhada',
  externo: 'Área externa',
}

const COR_PORTA = '#b45309'
const COR_JANELA = '#60a5fa'
const COR_PISO_SELECIONADO = '#3b82f6'

/** Painéis novos (card de detalhes, barra de câmeras, presets de luz) e o
 * toggle de altura de parede compartilham esse estilo "vidro" pra ficarem
 * visualmente coesos -- usa só tokens de tema (bg-card/border-border),
 * então funciona igual no claro e no escuro. */
const ESTILO_PAINEL_VIDRO = 'rounded-md border border-border/80 bg-card/70 shadow-sm backdrop-blur-md'

type PresetLuz = 'dia' | 'entardecer' | 'noite'

/** Cores/intensidades de luz da CENA 3D (dia/entardecer/noite) -- não tem
 * relação com o tema claro/escuro da UI (esse é sobre iluminação
 * arquitetônica simulada, não sobre acessibilidade da interface), por
 * isso são hex fixos mesmo. */
const PRESETS_LUZ: Record<PresetLuz, { corAmbiente: string; ambiente: number; corDirecional: string; direcional: number }> = {
  dia: { corAmbiente: '#ffffff', ambiente: 0.7, corDirecional: '#ffffff', direcional: 0.8 },
  entardecer: { corAmbiente: '#ffd9a0', ambiente: 0.45, corDirecional: '#ff9d5c', direcional: 0.6 },
  noite: { corAmbiente: '#8fa8ff', ambiente: 0.18, corDirecional: '#8fa8ff', direcional: 0.15 },
}

const ROTULO_PRESET_LUZ: Record<PresetLuz, string> = {
  dia: '☀️ Dia',
  entardecer: '🌇 Entardecer',
  noite: '🌙 Noite',
}

function pontoNaParede(parede: ParedeLayout, posicao: number) {
  return {
    x: parede.x1 + (parede.x2 - parede.x1) * posicao,
    z: parede.y1 + (parede.y2 - parede.y1) * posicao,
  }
}

/** Nosso plano (x,y) de core/vision.py mapeia pra (x, altura, z) no
 * Three.js -- x continua x, y da planta vira z (profundidade), y do
 * Three.js fica reservado pra altura. */
function anguloDaParede(parede: ParedeLayout) {
  return Math.atan2(parede.y2 - parede.y1, parede.x2 - parede.x1)
}

/** Mesma lógica de enquadramento usada pra cena inteira (largura,
 * profundidade e altura de parede viram distância de câmera), só que
 * reaproveitada tanto pro bounding box do layout inteiro quanto pro
 * bounding box de um único cômodo (câmera por ambiente). */
function calcularDistanciaCamera(largura: number, profundidade: number, alturaParede: number) {
  return Math.max(largura, profundidade, alturaParede * 2, 4) * 1.4
}

function formatarArea(largura: number, comprimento: number) {
  return (largura * comprimento).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function Piso({
  comodo,
  selecionado,
  onSelecionar,
}: {
  comodo: ComodoLayout
  selecionado: boolean
  onSelecionar: () => void
}) {
  return (
    <mesh
      position={[comodo.x + comodo.largura / 2, 0.02, comodo.y + comodo.comprimento / 2]}
      onClick={(e) => {
        e.stopPropagation()
        onSelecionar()
      }}
      onPointerOver={() => {
        document.body.style.cursor = 'pointer'
      }}
      onPointerOut={() => {
        document.body.style.cursor = 'auto'
      }}
    >
      <boxGeometry args={[comodo.largura, 0.04, comodo.comprimento]} />
      <meshStandardMaterial
        color={COR_PISO[comodo.tipo_piso]}
        emissive={selecionado ? COR_PISO_SELECIONADO : '#000000'}
        emissiveIntensity={selecionado ? 0.35 : 0}
      />
    </mesh>
  )
}

function Parede({ parede, altura }: { parede: ParedeLayout; altura: number }) {
  const comprimento = Math.hypot(parede.x2 - parede.x1, parede.y2 - parede.y1)
  if (comprimento <= 0) return null

  const angulo = anguloDaParede(parede)
  const meioX = (parede.x1 + parede.x2) / 2
  const meioZ = (parede.y1 + parede.y2) / 2

  return (
    <mesh position={[meioX, altura / 2, meioZ]} rotation={[0, -angulo, 0]}>
      <boxGeometry args={[comprimento, altura, ESPESSURA_PAREDE_M]} />
      <meshStandardMaterial color="#cbd5e1" />
    </mesh>
  )
}

function Abertura({ abertura, paredes }: { abertura: AberturaLayout; paredes: ParedeLayout[] }) {
  const parede = paredes[abertura.parede_index]
  if (!parede) return null

  const angulo = anguloDaParede(parede)
  const ponto = pontoNaParede(parede, abertura.posicao)

  const ehJanela = abertura.tipo === 'janela'
  const altura = ehJanela ? ALTURA_JANELA_M : ALTURA_PORTA_M
  const centroAltura = ehJanela ? PEITORIL_JANELA_M + altura / 2 : altura / 2

  return (
    <mesh position={[ponto.x, centroAltura, ponto.z]} rotation={[0, -angulo, 0]}>
      <boxGeometry args={[abertura.largura_m, altura, ESPESSURA_PAREDE_M * 1.6]} />
      <meshStandardMaterial color={ehJanela ? COR_JANELA : COR_PORTA} transparent opacity={0.85} />
    </mesh>
  )
}

function Cena({
  layout,
  alturaParede,
  presetLuz,
  comodoAtivo,
  onSelecionarComodo,
}: {
  layout: LayoutGeometria
  alturaParede: number
  presetLuz: PresetLuz
  comodoAtivo: number | null
  onSelecionarComodo: (indice: number) => void
}) {
  const { centroX, centroZ, distanciaCamera } = useMemo(() => {
    const comodoFoco = comodoAtivo != null ? layout.comodos[comodoAtivo] : undefined

    if (comodoFoco) {
      return {
        centroX: comodoFoco.x + comodoFoco.largura / 2,
        centroZ: comodoFoco.y + comodoFoco.comprimento / 2,
        distanciaCamera: calcularDistanciaCamera(comodoFoco.largura, comodoFoco.comprimento, alturaParede),
      }
    }

    const minX = Math.min(...layout.comodos.map((c) => c.x))
    const minY = Math.min(...layout.comodos.map((c) => c.y))
    const maxX = Math.max(...layout.comodos.map((c) => c.x + c.largura))
    const maxY = Math.max(...layout.comodos.map((c) => c.y + c.comprimento))
    const largura = maxX - minX
    const profundidade = maxY - minY
    return {
      centroX: minX + largura / 2,
      centroZ: minY + profundidade / 2,
      distanciaCamera: calcularDistanciaCamera(largura, profundidade, alturaParede),
    }
  }, [layout, alturaParede, comodoAtivo])

  const luz = PRESETS_LUZ[presetLuz]

  return (
    <>
      <PerspectiveCamera
        makeDefault
        position={[centroX + distanciaCamera, distanciaCamera * 0.9, centroZ + distanciaCamera]}
        fov={45}
      />
      <OrbitControls target={[centroX, 0, centroZ]} maxPolarAngle={Math.PI / 2.05} />
      <ambientLight color={luz.corAmbiente} intensity={luz.ambiente} />
      <directionalLight position={[10, 15, 10]} color={luz.corDirecional} intensity={luz.direcional} />
      {layout.comodos.map((comodo, i) => (
        <Piso key={i} comodo={comodo} selecionado={i === comodoAtivo} onSelecionar={() => onSelecionarComodo(i)} />
      ))}
      {layout.paredes.map((parede, i) => (
        <Parede key={i} parede={parede} altura={alturaParede} />
      ))}
      {layout.aberturas.map((abertura, i) => (
        <Abertura key={i} abertura={abertura} paredes={layout.paredes} />
      ))}
    </>
  )
}

interface LimiteDeErroProps {
  fallback: ReactNode
  children: ReactNode
}

interface LimiteDeErroState {
  comErro: boolean
}

/** O <Canvas> do react-three-fiber roda fora do controle normal do React
 * pra erros de render (perda de contexto WebGL, driver de GPU instável
 * etc.) -- só um error boundary de classe pega esse tipo de falha e evita
 * que ela derrube a tela de revisão inteira. */
class LimiteDeErro3D extends Component<LimiteDeErroProps, LimiteDeErroState> {
  state: LimiteDeErroState = { comErro: false }

  static getDerivedStateFromError() {
    return { comErro: true }
  }

  componentDidCatch(erro: unknown) {
    console.error('Falha ao renderizar a pré-visualização 3D:', erro)
  }

  render() {
    return this.state.comErro ? this.props.fallback : this.props.children
  }
}

function Indisponivel({ mensagem, acao }: { mensagem: string; acao?: ReactNode }) {
  return (
    <div className="flex flex-col items-start gap-2">
      <p className="text-xs text-muted-foreground">
        {mensagem} {MENSAGEM_BASE}
      </p>
      {acao}
    </div>
  )
}

/** Card de detalhes do cômodo selecionado -- sobrepõe o canto inferior
 * direito da área do canvas (não da tela inteira: este componente vive
 * embutido numa página normal, não em tela cheia). */
function CardDetalhesComodo({ comodo }: { comodo: ComodoLayout }) {
  return (
    <div className={`absolute right-2 bottom-2 max-w-[70%] px-3 py-2 text-xs ${ESTILO_PAINEL_VIDRO}`}>
      <p className="font-medium text-foreground">{comodo.nome}</p>
      <p className="text-muted-foreground">{ROTULO_TIPO_PISO[comodo.tipo_piso]}</p>
      <p className="mt-1 font-mono text-foreground">{formatarArea(comodo.largura, comodo.comprimento)} m²</p>
    </div>
  )
}

interface Props {
  layout: LayoutGeometria | undefined
  /** true quando `layout` veio do fallback ilustrativo, não da extração
   * oficial -- mostra o aviso de aproximado/não verificado. */
  ilustrativo?: boolean
  /** Presente só quando o arquivo original ainda está disponível pra
   * reenviar -- omitir esconde o botão de fallback. */
  onGerarIlustrativo?: () => void
  gerandoIlustrativo?: boolean
}

export function VisualizacaoPlanta3D({ layout, ilustrativo, onGerarIlustrativo, gerandoIlustrativo }: Props) {
  const [webglDisponivel] = useState(isWebGLDisponivel)
  // Default Real (2.8m) -- preserva o comportamento atual de quem já usa
  // o componente sem o toggle.
  const [alturaParede, setAlturaParede] = useState(ALTURA_PAREDE_REAL_M)
  const [presetLuz, setPresetLuz] = useState<PresetLuz>('dia')
  // Serve tanto pro card de detalhes (clicar no piso) quanto pra câmera
  // por ambiente (clicar num botão da lista) -- ver resumo da tarefa:
  // as duas interações foram unificadas no mesmo estado de propósito.
  // null = nada selecionado, card fechado, câmera mostra a cena inteira.
  const [comodoAtivo, setComodoAtivo] = useState<number | null>(null)
  // Evita indice obsoleto apontando pra um cômodo que não existe mais
  // quando `layout` muda de referência (ex: troca pra maquete
  // ilustrativa com um número diferente de cômodos) -- ajuste de estado
  // durante o render, padrão recomendado em vez de useEffect pra "resetar
  // estado quando uma prop muda".
  const [layoutAnterior, setLayoutAnterior] = useState(layout)
  if (layout !== layoutAnterior) {
    setLayoutAnterior(layout)
    setComodoAtivo(null)
  }

  if (!layout?.disponivel) {
    const motivo = layout?.motivo_indisponivel ? ` — ${layout.motivo_indisponivel}` : '.'
    return (
      <Indisponivel
        mensagem={`Pré-visualização 3D não disponível para esta planta${motivo}`}
        acao={
          onGerarIlustrativo && (
            <Button
              size="sm"
              variant="outline"
              className="h-8 w-fit text-xs"
              disabled={gerandoIlustrativo}
              onClick={onGerarIlustrativo}
            >
              {gerandoIlustrativo ? 'Gerando maquete aproximada… (pode levar ~2 min)' : '🧊 Gerar visualização 3D aproximada'}
            </Button>
          )
        }
      />
    )
  }

  if (!webglDisponivel) {
    return <Indisponivel mensagem="Este navegador/dispositivo não suporta WebGL." />
  }

  const comodoSelecionado = comodoAtivo != null ? layout.comodos[comodoAtivo] : undefined

  return (
    <div className="flex flex-col gap-2">
      {ilustrativo && (
        <p className="border-l-2 border-warning/40 bg-warning/10 px-3 py-1.5 text-xs text-warning">
          ⚠️ Maquete aproximada e ilustrativa, gerada sob demanda — não confira medidas aqui, os
          cômodos podem não corresponder exatamente à planta real.
        </p>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className={`flex flex-wrap gap-1 p-1 ${ESTILO_PAINEL_VIDRO}`}>
          {layout.comodos.map((comodo, i) => (
            <Button
              key={i}
              size="sm"
              variant={i === comodoAtivo ? 'default' : 'ghost'}
              className="h-7 text-xs"
              onClick={() => setComodoAtivo(i)}
            >
              {comodo.nome}
            </Button>
          ))}
        </div>

        <div className="flex gap-1">
          <div className={`flex gap-1 p-1 ${ESTILO_PAINEL_VIDRO}`}>
            {(Object.keys(PRESETS_LUZ) as PresetLuz[]).map((preset) => (
              <Button
                key={preset}
                size="sm"
                variant={preset === presetLuz ? 'default' : 'ghost'}
                className="h-7 text-xs"
                onClick={() => setPresetLuz(preset)}
              >
                {ROTULO_PRESET_LUZ[preset]}
              </Button>
            ))}
          </div>

          <div className={`flex gap-1 p-1 ${ESTILO_PAINEL_VIDRO}`}>
            <Button
              size="sm"
              variant={alturaParede === ALTURA_PAREDE_MAQUETE_M ? 'default' : 'ghost'}
              className="h-7 text-xs"
              onClick={() => setAlturaParede(ALTURA_PAREDE_MAQUETE_M)}
            >
              Maquete (1,2m)
            </Button>
            <Button
              size="sm"
              variant={alturaParede === ALTURA_PAREDE_REAL_M ? 'default' : 'ghost'}
              className="h-7 text-xs"
              onClick={() => setAlturaParede(ALTURA_PAREDE_REAL_M)}
            >
              Real (2,8m)
            </Button>
          </div>
        </div>
      </div>

      <div className="relative h-80 w-full border border-border bg-card">
        <LimiteDeErro3D fallback={<Indisponivel mensagem="Não foi possível renderizar a pré-visualização 3D neste ambiente." />}>
          <Canvas gl={{ antialias: true }}>
            <Cena
              layout={layout}
              alturaParede={alturaParede}
              presetLuz={presetLuz}
              comodoAtivo={comodoAtivo}
              onSelecionarComodo={setComodoAtivo}
            />
          </Canvas>
        </LimiteDeErro3D>
        {comodoSelecionado && <CardDetalhesComodo comodo={comodoSelecionado} />}
      </div>
    </div>
  )
}
