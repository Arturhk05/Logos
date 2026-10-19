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

## Comunicação com a API

- Em desenvolvimento, o Vite repassa as chamadas a `/api` para `http://localhost:8000`. Assim, a interface e a API ficam na mesma origem, como em produção, e o cookie de sessão funciona sem configuração extra. Use Chrome ou Firefox: o Safari não aceita o cookie seguro em `http://localhost`.
- Os tipos de `src/api/schema.d.ts` são gerados a partir do contrato da API (`openapi.json`). Quando a API mudar, exporte o contrato no backend (`uv run python -m scripts.export_openapi`) e rode `npm run gen:api`.
- `src/api/client.ts` faz as chamadas e transforma qualquer falha em um `ApiError`, com uma mensagem pronta para o usuário.
- `src/api/query-client.ts` define quando uma leitura é repetida: só em falhas temporárias (sem conexão, servidor indisponível, limite de requisições), até 3 vezes e com espera crescente. Alterações nunca são repetidas automaticamente.
