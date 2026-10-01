# OrçaObra AI

Orçamento de obra residencial a partir de uma planta baixa: a IA (Gemini)
extrai áreas, metros de parede e aberturas, o profissional revisa e o sistema
calcula materiais e mão de obra com preços SINAPI/RR, gerando Excel (uso
interno) e PDF (proposta ao cliente).

- **Backend:** FastAPI (`api/`) sobre a lógica de negócio em `core/`, Postgres (Neon) para histórico, perfil e monitor de cota.
- **Frontend:** React + Vite + TypeScript (`frontend/`). Em produção, o build é servido pela própria API.
- **Deploy:** Render, configurado em `render.yaml`.

## Rodando localmente

Requisitos: Python 3.11+ e Node 20+.

### Backend

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-api.txt -r requirements-dev.txt
cp .env.example .env                 # preencha as variáveis (ver abaixo)
uvicorn api.main:app --reload --port 8010
```

### Frontend

```bash
cd frontend
npm ci
npm run dev                          # http://localhost:5173
```

O Vite faz proxy de `/api` para `http://localhost:8010` (ver `frontend/vite.config.ts`).

## Variáveis de ambiente

Todas estão documentadas em `.env.example`.

| Variável | Para quê |
|---|---|
| `GEMINI_API_KEY` / `GEMINI_API_KEYS` | Chave(s) da API do Gemini. Várias chaves separadas por vírgula são tentadas em ordem quando a cota acaba. |
| `GEMINI_MODEL` | Modelo usado na leitura das plantas. |
| `MOCK_AI` | `true` devolve dados fixos, sem chamar a API. |
| `USE_CACHE` | `true` reaproveita a resposta da IA para a mesma planta, modelo e prompt. |
| `GEMINI_DAILY_LIMIT` | Limite diário usado no alerta de cota. |
| `DATABASE_URL` | Postgres (Neon). Sem ele, histórico e monitor não funcionam; perfil e logo usam arquivos locais. |
| `APP_USER` / `APP_PASSWORD` | Login HTTP Basic de todo o app. Sem eles, a API responde 503. |
| `AUTH_DISABLED` | `true` desliga o login. Só para desenvolvimento e testes. |

## Testes e verificação

```bash
# backend (sem chamar a IA, sem cache, sem login)
MOCK_AI=true USE_CACHE=false AUTH_DISABLED=true pytest
ruff check .

# frontend
cd frontend
npm run lint
npm run build
```

No PowerShell, defina as variáveis antes: `$env:MOCK_AI="true"; $env:USE_CACHE="false"; $env:AUTH_DISABLED="true"; pytest`.

Os testes não acessam o banco nem a API do Gemini. A CI (`.github/workflows/ci.yml`) roda os mesmos passos.

## Mais documentação

- `docs/README_sinapi_import.md`: importação dos preços oficiais do SINAPI.
- `docs/validacao_e2e_orcaobra.md`: roteiro de validação ponta a ponta.
