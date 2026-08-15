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
# ---------------------------------------------------------------------
_TRES_PADROES_M2 = {"Econômico": "m2", "Médio": "m2", "Alto Padrão": "m2"}
_TRES_PADROES_UN = {"Econômico": "un", "Médio": "un", "Alto Padrão": "un"}

GRUPOS_POR_PADRAO: dict[str, dict[str, CodigoSinapi]] = {
    "piso_seco":                    _grupo(_TRES_PADROES_M2),
    "piso_molhado":                 _grupo(_TRES_PADROES_M2),
    "piso_externo":                 _grupo(_TRES_PADROES_M2),
    "porta_interna":                _grupo(_TRES_PADROES_UN),
    "porta_externa":                _grupo(_TRES_PADROES_UN),
    "janela":                       _grupo(_TRES_PADROES_UN),
    "ponto_eletrico_infra":         _grupo(_TRES_PADROES_UN),
    "ponto_eletrico_acabamento":    _grupo(_TRES_PADROES_UN),
    "ponto_hidraulico_infra":       _grupo(_TRES_PADROES_UN),
    "ponto_hidraulico_acabamento":  _grupo(_TRES_PADROES_UN),
}

# Cobertura tem uma camada extra (tipo x padrão): "cobertura_{tipo}__{padrao}"
COBERTURA: dict[str, dict[str, CodigoSinapi]] = {
    "cobertura_Telhado": _grupo(_TRES_PADROES_M2),
    "cobertura_Laje":    _grupo(_TRES_PADROES_M2),
}

# ---------------------------------------------------------------------
# 3. MÃO DE OBRA POR SERVIÇO -- prioridade alta pra preencher: hoje
# quase tudo aqui é estimativa ("não coletado item a item"), não
# SINAPI de verdade. Chave final: "mao_de_obra__{servico}".
# ---------------------------------------------------------------------
MAO_DE_OBRA: dict[str, CodigoSinapi] = {
    "Alvenaria (assentamento)":               CodigoSinapi(None, "composicao", "m2_parede"),
    # Já tem pista: composição 89290 citada em coeficientes.py --
    # confirmar e trazer pra cá. NOTA: se "bloco_ceramico" acima
    # (103361) for adotado como composição completa, este item de
    # mão de obra pode ficar redundante -- decidir um dos dois.
    "Assentamento de Piso (Área Seca)":       CodigoSinapi(None, "composicao", "m2_piso_seco"),
    "Assentamento de Piso (Área Molhada)":    CodigoSinapi(None, "composicao", "m2_piso_molhado"),
    "Assentamento de Piso (Área Externa)":    CodigoSinapi(None, "composicao", "m2_piso_externo"),
    "Pintura":                                CodigoSinapi(None, "composicao", "m2_parede"),
    "Instalação de Porta Interna":            CodigoSinapi(None, "composicao", "unidade"),
    "Instalação de Porta Externa":            CodigoSinapi(None, "composicao", "unidade"),
    "Instalação de Janela":                   CodigoSinapi(None, "composicao", "unidade"),
    "Execução de Cobertura":                  CodigoSinapi(None, "composicao", "m2_cobertura"),
    "Estrutura (fundação/armação)":           CodigoSinapi(None, "composicao", "m2_area"),
    "Instalação Elétrica":                    CodigoSinapi(None, "composicao", "unidade"),
    "Instalação Hidráulica":                  CodigoSinapi(None, "composicao", "unidade"),
}

# ---------------------------------------------------------------------
# 4. ITENS EXTRAS / AVULSOS -- espaço livre pra materiais e serviços
# que ainda NÃO existem no motor de cálculo (core/coeficientes.py),
# mas que fazem parte de uma obra real e podem ser úteis como linha
# avulsa no orçamento (ex: reboco, impermeabilização, forro de gesso,
# rejunte, portão, calçada, muro). Adicionar aqui não quebra nada --
# esses itens só passam a existir quando alguém também expõe a chave
# na tela (ver sugestão de integração no fim do arquivo).
#
# Formato: "chave_livre": (CodigoSinapi, "Rótulo pra exibir na tela")
# ---------------------------------------------------------------------
ITENS_EXTRAS: dict[str, tuple[CodigoSinapi, str]] = {
    # "reboco": (CodigoSinapi(None, "composicao", "m2"), "Reboco / chapisco"),
    # "impermeabilizacao": (CodigoSinapi(None, "composicao", "m2"), "Impermeabilização de laje/banheiro"),
    # "forro_gesso": (CodigoSinapi(None, "composicao", "m2"), "Forro de gesso"),
    # "rejunte": (CodigoSinapi(None, "insumo", "kg"), "Rejunte"),
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
