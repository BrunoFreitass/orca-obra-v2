import base64
import json
import os
import time
import tempfile

import cv2
import requests

from core import cache
from config import GEMINI_API_KEYS, GEMINI_MODEL, MOCK_AI, USE_CACHE, DADOS_MOCK
from core.image_processing import melhorar_imagem

class ErroExtracaoAmigavel(Exception):
    """
    Exceção personalizada para erros de extração da planta.
    Permite exibir mensagens amigáveis ao usuário
    sem expor detalhes técnicos diretamente.
    """

    def __init__(self, mensagem, detalhe_tecnico=None):
        super().__init__(mensagem)
        self.mensagem_amigavel = mensagem
        self.detalhe_tecnico = detalhe_tecnico


CAMPOS_AGREGADOS = (
    "area_piso_seco", "area_piso_molhado", "area_piso_externo",
    "metros_parede", "portas_internas", "portas_externas", "janelas",
)


def _preparar_imagem(caminho_arquivo):
    """
    Sempre devolve uma imagem JPEG otimizada para enviar ao Gemini.
    PDFs e imagens passam pelo mesmo pré-processamento.
    """

    if caminho_arquivo.lower().endswith(".pdf"):
        import fitz

        with fitz.open(caminho_arquivo) as doc:
            pagina = doc[0]
            pix = pagina.get_pixmap(dpi=200)

        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
            delete=False
        ) as temp:
            imagem_temporaria = temp.name

        try:
            pix.save(imagem_temporaria)

            imagem = melhorar_imagem(imagem_temporaria)

        finally:
            if os.path.exists(imagem_temporaria):
                os.remove(imagem_temporaria)

    else:
        imagem = melhorar_imagem(caminho_arquivo)

    _, buffer = cv2.imencode(".jpg", imagem)

    return buffer.tobytes()


def _montar_prompt():
    return """
    Analise esta imagem de planta baixa de engenharia/arquitetura.

    Antes de responder, raciocine internamente assim, COMODO POR
    COMODO (nao inclua esse raciocinio na resposta final, so o JSON
    agregado no final):
    0. Quando a planta não possuir quadro de áreas:
        (a) utilize as cotas lineares disponíveis;
        (b) identifique largura e comprimento de cada ambiente;
        (c) calcule a área aproximada;
        (d) informe confiança como "media";
        (f) nunca invente área como se fosse leitura direta.
    1. Liste cada comodo visivel na planta (sala, quarto, cozinha,
       banheiro, area de servico, varanda, garagem, etc).
    2. Para cada comodo, classifique o tipo de piso em uma das 3
       categorias:
       - "seco": ambientes sociais/intimos comuns (sala, quarto,
         cozinha, corredor, escritorio) -- normalmente porcelanato.
       - "molhado": ambientes com ponto de agua e caimento (banheiro,
         area de servico, lavabo) -- normalmente ceramica.
       - "externo": ambientes descobertos ou semi-descobertos (varanda,
         garagem, area externa, quintal coberto) -- piso antiderrapante.
    3. Determine a area (m2) de cada comodo. Existem DOIS jeitos
       possiveis de chegar nesse numero, e voce deve saber qual deles
       usou em cada comodo (isso importa para a etapa de confianca
       mais abaixo):
       (a) A planta tem uma cota de AREA ja pronta e escrita perto do
           comodo (ex: um texto "A: 16,56 m²" ou "16,56 m²" dentro ou
           proximo do comodo, geralmente vindo de um "Quadro de Areas").
           Nesse caso, USE esse numero diretamente.
       (b) A planta NAO tem area pronta pra aquele comodo -- so tem
           cotas de comprimento nas bordas (ex: "3,85", "4,30" nas
           réguas de medida externas). Nesse caso, voce PRECISA
           multiplicar largura x altura do comodo pra estimar a area,
           o que e uma estimativa por calculo, nao uma leitura direta.
    4. Percorra o perimetro de cada comodo e conte os segmentos de
       parede, somando os comprimentos lineares (nao conte a mesma
       parede duas vezes quando ela e compartilhada entre dois comodos).
    5. Para cada porta da planta (geralmente um arco de 1/4 de circulo),
       classifique se ela e:
       - "interna": conecta dois ambientes internos da casa.
       - "externa": conecta um ambiente interno a area externa/rua
         (porta de entrada, porta de fundos, porta pra varanda/quintal).
    6. Conte, uma por uma, todas as janelas da planta (linhas paralelas
       na espessura de parede externa). Janelas sao sempre tratadas
       como elemento externo, nao precisam de classificacao adicional.

    Depois de percorrer todos os comodos, SOME os resultados nas
    seguintes 7 variaveis agregadas (essas sao as unicas que vao pro
    JSON final):
    - area_piso_seco: soma da area de todos os comodos "seco"
    - area_piso_molhado: soma da area de todos os comodos "molhado"
    - area_piso_externo: soma da area de todos os comodos "externo"
    - metros_parede: soma de todos os segmentos de parede (passo 4)
    - portas_internas: contagem total de portas internas (passo 5)
    - portas_externas: contagem total de portas externas (passo 5)
    - janelas: contagem total de janelas (passo 6)

    Para CADA uma dessas 7 variaveis agregadas, avalie sua propria
    confianca de acordo com esta regra objetiva (nao subjetiva) --
    PRESTE ATENCAO ESPECIAL na diferenca entre "alta" e "media" pras
    3 variaveis de area, que e uma fonte comum de erro:
    - "alta": TODOS os comodos que compoem essa soma tinham uma cota
      de AREA ja pronta e escrita na planta (metodo 3a acima) -- voce
      LEU o numero, nao calculou ele. Se a planta tem um "Quadro de
      Areas" com area por comodo, isso conta como alta. Pra
      metros_parede, portas e janelas, "alta" significa que havia cota
      de comprimento/contagem explicita e inequivoca cobrindo tudo.
    - "media": PELO MENOS UM comodo que compoe essa soma NAO tinha area
      pronta, e voce teve que calcular multiplicando cotas lineares
      (metodo 3b), OU voce contou/mediu visualmente sem cota de texto
      (ex: contando arcos de porta, ou somando segmentos de parede a
      partir do desenho). Isso vale MESMO que voce tenha usado numeros
      reais da planta (cotas lineares) -- calcular a partir deles ainda
      e uma estimativa, nao uma leitura direta, entao NUNCA classifique
      como "alta" so porque usou algum numero da planta.
    - "baixa": a planta estava com baixa qualidade/resolucao, elementos
      sobrepostos, cortados, ou ambiguos nessa categoria especifica, e
      voce teve que chutar ou inferir sem base visual clara (isso
      inclui casos onde a classificacao seco/molhado/externo ou
      interna/externa de um elemento ficou incerta).
    Para cada campo, inclua tambem um "motivo" de no maximo 12 palavras
    explicando objetivamente o que embasou a confianca, e deixando
    claro se foi LEITURA direta ou CALCULO/estimativa (ex: "cota de
    area de 12m2 escrita no banheiro" para alta, ou "area calculada
    multiplicando cotas lineares de 3,85 x 2,70" para media).

    Retorne estritamente um JSON valido com a estrutura abaixo, sem
    textos adicionais, explicacoes ou marcacoes de markdown -- so o JSON:
    {
        "area_piso_seco": <float>,
        "area_piso_molhado": <float>,
        "area_piso_externo": <float>,
        "metros_parede": <float>,
        "portas_internas": <int>,
        "portas_externas": <int>,
        "janelas": <int>,
        "confianca": {
            "area_piso_seco": {"nivel": "alta|media|baixa", "motivo": "<string curta>"},
            "area_piso_molhado": {"nivel": "alta|media|baixa", "motivo": "<string curta>"},
            "area_piso_externo": {"nivel": "alta|media|baixa", "motivo": "<string curta>"},
            "metros_parede": {"nivel": "alta|media|baixa", "motivo": "<string curta>"},
            "portas_internas": {"nivel": "alta|media|baixa", "motivo": "<string curta>"},
            "portas_externas": {"nivel": "alta|media|baixa", "motivo": "<string curta>"},
            "janelas": {"nivel": "alta|media|baixa", "motivo": "<string curta>"}
        }
    }
    """


def _chamar_gemini_com_uma_chave(chave, prompt, img_base64):
    """Faz a chamada a API com UMA chave especifica, com ate 3
    tentativas em caso de erro temporario (503 UNAVAILABLE).

    Retorna (resultado_json, None) em caso de sucesso, ou
    (None, info_erro) em caso de falha -- onde info_erro e um dict com
    "status" (categoria do erro, ex: RESOURCE_EXHAUSTED) e "bruto"
    (resposta completa da API, pra diagnostico).
    """
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={chave}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": "image/jpeg", "data": img_base64}},
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    headers = {"Content-Type": "application/json"}

    max_tentativas = 3
    espera_segundos = 5

    for tentativa in range(1, max_tentativas + 1):
        try:
            resposta = requests.post(url, json=payload, headers=headers, timeout=60)
            resultado = resposta.json()
        except requests.exceptions.RequestException as e:
            # Falha de rede (timeout, DNS, conexao recusada etc.) --
            # antes isso propagava sem tratamento e derrubava toda a
            # extracao mesmo havendo outras chaves configuradas. Agora
            # trata como "erro nesta chave" e segue pra proxima tentativa
            # (ou proxima chave, se acabaram as tentativas aqui).
            if tentativa < max_tentativas:
                time.sleep(espera_segundos)
                continue
            return None, {"status": "ERRO_DE_REDE", "bruto": str(e)}
        except ValueError:
            # resposta.json() falhou -- corpo nao era JSON valido
            # (ex: erro HTML de proxy/gateway). Trata como falha desta
            # chave em vez de propagar exception nao tratada.
            if tentativa < max_tentativas:
                time.sleep(espera_segundos)
                continue
            return None, {"status": "RESPOSTA_INVALIDA", "bruto": resposta.text[:500] if 'resposta' in dir() else ""}

        if "candidates" in resultado:
            return resultado, None

        status_erro = resultado.get("error", {}).get("status", "")

        # 503 UNAVAILABLE ("alta demanda") e temporario -- vale tentar
        # de novo com a MESMA chave antes de considerar ela esgotada.
        if status_erro == "UNAVAILABLE" and tentativa < max_tentativas:
            time.sleep(espera_segundos)
            continue

        return None, {"status": status_erro, "bruto": resultado}

    return None, {"status": "UNAVAILABLE", "bruto": resultado}


def extrair_dados_da_planta(caminho_arquivo):
    # 1. Modo mock: nao gasta nenhuma chamada de API. Use para testar
    #    upload, calculo e geracao de excel sem tocar no Gemini.
    if MOCK_AI:
        return DADOS_MOCK

    # 2. Cache local: a mesma planta (mesmo arquivo) ja testada antes
    #    nao dispara uma nova chamada de API.
    if USE_CACHE:
        resultado_em_cache = cache.buscar_cache(caminho_arquivo)
        if resultado_em_cache is not None:
            return resultado_em_cache

    if not GEMINI_API_KEYS:
        raise ErroExtracaoAmigavel(
            "Nenhuma chave da API do Gemini está configurada. Defina "
            "GEMINI_API_KEY (ou GEMINI_API_KEYS, para várias chaves) no "
            "arquivo .env, ou ative MOCK_AI=true para testar a interface "
            "sem consumir a API."
        )

    img_bytes = _preparar_imagem(caminho_arquivo)
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    prompt = _montar_prompt()

    # Tenta cada chave da lista, em ordem. Se uma chave estourar cota
    # (RESOURCE_EXHAUSTED) ou tiver qualquer outro problema, passa pra
    # proxima automaticamente -- o usuario so ve erro se TODAS as
    # chaves configuradas falharem.
    erros_por_chave = []
    for indice, chave in enumerate(GEMINI_API_KEYS, start=1):
        resultado, erro = _chamar_gemini_com_uma_chave(chave, prompt, img_base64)

        if resultado is not None:
            break

        erros_por_chave.append(f"Chave {indice}: {erro['status'] or 'erro desconhecido'}")
        continue
    else:
        # Todas as chaves falharam. Monta uma mensagem amigavel,
        # priorizando a explicacao mais provavel (cota esgotada e o
        # caso mais comum em produção).
        algum_erro_de_cota = any("RESOURCE_EXHAUSTED" in e for e in erros_por_chave)
        if algum_erro_de_cota:
            mensagem = (
                "A cota de uso da IA foi atingida em todas as chaves configuradas "
                "no momento. Tente novamente em alguns minutos, ou adicione outra "
                "chave em GEMINI_API_KEYS no arquivo .env."
            )
        else:
            mensagem = (
                "Não foi possível analisar a planta agora — a IA não respondeu "
                "corretamente. Tente novamente em instantes; se o problema "
                "persistir, confira se a chave da API ainda é válida."
            )
        raise ErroExtracaoAmigavel(mensagem, detalhe_tecnico="; ".join(erros_por_chave))

    texto_resposta = resultado["candidates"][0]["content"]["parts"][0]["text"]
    texto_limpo = texto_resposta.replace("```json", "").replace("```", "").strip()

    try:
        dados = json.loads(texto_limpo)
    except json.JSONDecodeError as e:
        raise ErroExtracaoAmigavel(
            "A IA retornou uma resposta em formato inesperado ao analisar essa "
            "planta. Tente novamente — se persistir, tente com uma imagem de "
            "melhor qualidade ou outro arquivo.",
            detalhe_tecnico=f"JSONDecodeError: {e}. Texto bruto: {texto_resposta[:500]}",
        )

    # Defesa: garante que todos os 7 campos agregados existam, mesmo se
    # o modelo esquecer algum (preenche com 0). E se o bloco de
    # confianca inteiro faltar, preenche com "media" em vez de quebrar
    # a tela -- o indicador degrada graciosamente em vez de lancar
    # excecao.
    for campo in CAMPOS_AGREGADOS:
        dados.setdefault(campo, 0)

    if "confianca" not in dados:
        dados["confianca"] = {}
    for campo in CAMPOS_AGREGADOS:
        dados["confianca"].setdefault(
            campo, {"nivel": "media", "motivo": "Confiança não informada pela IA"}
        )

    if USE_CACHE:
        cache.salvar_cache(caminho_arquivo, dados)

    return dados
