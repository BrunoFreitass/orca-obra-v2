import { OrbitControls, PerspectiveCamera } from '@react-three/drei'
import { Canvas } from '@react-three/fiber'
import { Component, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import {
  ALTURA_JANELA_M,
  ALTURA_PAREDE_M,
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

const COR_PORTA = '#b45309'
const COR_JANELA = '#60a5fa'

/** Marcador simples pra portas/janelas na v1 -- a IA não estima a largura
 * real do vão a partir de uma planta baixa, só a posição na parede. */
const LARGURA_MARCADOR_ABERTURA_M = 0.8

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

function Piso({ comodo }: { comodo: ComodoLayout }) {
  return (
    <mesh position={[comodo.x + comodo.largura / 2, 0.02, comodo.y + comodo.comprimento / 2]}>
      <boxGeometry args={[comodo.largura, 0.04, comodo.comprimento]} />
      <meshStandardMaterial color={COR_PISO[comodo.tipo_piso]} />
    </mesh>
  )
}

function Parede({ parede }: { parede: ParedeLayout }) {
  const comprimento = Math.hypot(parede.x2 - parede.x1, parede.y2 - parede.y1)
  if (comprimento <= 0) return null

  const angulo = anguloDaParede(parede)
  const meioX = (parede.x1 + parede.x2) / 2
  const meioZ = (parede.y1 + parede.y2) / 2

  return (
    <mesh position={[meioX, ALTURA_PAREDE_M / 2, meioZ]} rotation={[0, -angulo, 0]}>
      <boxGeometry args={[comprimento, ALTURA_PAREDE_M, ESPESSURA_PAREDE_M]} />
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
      <boxGeometry args={[LARGURA_MARCADOR_ABERTURA_M, altura, ESPESSURA_PAREDE_M * 1.6]} />
      <meshStandardMaterial color={ehJanela ? COR_JANELA : COR_PORTA} transparent opacity={0.85} />
    </mesh>
  )
}

function Cena({ layout }: { layout: LayoutGeometria }) {
  const { centroX, centroZ, distanciaCamera } = useMemo(() => {
    const minX = Math.min(...layout.comodos.map((c) => c.x))
    const minY = Math.min(...layout.comodos.map((c) => c.y))
    const maxX = Math.max(...layout.comodos.map((c) => c.x + c.largura))
    const maxY = Math.max(...layout.comodos.map((c) => c.y + c.comprimento))
    const largura = maxX - minX
    const profundidade = maxY - minY
    return {
      centroX: minX + largura / 2,
      centroZ: minY + profundidade / 2,
      distanciaCamera: Math.max(largura, profundidade, 4) * 1.4,
    }
  }, [layout])

  return (
    <>
      <PerspectiveCamera
        makeDefault
        position={[centroX + distanciaCamera, distanciaCamera * 0.9, centroZ + distanciaCamera]}
        fov={45}
      />
      <OrbitControls target={[centroX, 0, centroZ]} maxPolarAngle={Math.PI / 2.05} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[10, 15, 10]} intensity={0.8} />
      {layout.comodos.map((comodo, i) => (
        <Piso key={i} comodo={comodo} />
      ))}
      {layout.paredes.map((parede, i) => (
        <Parede key={i} parede={parede} />
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

function Indisponivel({ mensagem }: { mensagem: string }) {
  return (
    <p className="text-xs text-muted-foreground">
      {mensagem} {MENSAGEM_BASE}
    </p>
  )
}

interface Props {
  layout: LayoutGeometria | undefined
}

export function VisualizacaoPlanta3D({ layout }: Props) {
  const [webglDisponivel] = useState(isWebGLDisponivel)

  if (!layout?.disponivel) {
    const motivo = layout?.motivo_indisponivel ? ` — ${layout.motivo_indisponivel}` : '.'
    return <Indisponivel mensagem={`Pré-visualização 3D não disponível para esta planta${motivo}`} />
  }

  if (!webglDisponivel) {
    return <Indisponivel mensagem="Este navegador/dispositivo não suporta WebGL." />
  }

  return (
    <div className="h-80 w-full border border-border bg-card">
      <LimiteDeErro3D fallback={<Indisponivel mensagem="Não foi possível renderizar a pré-visualização 3D neste ambiente." />}>
        <Canvas gl={{ antialias: true }}>
          <Cena layout={layout} />
        </Canvas>
      </LimiteDeErro3D>
    </div>
  )
}
