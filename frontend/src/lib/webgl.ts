/** Detecção defensiva de suporte a WebGL -- alguns ambientes restritos
 * (navegadores corporativos, VMs sem GPU, certas versões mobile) não têm
 * WebGL habilitado. getContext pode inclusive lançar exceção em vez de só
 * retornar null nesses casos, então tudo aqui fica dentro de um try/catch. */
export function isWebGLDisponivel(): boolean {
  try {
    const canvas = document.createElement('canvas')
    const contexto = canvas.getContext('webgl2') || canvas.getContext('webgl')
    return contexto !== null
  } catch {
    return false
  }
}
