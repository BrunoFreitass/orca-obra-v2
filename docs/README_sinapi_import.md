# Importador SINAPI oficial — como funciona

## O que isso resolve

Hoje os preços em `core/coeficientes.py` são atualizados manualmente
(foi assim que vocês pegaram o cimento desatualizado). Este importador
automatiza a parte chata: ler a planilha oficial da Caixa e transformar
os códigos certos em preços atualizados no OrçaObra — sem digitar nada
a mão e sem depender de nenhuma API paga de terceiros.

## Por que o download continua manual

O portal da Caixa (`caixa.gov.br/poder-publico/.../sinapi`) bloqueia
acesso automatizado via `robots.txt`. Isso não significa que baixar o
arquivo seja proibido — é dado público, disponibilizado gratuitamente
pra download — só que fazer um robô visitar a página automaticamente
não é bem-vindo por eles. Por respeito a essa sinalização, o fluxo
proposto mantém esse passo manual: baixar o ZIP do mês (2 minutos,
uma vez por mês) e apontar o script pro arquivo extraído. Tudo depois
disso é automático.

Isso também evita depender de serviços terceiros pagos (tipo o
Buscador SINAPI que vocês usaram como referência) — cujo dado de base
é o mesmo da Caixa, só que reembalado e cobrado. Ir direto na fonte
oficial é grátis, legítimo e dá a vocês controle total sobre o
pipeline.

## Fluxo completo

```
1. [manual, 1x/mês]  Baixar o ZIP do SINAPI para RR no site da Caixa
2. [automático]      python -m core.sinapi_import arquivo1.xlsx arquivo2.xlsx
                      -> lê os códigos mapeados em sinapi_codigos.py
                      -> mostra resumo do que mudou
                      -> grava em precos_customizados.json (mesmo
                         mecanismo de override que já existe)
3. [automático]      O motor de cálculo (core/calculator.py via
                      core/tabela_precos.obter_preco()) já usa o
                      preço novo na próxima geração de orçamento --
                      nenhuma outra mudança de código necessária
```

## Antes de usar

1. Baixe o pacote mensal ("SINAPI_Referência") do site da Caixa pro
   estado atendido (hoje só RR) — dentro dele está o arquivo
   `.xlsx` que o comando abaixo espera.
2. Rode `python -m core.sinapi_import <arquivo.xlsx>` (use `--sim`
   pra gravar sem confirmação interativa, útil em automação).
3. Confira o resumo impresso — quantos itens foram atualizados, quais
   ficaram sem código mapeado, e qualquer aviso de unidade
   incompatível — antes de considerar o orçamento confiável pro mês.

Se algum item novo precisar de código (ex: um material que ainda não
existe em `sinapi_codigos.py`), preencha lá seguindo as instruções no
topo do próprio arquivo — é trabalho de pesquisa (achar o código
certo na planilha), não de programação.

## Estado atual (2026-09)

Testado de ponta a ponta contra o pacote real da Caixa (RR, ref.
2026-07): a detecção de layout funcionou sem ajuste, e **39 dos 55
itens do motor de cálculo já têm código SINAPI real** (rode
`python -m core.sinapi_codigos` pra ver o número atualizado e o que
falta). Isso cobre praticamente todas as categorias — materiais
simples (cimento, areia, brita, aço), pisos, portas, janela (por m²,
não por unidade — ver nota abaixo), cobertura (telhado e laje, com
estrutura da laje separada da impermeabilização), pintura, reboco,
impermeabilização, forro de gesso, rejunte e piso externo.

Rodar o importador contra o arquivo real corrigiu distorções grandes
que existiam nos preços "de pesquisa de mercado" que alimentavam o
motor de cálculo antes — o pior caso foi Porta Interna (Econômico),
que estava **395% abaixo** do valor real do SINAPI pra Roraima.

**O que ficou de fora, e por quê (não é falta de busca, é confirmado
contra o arquivo real):**
- **Mão de obra pra casa inteira** (Estrutura/fundação, Instalação
  Elétrica, Instalação Hidráulica): são estimativas de lump-sum pra
  obra toda, e o SINAPI só tem os insumos avulsos de mão de obra
  (ex: "ELETRICISTA HORISTA", R$/hora) — não uma composição pronta
  equivalente.
- **Pontos elétricos/hidráulicos por padrão de acabamento**: SINAPI só
  tem o suporte/placa avulso por altura de montagem, não um pacote
  "infraestrutura completa" ou "acabamento completo".
- **Muro e calçada**: calçada até tem composição limpa (94992/94993),
  mas nenhum dos dois tem fonte de quantidade em `DadosExtracao` — a
  planta baixa não mostra perímetro de lote nem área de calçada, e
  diferente de janela não dá pra assumir um tamanho médio razoável
  (lotes variam demais). Precisaria de um campo novo de extração ou
  input manual na tela, não só um código SINAPI (ver comentário na
  seção `ITENS_EXTRAS` de `sinapi_codigos.py`).

**Duas particularidades que valem saber antes de mexer:**
- **Janela** virou preço por m² (era por unidade) — SINAPI só
  precifica por área do vão, mas uma planta baixa não mostra a altura
  real de cada janela (só a largura), então a contagem que a IA
  extrai é convertida em área usando um tamanho médio fixo
  (`AREA_MEDIA_JANELA_M2` em `core/models.py`).
- **Reboco** não tem composição SINAPI única — é sempre chapisco +
  emboço em separado. Como `CodigoSinapi` só guarda 1 código, esse
  item ficou com `codigo=None` de propósito, mas o preço padrão em
  `coeficientes.py` foi atualizado à mão com a soma dos 2 códigos
  reais (não vai se beneficiar de atualização automática mês a mês
  até o importador ganhar suporte a múltiplos códigos por item).

## Limitações honestas

- **Não baixa nada sozinho** (ver "por que" acima) — é um importador,
  não um scraper.
- **Não valida semanticamente** se um preço faz sentido — isso já é
  trabalho do `core/validacao.py` existente, que roda em cima de
  qualquer preço vigente.
- **Detecção de layout é por texto de cabeçalho, não posição fixa de
  coluna** — mais robusto a mudanças de leiaute da Caixa entre meses,
  mas só foi validado contra o pacote de 2026-07 até agora.
- **(Resolvido em 2026-09) Rodar a suíte de testes apagava/sobrescrevia
  `precos_customizados.json` de verdade sem avisar** — vários testes
  chamavam `restaurar_padroes()`/`salvar_overrides()` direto no
  arquivo real. `tests/conftest.py` agora isola cada teste num arquivo
  temporário; rodar `pytest` depois de importar preços é seguro hoje.
