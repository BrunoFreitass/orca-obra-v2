"""
Mapeamento entre as chaves internas do OrçaObra (as mesmas usadas em
core/tabela_precos.py._itens_editaveis()) e os códigos oficiais do
SINAPI (CAIXA/IBGE) para cada insumo/composição.

POR QUE ISSO PRECISA SER PREENCHIDO À MÃO (uma única vez):
Não existe correspondência automática confiável entre "cimento" e o
código SINAPI certo — a mesma palavra aparece em dezenas de insumos e
composições diferentes. Errar o código aqui significa alimentar o
motor de cálculo com o preço errado, silenciosamente. Por isso o
código é escolhido uma vez por um humano e depois nunca muda — só o
PREÇO daquele código muda mês a mês, e isso o importador resolve
sozinho.

COMO ACHAR O CÓDIGO CERTO (leva algumas horas pra tabela toda -- pode
ser feito aos poucos, item por item, sem pressa):
1. Baixe o ZIP mais recente do SINAPI para Roraima em:
   https://www.caixa.gov.br/poder-publico/modernizacao-gestao/sinapi/Paginas/default.aspx
   -> "Preços de Insumos e Composições" -> RR -> mês mais recente ->
   versão "Não Desonerado"
2. Para MATERIAIS SIMPLES (cimento, areia, brita...): abra o
   relatório de Insumos (ISD) e procure o insumo puro.
3. Para ITENS POR PADRÃO DE ACABAMENTO E MÃO DE OBRA: prefira o
   relatório de Composições Sintéticas (CSD) -- já vem com
   produtividade e mão de obra embutidas, então usar a composição
   certa aqui pode SUBSTITUIR a estimativa manual que hoje existe em
   MAO_DE_OBRA_POR_SERVICO (core/coeficientes.py), em vez de só
   atualizar o número.
4. Confira se a unidade do código bate com `unidade_esperada` abaixo
   antes de aceitar o valor.
5. Rode core/sinapi_import.py para conferir o resumo antes de gravar
   de vez.

ATENÇÃO -- SINAPI nem sempre tem equivalente exato: para itens de
acabamento/design (ex: "porcelanato importado alto padrão", "janela
com vidro duplo premium") o SINAPI raramente tem uma composição que
capture a diferença de padrão -- ele tende a ter só uma faixa
"comum"/"popular". Nesses casos, é normal e correto manter a
pesquisa de mercado como fonte (como já está hoje) em vez de forçar
um código que não representa o item real. Preencher só o que
realmente tiver um equivalente SINAPI de boa fé.

Itens ainda com codigo=None são ignorados pelo importador -- o motor
de cálculo continua usando o valor padrão de core/coeficientes.py (ou
um override manual) até que o código seja preenchido aqui.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CodigoSinapi:
    codigo: str | None      # código numérico do SINAPI, como string (ex: "94965")
    tipo: str                # "insumo" ou "composicao"
    unidade_esperada: str    # só pra checagem visual no resumo, não usado nos cálculos
    fator_conversao: float = 1.0  # multiplica o preço bruto do SINAPI antes de gravar --
    # necessário quando a unidade que o SINAPI coleta não bate com a unidade que o
    # OrçaObra usa (ex: SINAPI mede cimento "por kg", OrçaObra mede "por saco de
    # 50kg" -> fator_conversao=50). Deixe 1.0 quando as unidades já batem.


def _grupo(padroes: dict[str, str]) -> dict[str, CodigoSinapi]:
    """Gera as 3 chaves de um grupo por padrão de acabamento
    (Econômico/Médio/Alto Padrão) a partir de {padrao: unidade}."""
    return {
        padrao: CodigoSinapi(codigo=None, tipo="composicao", unidade_esperada=unidade)
        for padrao, unidade in padroes.items()
    }


# ---------------------------------------------------------------------
# 1. MATERIAIS SIMPLES (insumo puro -- olhar no relatório ISD)
# ---------------------------------------------------------------------
MATERIAIS_SIMPLES: dict[str, CodigoSinapi] = {
    # ATENÇÃO -- ver bloco de notas logo abaixo desta tabela antes de
    # confiar nestes 7 códigos em produção. Foram encontrados por
    # pesquisa (não extraídos diretamente da planilha oficial por
    # mim), então cada um deve ser conferido uma vez contra o arquivo
    # real antes do primeiro uso.
    "bloco_ceramico": CodigoSinapi("103361", "composicao", "m2"),
    # SINAPI 103361 -- "Alvenaria de vedação de blocos cerâmicos
    # furados na horizontal de 14x19x29cm (espessura 14cm), argamassa
    # de assentamento com preparo manual" -- bate com a dimensão
    # 14x19x29 já usada no rótulo do item (ver nota 1 abaixo: ISSO
    # RESOLVE a dúvida de typo que havia). ATENÇÃO: é uma COMPOSIÇÃO
    # (m2 de parede pronta, já com argamassa e mão de obra), não um
    # insumo puro de bloco -- se usar este código, o item deixa de
    # precisar de CONSUMO_TIJOLO_POR_M2_PAREDE em coeficientes.py
    # separado, porque a mão de obra de assentamento já vem embutida.
    "argamassa":      CodigoSinapi("34353", "insumo", "kg"),
    # "Argamassa Colante AC II" -- confiança alta
    "tinta":          CodigoSinapi("7356",  "insumo", "l"),
    # "Tinta Látex Acrílica Premium, cor branco fosco" -- confiança alta
    "cimento":        CodigoSinapi("1379", "insumo", "kg", fator_conversao=50),
    # SINAPI 1379 -- "Cimento Portland Composto CP II-32", medido por
    # KG (fator_conversao=50 converte pra preço por saco de 50kg
    # automaticamente). Confirmado por 2 fontes independentes.
    "areia":          CodigoSinapi("370",   "insumo", "m3"),
    # "Areia média - posto jazida/fornecedor" -- confiança alta
    # (preço de RR já visto: R$68,33/m³)
    "brita":          CodigoSinapi("4721",  "insumo", "m3"),
    # "Pedra britada n. 1 (9,5 a 19mm) posto pedreira/fornecedor" -- confiança alta
    "aco":            CodigoSinapi("32",    "insumo", "kg"),
    # "Aço CA-50, 6,3mm, vergalhão" -- já era a fonte citada em
    # coeficientes.py (PRECO_ACO_RR), agora confirmado por fonte independente

    # ---- Ativados a partir de ITENS_EXTRAS (ver secao 4 abaixo) ----
    # Conferidos em 2026-09 contra o arquivo oficial da Caixa (pacote
    # SINAPI_Referência, ref. 2026-07, coluna RR).
    "reboco":            CodigoSinapi(None, "composicao", "m2"),
    # SINAPI nao tem um codigo unico "reboco completo": e sempre 2
    # composicoes separadas (chapisco + emboco/massa unica), e
    # CodigoSinapi so guarda 1 codigo. Por isso continua None aqui --
    # o importador automatico nao consegue somar 2 codigos -- mas
    # PRECO_REBOCO_M2 em coeficientes.py ja foi atualizado A MAO com o
    # valor real somado: chapisco 87878 (R$6,81/m2) + emboço/massa
    # unica 87794 (R$53,28/m2), ambos "sem presença de vãos"/preparo
    # manual, RR, ref. 2026-07. Se algum dia o motor de calculo passar
    # a aceitar mais de 1 codigo por item, isso pode ser automatizado.
    "impermeabilizacao": CodigoSinapi("98555", "composicao", "m2"),
    # "Impermeabilização de superfície com argamassa polimérica/
    # membrana acrílica, 3 demãos" -- opção padrão mais comum pra área
    # molhada (banheiro/área de serviço). Existem alternativas mais
    # robustas (manta asfáltica, membrana de poliuretano) pra quem
    # quiser um padrão mais caro -- ver ITENS_EXTRAS/histórico de busca.
    "forro_gesso":       CodigoSinapi("96109", "composicao", "m2"),
    # "Forro em placas de gesso, para ambientes residenciais" -- match direto.
    "rejunte":           CodigoSinapi("34357", "insumo", "kg"),
    # "Rejunte cimentício, qualquer cor" -- match direto.
}

# ---------------------------------------------------------------------
# NOTAS IMPORTANTES sobre os códigos acima -- leia antes de usar
# ---------------------------------------------------------------------
# Estes códigos vieram de pesquisa em sites que reproduzem a base
# SINAPI (orcamentor.com, buscadorsinapi.com.br), NÃO de abrir o
# arquivo oficial da Caixa diretamente -- eu não tenho como baixar o
# ZIP daqui. São bons candidatos, com fonte cruzada em mais de um
# lugar, mas ainda merecem 1 conferência rápida (Ctrl+F pelo código na
# planilha baixada) antes do primeiro uso real.
#
# NOTA 1 -- bloco_ceramico RESOLVIDO: SINAPI 103361 cobre exatamente
# a dimensão 14x19x29cm que o projeto já usava no rótulo -- não era
# typo, é uma composição real (AF_12/2021). É uma COMPOSIÇÃO (m2 de
# parede pronta), não um insumo de bloco avulso -- ver comentário
# junto ao código acima sobre o impacto disso em coeficientes.py.
#
# NOTA 2 -- cimento RESOLVIDO: SINAPI 1379 ("Cimento Portland
# Composto CP II-32"), medido "por KG" -- o fator_conversao=50 já
# transforma isso em "preço por saco de 50kg" automaticamente, sem
# precisar mexer no importador.

# ---------------------------------------------------------------------
# 2. ITENS POR PADRÃO DE ACABAMENTO (Econômico / Médio / Alto Padrão)
# Chave final: "{prefixo}__{padrao}", igual ao usado em tabela_precos.py
#
# Os códigos preenchidos abaixo foram conferidos em 2026-08 contra o
# arquivo oficial da Caixa (pacote SINAPI_Referência, ref. 2026-07,
# coluna RR) -- preço e unidade batem com a planilha real, não só
# pesquisa em site terceiro (ver MATERIAIS_SIMPLES acima pro caso
# antigo). Onde não achei uma composição SINAPI que capture bem a
# diferença de padrão, ou a unidade não bate com o que o motor de
# cálculo usa hoje, o item ficou codigo=None de propósito -- forçar um
# código errado alimentaria o cálculo com preço errado silenciosamente
# (ver aviso no topo do arquivo). O motivo de cada None está comentado
# ao lado.
# ---------------------------------------------------------------------
_TRES_PADROES_M2 = {"Econômico": "m2", "Médio": "m2", "Alto Padrão": "m2"}
_TRES_PADROES_UN = {"Econômico": "un", "Médio": "un", "Alto Padrão": "un"}

GRUPOS_POR_PADRAO: dict[str, dict[str, CodigoSinapi]] = {
    # Revestimento cerâmico de piso, ambiente > 10m² -- tamanho de
    # cômodo mais comum (sala/quarto/cozinha) entre as faixas que o
    # SINAPI usa (< 5m² / 5-10m² / > 10m²).
    "piso_seco": {
        "Econômico":   CodigoSinapi("87248", "composicao", "m2"),
        # Revest. cerâmico esmaltado 35x35cm, ambiente >10m² -- R$69,52/m2 (RR, 2026-07)
        "Médio":       CodigoSinapi("87257", "composicao", "m2"),
        # Revest. cerâmico esmaltado 60x60cm, ambiente >10m² -- R$80,66/m2 (RR, 2026-07)
        "Alto Padrão": CodigoSinapi("87263", "composicao", "m2"),
        # Revest. cerâmico porcelanato 60x60cm, ambiente >10m² -- R$155,26/m2 (RR, 2026-07)
    },
    # Mesmas famílias do piso_seco, mas na faixa de ambiente < 5m² --
    # perfil típico de banheiro/área de serviço.
    "piso_molhado": {
        "Econômico":   CodigoSinapi("87246", "composicao", "m2"),
        # Revest. cerâmico esmaltado 35x35cm, ambiente <5m² -- R$88,98/m2 (RR, 2026-07)
        "Médio":       CodigoSinapi("87255", "composicao", "m2"),
        # Revest. cerâmico esmaltado 60x60cm, ambiente <5m² -- R$108,68/m2 (RR, 2026-07)
        "Alto Padrão": CodigoSinapi("87261", "composicao", "m2"),
        # Revest. cerâmico porcelanato 60x60cm, ambiente <5m² -- R$185,17/m2 (RR, 2026-07)
    },
    # Não achei, no relatório de RR, uma composição de piso de área
    # externa (antiderrapante/intertravado) com preço coletado -- as
    # únicas com "piso externo" na descrição eram sobre mobiliário
    # urbano ou pavimentação de rua, não bateram com o item real.
    "piso_externo": _grupo(_TRES_PADROES_M2),
    # Kits de porta de madeira (fornecimento + batente + instalação),
    # ~70cm de largura -- tamanho padrão de porta interna. O SINAPI já
    # rotula "Popular"/"Médio", batendo direto com os 2 primeiros
    # padrões daqui; Alto Padrão usa porta maciça (mais pesada/robusta,
    # com fechadura) em vez de semi-oca.
    "porta_interna": {
        "Econômico":   CodigoSinapi("91331", "composicao", "un"),
        # Kit porta semi-oca leve/média, padrão popular, 70x210cm, sem fechadura -- R$794,57 (RR, 2026-07)
        "Médio":       CodigoSinapi("90848", "composicao", "un"),
        # Kit porta semi-oca leve/média, padrão médio, 70x210cm, sem fechadura -- R$845,14 (RR, 2026-07)
        "Alto Padrão": CodigoSinapi("90846", "composicao", "un"),
        # Kit porta maciça (pesada/superpesada), padrão médio, 90x210cm, com fechadura -- R$1.335,80 (RR, 2026-07)
    },
    # Mesma família de kits de madeira pros 2 primeiros padrões (prática
    # comum -- porta externa residencial simples também costuma ser de
    # madeira); Alto Padrão troca pra porta de alumínio com vidro,
    # comum em entrada principal/varanda de padrão alto.
    "porta_externa": {
        "Econômico":   CodigoSinapi("91318", "composicao", "un"),
        # Kit porta semi-oca leve/média p/ pintura, padrão popular, 60x210cm, sem fechadura -- R$752,64 (RR, 2026-07)
        "Médio":       CodigoSinapi("90849", "composicao", "un"),
        # Kit porta semi-oca leve/média p/ pintura, padrão médio, 80x210cm, sem fechadura -- R$869,83 (RR, 2026-07)
        "Alto Padrão": CodigoSinapi("94805", "composicao", "un"),
        # Porta de alumínio de abrir p/ vidro, 87x210cm, com vidro -- R$919,79 (RR, 2026-07)
    },
    # SINAPI precifica janela por m² (varia com o tamanho real do vão),
    # mas o motor de cálculo hoje trata janela como unidade (contagem)
    # -- unidade incompatível, forçar um código aqui alimentaria o
    # cálculo com preço errado. Precisa decidir: ou o motor passa a
    # pedir m² por janela, ou o item continua pesquisa de mercado.
    "janela": _grupo(_TRES_PADROES_UN),
    # SINAPI só tem "ponto elétrico"/"ponto hidráulico" como componente
    # avulso de instalação (ex: caixa/suporte por altura de montagem --
    # alto/médio/baixo), não como pacote "infraestrutura completa" ou
    # "acabamento completo" por padrão de acabamento que dê pra separar
    # em Econômico/Médio/Alto Padrão.
    "ponto_eletrico_infra":        _grupo(_TRES_PADROES_UN),
    "ponto_eletrico_acabamento":   _grupo(_TRES_PADROES_UN),
    "ponto_hidraulico_infra":      _grupo(_TRES_PADROES_UN),
    "ponto_hidraulico_acabamento": _grupo(_TRES_PADROES_UN),
}

# Cobertura tem uma camada extra (tipo x padrão): "cobertura_{tipo}__{padrao}"
COBERTURA: dict[str, dict[str, CodigoSinapi]] = {
    "cobertura_Telhado": {
        "Econômico":   CodigoSinapi("94195", "composicao", "m2"),
        # Telhamento c/ telha cerâmica de encaixe tipo portuguesa, até 2 águas -- R$52,60/m2 (RR, 2026-07)
        "Médio":       CodigoSinapi("94207", "composicao", "m2"),
        # Telhamento c/ telha ondulada de fibrocimento e=6mm, até 2 águas -- R$84,72/m2 (RR, 2026-07)
        "Alto Padrão": CodigoSinapi("94216", "composicao", "m2"),
        # Telhamento c/ telha metálica termoacústica e=30mm, até 2 águas -- R$222,78/m2 (RR, 2026-07)
    },
    # Conferido em 2026-09: existe sim impermeabilização de superfície
    # coletada pra RR (aba ISD/CSD), 3 níveis de robustez plausíveis
    # pra usar como padrão Econômico/Médio/Alto:
    "cobertura_Laje": {
        "Econômico":   CodigoSinapi("98557", "composicao", "m2"),
        # "Impermeabilização de superfície com emulsão asfáltica, 2 demãos" -- R$45,83/m2 (RR, 2026-07)
        "Médio":       CodigoSinapi("98546", "composicao", "m2"),
        # "Impermeabilização de superfície com manta asfáltica, 1 camada, e=4mm" -- R$136,94/m2 (RR, 2026-07)
        "Alto Padrão": CodigoSinapi("98553", "composicao", "m2"),
        # "Impermeabilização de superfície com membrana à base de poliuretano, 2 demãos" -- R$190,94/m2 (RR, 2026-07)
    },
}

# ---------------------------------------------------------------------
# 3. MÃO DE OBRA POR SERVIÇO -- hoje quase tudo aqui é estimativa ("não
# coletado item a item"), não SINAPI de verdade. Chave final:
# "mao_de_obra__{servico}".
#
# DECISÃO (2026-08, princípio "só dado SINAPI, sem pesquisa de mercado
# paralela"): sempre que o material equivalente já é uma composição
# SINAPI completa (material + mão de obra embutidos -- confirmado
# contra o arquivo oficial, ex: "PINTURA LÁTEX ACRÍLICA PREMIUM,
# APLICAÇÃO MANUAL" já inclui a tinta), o item de mão de obra
# correspondente SOME daqui em vez de ficar com codigo=None -- ver
# core/calculator.py:calcular_mao_de_obra() pra onde isso é aplicado.
# Manter os dois (preço do material via SINAPI completo + estimativa de
# mão de obra em paralelo) duplicaria o custo. Removidos por esse
# motivo: "Alvenaria (assentamento)" (coberto por bloco_ceramico,
# 103361), "Assentamento de Piso (Área Seca/Molhada)" (piso_seco/
# piso_molhado), "Instalação de Porta Interna/Externa" (porta_interna/
# porta_externa).
#
# Os itens abaixo continuam com codigo=None porque não há composição
# SINAPI com preço coletado pra RR que os cubra (ainda são
# estimativa/pesquisa de mercado, e por ora ficam assim -- decisão
# tomada em 2026-08: nenhum outro dado de terceiros até achar SINAPI
# real).
# ---------------------------------------------------------------------
MAO_DE_OBRA: dict[str, CodigoSinapi] = {
    "Assentamento de Piso (Área Externa)":    CodigoSinapi(None, "composicao", "m2_piso_externo"),
    "Pintura":                                CodigoSinapi(None, "composicao", "m2_parede"),
    "Instalação de Janela":                   CodigoSinapi(None, "composicao", "unidade"),
    "Execução de Cobertura":                  CodigoSinapi(None, "composicao", "m2_cobertura"),
    # Só ainda é usado pra cobertura_Laje (sem composição SINAPI) --
    # pra Telhado, cobertura_Telhado (94195/94207/94216) já cobre
    # material + mão de obra, então este item nem entra no cálculo
    # quando tipo_cobertura="Telhado" (ver calcular_mao_de_obra()).
    "Estrutura (fundação/armação)":           CodigoSinapi(None, "composicao", "m2_area"),
    "Instalação Elétrica":                    CodigoSinapi(None, "composicao", "unidade"),
    "Instalação Hidráulica":                  CodigoSinapi(None, "composicao", "unidade"),
}

# ---------------------------------------------------------------------
# 4. ITENS EXTRAS / AVULSOS -- espaço livre pra materiais e serviços
# que ainda NÃO existem no motor de cálculo (core/coeficientes.py),
# mas que fazem parte de uma obra real e podem ser úteis como linha
# avulsa no orçamento (ex: portão, muro, calçada). Adicionar aqui não
# quebra nada -- esses itens só passam a existir quando alguém também
# expõe a chave na tela (ver sugestão de integração no fim do arquivo).
#
# reboco, impermeabilizacao, forro_gesso e rejunte SAÍRAM daqui em
# 2026-09: já entram no motor de cálculo (MATERIAIS_SIMPLES acima +
# core/calculator.py:calcular_materiais()), porque dá pra derivar a
# quantidade deles direto de DadosExtracao (area_parede/area_piso_*)
# sem precisar de nenhum campo novo de extração. muro e calcada
# continuam de fora: dependem do perímetro do lote, que a planta
# baixa normalmente não mostra e a extração da IA hoje não capta.
#
# Formato: "chave_livre": (CodigoSinapi, "Rótulo pra exibir na tela")
# ---------------------------------------------------------------------
ITENS_EXTRAS: dict[str, tuple[CodigoSinapi, str]] = {
    # "muro": (CodigoSinapi(None, "composicao", "m2"), "Muro de fechamento"),
    # "calcada": (CodigoSinapi(None, "composicao", "m2"), "Calçada externa"),
}


def todos_mapeamentos() -> dict[str, CodigoSinapi]:
    """Achata tudo (materiais simples + grupos por padrão + cobertura +
    mão de obra) num único dict {chave_final: CodigoSinapi}, no formato
    que core/sinapi_import.py espera. Itens_extras ficam de fora daqui
    de propósito -- eles seguem outro fluxo (ver comentário na seção 4)."""
    resultado: dict[str, CodigoSinapi] = dict(MATERIAIS_SIMPLES)

    for prefixo, grupo in GRUPOS_POR_PADRAO.items():
        for padrao, codigo in grupo.items():
            resultado[f"{prefixo}__{padrao}"] = codigo

    for prefixo, grupo in COBERTURA.items():
        for padrao, codigo in grupo.items():
            resultado[f"{prefixo}__{padrao}"] = codigo

    for servico, codigo in MAO_DE_OBRA.items():
        resultado[f"mao_de_obra__{servico}"] = codigo

    return resultado


# Nome usado por core/sinapi_import.py -- mantém compatibilidade com a
# primeira versão do importador.
MAPEAMENTO_SINAPI = todos_mapeamentos()

# Nome da coluna de preço no relatório oficial para o estado atendido
# pelo OrçaObra. A Caixa às vezes usa a sigla ("RR"), às vezes o nome
# por extenso ("Roraima") -- o importador tenta os dois.
UF_COLUNA_ALVOS = ("rr", "roraima")


# ---------------------------------------------------------------------
# Progresso de preenchimento (só informativo -- rode este arquivo
# diretamente pra ver quantos itens já têm código: `python -m
# core.sinapi_codigos`)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    total = len(MAPEAMENTO_SINAPI)
    preenchidos = sum(1 for c in MAPEAMENTO_SINAPI.values() if c.codigo is not None)
    print(f"{preenchidos}/{total} itens do motor de cálculo já têm código SINAPI mapeado.")
    print(f"{len(ITENS_EXTRAS)} item(ns) extra(s) cadastrados (fora do motor de cálculo hoje).")
    if preenchidos < total:
        print("\nFaltando:")
        for chave, codigo in MAPEAMENTO_SINAPI.items():
            if codigo.codigo is None:
                print(f"  - {chave} ({codigo.tipo}, {codigo.unidade_esperada})")
