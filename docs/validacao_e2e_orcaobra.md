# Validação ponta a ponta — OrçaObra AI (persistência Postgres/Neon)

## Contexto

OrçaObra AI é um app que transforma plantas baixas em orçamentos de obra, usando
Gemini Vision pra extrair dados da planta e uma tabela de coeficientes/preços
pra calcular materiais e mão de obra.

- **Produção:** https://orcaobra-ia.onrender.com (Render, plano free — o primeiro
  request após um tempo ocioso pode levar até ~50s pra "acordar" o serviço).
- **Stack:** FastAPI (`api/main.py`) servindo tanto as rotas `/api/*` quanto o
  build estático do frontend React (`frontend/dist`) na mesma origem.
- **Banco:** Postgres via Neon, configurado em `DATABASE_URL` (env var no
  Render, não está no repo).
- **Repo:** `BrunoFreitass/orca-obra-v2`, branch `main`.

Numa sessão anterior de trabalho, o histórico de orçamentos e o monitor de
cota do Gemini foram migrados de SQLite local (que se perdia a cada redeploy,
porque o filesystem do Render free é efêmero) para esse Postgres. Vários bugs
reais só apareceram testando contra o banco de verdade e foram corrigidos:

- `GENERATED ALWAYS AS IDENTITY` sem tipo de coluna (sintaxe SQL inválida).
- `core/orcamento_service.py` chamando `salvar_orcamento()` com parâmetros que
  não existiam mais no novo schema (`caminho_excel`/`caminho_pdf` em vez de
  `orcamento_json`) — quebrava `POST /api/orcamento/gerar` com 500.
- `api/routers/historico.py` (download de Excel/PDF) lendo um caminho de
  arquivo em disco que não sobrevive a redeploy — reescrito pra regenerar o
  arquivo sob demanda a partir do `orcamento_json` salvo no banco.

Essa sessão já validou o fluxo ponta a ponta uma vez (via API e via frontend
real, com upload de planta e extração real pelo Gemini) e depois **apagou os
registros de teste** — o histórico de produção deveria estar vazio agora.

**Objetivo desta validação:** confirmar de forma independente que está tudo
funcionando (não confiar só no relato da sessão anterior) e cobrir os pontos
que ficaram sem testar.

---

## 1. Sanity check inicial

```bash
curl -s https://orcaobra-ia.onrender.com/api/health
# esperado: {"status":"ok"}

curl -s https://orcaobra-ia.onrender.com/api/historico
# esperado: [] (histórico limpo, sem lixo de teste)

curl -s https://orcaobra-ia.onrender.com/api/monitor/status
# esperado: JSON com "nivel", "total", "limite" etc. Anotar o "total" atual
# antes de rodar o teste de extração abaixo (pra confirmar que sobe +1 depois).
```

Se `/api/historico` não voltar `[]`, é possível que tenha sobrado lixo da
validação anterior — nesse caso, listar e decidir com o usuário se apaga
antes de prosseguir (não apagar nada sem confirmar, pode ser dado real).

## 2. Fluxo completo via API (materiais → mão de obra → gerar → histórico)

Rodar os 3 passos com valores de teste (`padrao` aceita `"Econômico"`,
`"Médio"` ou `"Alto Padrão"`; `estrutura`/`tipo_cobertura` aceita `"Telhado"`
ou `"Laje"` — **testar `"Laje"` aqui, que a sessão anterior não cobriu**):

```bash
BASE=https://orcaobra-ia.onrender.com

curl -s -X POST "$BASE/api/orcamento/materiais" -H "Content-Type: application/json" -d '{
  "area_piso_seco": 40, "area_piso_molhado": 8, "area_piso_externo": 6,
  "metros_parede": 60, "portas_internas": 3, "portas_externas": 1, "janelas": 4,
  "padrao": "Alto Padrão", "estrutura": "Laje"
}' > materiais.json

curl -s -X POST "$BASE/api/orcamento/mao-de-obra" -H "Content-Type: application/json" -d '{
  "area_piso_seco": 40, "area_piso_molhado": 8, "area_piso_externo": 6,
  "metros_parede": 60, "portas_internas": 3, "portas_externas": 1, "janelas": 4,
  "padrao": "Alto Padrão", "estrutura": "Laje"
}' > mao_de_obra.json

# Montar o payload de /gerar juntando materiais.json + mao_de_obra.json
# (ver core/api/schemas.py::OrcamentoGerarRequest) e então:

curl -s -X POST "$BASE/api/orcamento/gerar" -H "Content-Type: application/json" -d @gerar_req.json
# esperado: HTTP 200, JSON com custo_direto, preco_venda, historico_id (novo id)
```

**Critério de sucesso:** `HTTP 200`, não `500`. Anotar o `historico_id`
retornado — vai ser usado nos passos seguintes.

## 3. Histórico: listar, baixar, excluir

```bash
ID=<historico_id do passo 2>

curl -s "$BASE/api/historico" | grep "\"id\":$ID"
# esperado: o registro aparece na lista

curl -s -o /tmp/teste.xlsx -w "%{http_code}\n" "$BASE/api/historico/$ID/excel"
# esperado: 200, e o arquivo salvo deve começar com "PK" (assinatura zip/xlsx)
head -c 4 /tmp/teste.xlsx

curl -s -o /tmp/teste.pdf -w "%{http_code}\n" "$BASE/api/historico/$ID/pdf"
# esperado: 200, arquivo deve começar com "%PDF"
head -c 8 /tmp/teste.pdf

curl -s -o /dev/null -w "%{http_code}\n" -X DELETE "$BASE/api/historico/$ID"
# esperado: 204

curl -s "$BASE/api/historico"
# esperado: registro de teste não aparece mais
```

## 4. Monitor de cota

```bash
curl -s "$BASE/api/monitor/status"
# esperado: "total" maior que o valor anotado no passo 1 (se algum teste
# chamou a extração real via Gemini) -- confirma que o monitor está
# gravando no Postgres corretamente.
```

## 5. Frontend real (se a sessão tiver acesso a browser)

Se houver capacidade de automação de navegador, repetir o fluxo manual:

1. Abrir https://orcaobra-ia.onrender.com
2. Preencher "Nome do projeto" na barra lateral
3. Em "Planta Baixa", enviar uma imagem de planta (pode ser sintética, com
   um "quadro de áreas" legível — isso melhora a extração)
4. Clicar "Analisar Planta com IA" — aba Revisão deve mostrar os dados
   extraídos com um índice de confiança
5. "Confirmar Dados e Prosseguir" → aba Orçamento deve calcular materiais e
   mão de obra automaticamente
6. "Gerar Orçamento Completo" → deve aparecer "Orçamento gerado com sucesso!"
7. Aba Histórico → o projeto deve aparecer na tabela
8. Clicar no ícone de download (Excel) e no de excluir (lixeira) na tabela
   — **estes dois botões específicos não foram clicados na validação
   anterior**, só testados via curl.

Se não houver automação de navegador disponível, pular esta seção e reportar
que ficou sem cobertura (não simular/inventar um resultado).

## 6. Gaps conhecidos (não são bugs desta sessão, mas valem registrar)

Estes dois módulos **ainda não foram migrados** pro Postgres — continuam
gravando em arquivo local, que se perde a cada redeploy no Render free.
Não é escopo desta validação corrigir, só confirmar que o comportamento é
esse (grava, mas não sobrevive a um redeploy) e reportar:

- `core/perfil_empresa.py` (`PUT /api/perfil`, `POST /api/perfil/logo`) —
  grava em `perfil_empresa.json` local.
- `core/tabela_precos.py` (preços customizados, `POST /api/precos/aplicar`
  ou similar — conferir `api/routers/precos.py`) — grava em
  `precos_customizados.json` local.

## 7. Limpeza ao final

Se algum registro de teste novo foi criado no histórico de produção durante
essa validação e ainda não foi apagado no passo 3, apagar antes de encerrar
(`DELETE /api/historico/{id}`) e confirmar `GET /api/historico` → `[]`.

## 8. Relatório final esperado

Ao final, reportar em texto corrido (não precisa de outro arquivo):

- O que passou / o que falhou, com o código HTTP ou mensagem de erro exata
  de qualquer falha.
- Se algum passo não pôde ser executado (ex: sem acesso a browser), dizer
  isso explicitamente em vez de omitir.
- Confirmação final de que `/api/historico` voltou vazio.
