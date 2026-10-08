# OrçaObra AI — frontend

React 19 + Vite + TypeScript, com Tailwind, componentes shadcn/ui (Radix),
TanStack Query para as chamadas à API e Zustand para o estado da sessão.

## Comandos

```bash
npm ci           # instala dependências
npm run dev      # servidor de desenvolvimento em http://localhost:5173
npm run lint     # oxlint
npm run build    # checagem de tipos (tsc) + build de produção em dist/
```

Em desenvolvimento, `/api` é encaminhado para o backend em `http://localhost:8010`
(ver `vite.config.ts`). Em produção, o `dist/` é servido pela própria API
(`api/main.py`), na mesma origem.

## Estrutura

- `src/routes/`: telas (início/histórico, revisão dos dados extraídos, orçamento).
- `src/components/`: painéis da sidebar (planta, projeto, perfil, preços, SINAPI) e componentes de UI.
- `src/hooks/`: uma hook por recurso da API (TanStack Query).
- `src/lib/`: cliente HTTP (`api-client.ts`), stores Zustand e tipos espelhando `api/schemas.py`.

Como rodar o projeto inteiro e configurar as variáveis de ambiente: veja o `README.md` na raiz.
