# Logos Web

Interface da plataforma Logos, construída com React, TypeScript e Vite.

## Pré-requisitos

- [Node.js](https://nodejs.org/) 24 LTS (versão em `.nvmrc`)
- A API rodando em `http://localhost:8000` (veja `backend/README.md`)

## Comandos

Execute a partir de `frontend/`:

| Comando                | O que faz                                       |
| ---------------------- | ----------------------------------------------- |
| `npm install`          | Instala as dependências                         |
| `npm run dev`          | Inicia a interface em http://localhost:5173     |
| `npm test`             | Executa os testes                               |
| `npm run test:watch`   | Executa os testes a cada alteração              |
| `npm run lint`         | Verifica o código com o ESLint                  |
| `npm run format`       | Formata o código com o Prettier                 |
| `npm run format:check` | Verifica a formatação, sem alterar os arquivos  |
| `npm run typecheck`    | Verifica os tipos                               |
| `npm run build`        | Gera a versão de produção em `dist/`            |
| `npm run gen:api`      | Gera os tipos da API a partir de `openapi.json` |

## Estrutura

O código é organizado por funcionalidade, como no backend:

```
src/
├── api/        # cliente HTTP, erros tipados e tipos gerados do contrato da API
├── app/        # rotas, sessão e barras de navegação
├── features/   # uma pasta por área: login, fila, incidentes, histórico, motorista
├── shared/     # rótulos, formatação e componentes usados por mais de uma tela (shared/ui)
└── test/       # MSW e utilitários de teste
```

As cores ficam como variáveis em `src/index.css` (`bg-surface`, `text-ink`, `bg-critical`...). O vermelho (`critical`) é reservado à criticidade Alta, e a criticidade sempre aparece com ícone e texto.

## Testes de tela

Os testes rodam no ambiente `node` do Vitest, sem um DOM simulado: o `fetch` do Node recusa o `AbortSignal` do `jsdom`, que o cliente usa para os tempos limite. Por isso cada tela separa:

- a lógica (filtros, ações permitidas, validação) e as chamadas à API, em arquivos `.ts`, testados com MSW;
- a visualização (`*View.tsx`), que só recebe props e é testada em cada estado (carregando, erro, vazio, com dados) com `renderView` de `src/test/render.tsx`.

Cliques, foco e a tecla Esc são conferidos no navegador.

## Comunicação com a API

- Em desenvolvimento, o Vite repassa as chamadas a `/api` para `http://localhost:8000`. Assim, a interface e a API ficam na mesma origem, como em produção, e o cookie de sessão funciona sem configuração extra. Use Chrome ou Firefox: o Safari não aceita o cookie seguro em `http://localhost`.
- Os tipos de `src/api/schema.d.ts` são gerados a partir do contrato da API (`openapi.json`). Quando a API mudar, exporte o contrato no backend (`uv run python -m scripts.export_openapi`) e rode `npm run gen:api`.
- `src/api/client.ts` faz as chamadas e transforma qualquer falha em um `ApiError`, com uma mensagem pronta para o usuário.
- `src/api/query-client.ts` define quando uma leitura é repetida: só em falhas temporárias (sem conexão, servidor indisponível, limite de requisições), até 3 vezes e com espera crescente. Alterações nunca são repetidas automaticamente.

## Executar com Docker

O `docker compose up -d --build`, na raiz do repositório, sobe banco, API e interface em http://localhost:8080, sem precisar do Node instalado. A imagem gera o mesmo build da produção e o serve com nginx ([`nginx.conf`](nginx.conf)), que faz o papel do CloudFront: repassa `/api` para a API e responde as rotas do React com o `index.html` (ADR-09). Para desenvolver, com recarga automática, use `npm run dev`.

## Deploy

Um push na `main` que altere `frontend/` publica a interface pelo workflow [`deploy-frontend.yml`](../.github/workflows/deploy-frontend.yml): as mesmas verificações do CI, o build enviado ao S3 e a invalidação do cache do CloudFront. Os passos e a configuração da AWS estão em [`docs/deploy.md`](../docs/deploy.md), e a forma como o CloudFront entrega as rotas do React, sem alterar as respostas da API, na [ADR-09](../docs/adr/ADR-09-rotas-do-frontend-no-cloudfront.md).
