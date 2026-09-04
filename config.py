import os

from dotenv import load_dotenv

load_dotenv()  # le o arquivo .env na raiz do projeto, se existir


def _carregar_lista_de_chaves():
    """Monta a lista de chaves Gemini disponiveis, na ordem em que
    devem ser tentadas. Suporta dois formatos no .env, pra nao quebrar
    quem ja tinha GEMINI_API_KEY configurada antes desse recurso:

    - GEMINI_API_KEYS=chave1,chave2,chave3   (varias chaves, recomendado)
    - GEMINI_API_KEY=chave1                  (formato antigo, continua funcionando)

    Se as duas variaveis existirem, a chave de GEMINI_API_KEY entra
    primeiro na lista (nao se perde), seguida das chaves extras de
    GEMINI_API_KEYS que ainda nao estiverem la.
    """
    chaves = []

    chave_unica = os.environ.get("GEMINI_API_KEY", "").strip()
    if chave_unica:
        chaves.append(chave_unica)

    chaves_extra = os.environ.get("GEMINI_API_KEYS", "")
    for chave in chaves_extra.split(","):
        chave = chave.strip()
        if chave and chave not in chaves:
            chaves.append(chave)

    return chaves


# Lista de chaves Gemini, na ordem de tentativa. Quando uma chave
# estoura a cota (erro RESOURCE_EXHAUSTED), o core/vision.py passa
# automaticamente pra proxima da lista antes de desistir.
GEMINI_API_KEYS = _carregar_lista_de_chaves()

# Mantido por compatibilidade com codigo que ainda espera uma chave
# unica (ex: mensagens de erro que citam "a chave configurada").
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""

# Modelo usado para ler as plantas. gemini-3.1-flash-lite e o mais barato
# disponivel atualmente e da conta bem de extracao estruturada simples.
# Troque aqui se precisar de mais precisao em plantas complexas
# (ex: gemini-3.5-flash), sem precisar mexer em codigo.
# Obs: modelos do Gemini sao descontinuados com frequencia -- se aparecer
# erro 404 "no longer available", confira o nome atual em
# https://ai.google.dev/gemini-api/docs/changelog
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

# Ativa modo mock: nenhuma chamada a API e feita, retorna dados fixos.
# Ideal para testar a interface (upload, calculo, geracao de excel)
# sem consumir cota do Gemini. Ative com MOCK_AI=true no .env
MOCK_AI = os.environ.get("MOCK_AI", "false").lower() == "true"

# Ativa cache local em disco: o mesmo arquivo de planta (mesmo hash)
# so e enviado pra API uma vez. Testes repetidos com a mesma planta
# nao gastam cota de novo.
USE_CACHE = os.environ.get("USE_CACHE", "true").lower() == "true"

# Dados usados quando MOCK_AI=true. Formato com extracao POR AMBIENTE:
# area de piso discriminada em seca/molhada/externa, portas em
# internas/externas. Inclui o bloco "confianca" no mesmo formato que o
# Gemini retorna de verdade, pra testar o indicador de confianca na
# tela sem gastar cota de API.
DADOS_MOCK = {
    "area_piso_seco": 120.40,
    "area_piso_molhado": 18.90,
    "area_piso_externo": 26.50,
    "metros_parede": 312.0,
    "portas_internas": 12,
    "portas_externas": 4,
    "janelas": 14,
    "confianca": {
        "area_piso_seco": {"nivel": "alta", "motivo": "Cota de 120,40m² escrita na planta"},
        "area_piso_molhado": {"nivel": "alta", "motivo": "Cotas de área escritas nos banheiros"},
        "area_piso_externo": {"nivel": "media", "motivo": "Soma visual da varanda e garagem"},
        "metros_parede": {"nivel": "media", "motivo": "Soma visual dos segmentos de parede"},
        "portas_internas": {"nivel": "alta", "motivo": "Contagem visual de 12 arcos internos"},
        "portas_externas": {"nivel": "alta", "motivo": "Contagem visual de 4 arcos externos"},
        "janelas": {"nivel": "baixa", "motivo": "Planta mock, sem base visual real"},
    },
    # Layout de exemplo (geometria) pra testar a maquete 3D no frontend
    # sem gastar API. E uma planta pequena e ilustrativa (4 comodos) --
    # NAO tenta reconciliar numericamente com os 7 campos agregados
    # acima (ex: so 2 portas internas aqui, contra 12 nos agregados).
    # O que importa e ser geometricamente coerente: retangulos sem
    # sobreposicao, paredes fechando o perimetro, aberturas apontando
    # pra paredes que existem, num sistema de coordenadas em metros.
    "layout": {
        "disponivel": True,
        "motivo_indisponivel": "",
        "comodos": [
            {"nome": "Sala", "tipo_piso": "seco", "x": 0.0, "y": 0.0, "largura": 5.0, "comprimento": 4.0},
            {"nome": "Quarto", "tipo_piso": "seco", "x": 5.0, "y": 0.0, "largura": 4.0, "comprimento": 4.0},
            {"nome": "Banheiro", "tipo_piso": "molhado", "x": 0.0, "y": 4.0, "largura": 2.5, "comprimento": 2.5},
            {"nome": "Varanda", "tipo_piso": "externo", "x": 2.5, "y": 4.0, "largura": 6.5, "comprimento": 2.5},
        ],
        "paredes": [
            {"x1": 0.0, "y1": 0.0, "x2": 9.0, "y2": 0.0},   # 0: externa inferior
            {"x1": 9.0, "y1": 0.0, "x2": 9.0, "y2": 6.5},   # 1: externa direita (Quarto)
            {"x1": 9.0, "y1": 6.5, "x2": 0.0, "y2": 6.5},   # 2: externa superior (Varanda/Banheiro)
            {"x1": 0.0, "y1": 6.5, "x2": 0.0, "y2": 0.0},   # 3: externa esquerda (Sala/Banheiro)
            {"x1": 5.0, "y1": 0.0, "x2": 5.0, "y2": 4.0},   # 4: divisa Sala/Quarto
            {"x1": 0.0, "y1": 4.0, "x2": 9.0, "y2": 4.0},   # 5: divisa fileira Sala+Quarto / Banheiro+Varanda
            {"x1": 2.5, "y1": 4.0, "x2": 2.5, "y2": 6.5},   # 6: divisa Banheiro/Varanda
        ],
        "aberturas": [
            {"tipo": "porta_externa", "parede_index": 0, "posicao": 0.30},  # entrada, junto a Sala
            {"tipo": "porta_interna", "parede_index": 4, "posicao": 0.50},  # Sala <-> Quarto
            {"tipo": "porta_interna", "parede_index": 5, "posicao": 0.14},  # Sala <-> Banheiro
            {"tipo": "porta_externa", "parede_index": 5, "posicao": 0.67},  # Quarto <-> Varanda
            {"tipo": "janela", "parede_index": 1, "posicao": 0.31},         # janela do Quarto
            {"tipo": "janela", "parede_index": 2, "posicao": 0.86},         # janela do Banheiro
            {"tipo": "janela", "parede_index": 3, "posicao": 0.69},         # janela da Sala
        ],
    },
}

# Constantes de extrusao 3D (frontend/src/lib/constants.ts espelha os
# mesmos valores). A IA nao estima espessura de parede nem altura de
# portas/janelas a partir de uma planta baixa (vista de cima nao mostra
# altura/espessura) -- sao padroes de mercado usados so pra desenhar a
# maquete 3D, sem impacto no calculo do orcamento.
ESPESSURA_PAREDE_PADRAO_M = 0.15
ALTURA_PORTA_PADRAO_M = 2.10
ALTURA_JANELA_PADRAO_M = 1.20
PEITORIL_JANELA_PADRAO_M = 0.90

# Local padrão da obra (usado em PDF e histórico)
LOCAL_OBRA = os.environ.get("LOCAL_OBRA", "Boa Vista/RR")

# Connection string do Postgres (Neon) usada por core/historico.py.
# Vem com sslmode=require incluso na string padrao do Neon.
DATABASE_URL = os.environ.get("DATABASE_URL", "")
