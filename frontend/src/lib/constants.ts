/** Local da obra -- hoje fixo (config.py::LOCAL_OBRA no backend), sem
 * campo de edição em nenhuma das duas UIs. */
export const LOCAL_OBRA = 'Boa Vista/RR'

// --- Constantes de extrusão 3D (VisualizacaoPlanta3D) ---------------------
// Espelham config.py (ESPESSURA_PAREDE_PADRAO_M etc.) e
// core/models.py::ALTURA_PAREDE_PADRAO -- a IA não estima esses valores a
// partir de uma planta baixa (vista de cima não mostra altura/espessura),
// então são padrões de mercado usados só pra desenhar a maquete.
export const ESPESSURA_PAREDE_M = 0.15
export const ALTURA_PAREDE_M = 2.8
export const ALTURA_PORTA_M = 2.1
export const ALTURA_JANELA_M = 1.2
export const PEITORIL_JANELA_M = 0.9
