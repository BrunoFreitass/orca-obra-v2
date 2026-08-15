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

1. Aplicar o patch em `core/tabela_precos.py` (ver `PATCH_tabela_precos.md`)
2. Preencher os códigos SINAPI reais em `sinapi_codigos.py` (uma vez
   só — os códigos não mudam mês a mês, só o preço)
3. Baixar um ZIP de teste da Caixa e rodar o importador pra conferir
   se os preços e descrições batem com o esperado antes de confiar
   nele em produção

## Limitações honestas desta primeira versão

- **Não baixa nada sozinho** (ver "por que" acima) — é um importador,
  não um scraper.
- **Não valida semanticamente** se um preço faz sentido — isso já é
  trabalho do `core/validacao.py` existente, que roda em cima de
  qualquer preço vigente.
- **Detecção de layout é por texto de cabeçalho, não posição fixa de
  coluna** — mais robusto a mudanças de leiaute da Caixa entre meses,
  mas ainda não testado contra um arquivo real (não tenho acesso pra
  baixar um agora). O primeiro teste real de vocês com o ZIP do mês
  vai revelar se algum ajuste fino é necessário.
- **Só cobre os itens que vocês mapearem em `sinapi_codigos.py`** —
  hoje isso são os ~7 materiais simples (cimento, areia, brita, aço,
  bloco cerâmico, argamassa, tinta); os itens por padrão de acabamento
  (piso, porta, janela, cobertura) e mão de obra ficam de fora até
  alguém mapear os códigos correspondentes.
