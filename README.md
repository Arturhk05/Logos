# Logos

Central de resposta a incidentes para uma operação de logística. Motoristas reportam pelo celular o que acontece na estrada (acidentes, bloqueios, problemas mecânicos), e a central organiza, investiga e encerra cada ocorrência, sempre começando pelas mais críticas.

| Link | |
|---|---|
| Aplicação | https://logos.arturkrauspenhar.com.br |
| Vídeo de demonstração | _(link do vídeo)_ |
| Documentação da API (Swagger) | https://logos.arturkrauspenhar.com.br/api/docs |

## Como usar

Todos os usuários de demonstração usam a senha `logos123`, que também aparece na tela de login.

| Usuário | Papel | O que faz |
|---|---|---|
| `jose` | Motorista | Reporta incidentes (com a criticidade sugerida pela categoria) e acompanha o status dos próprios reportes. Telas pensadas para celular. |
| `camila`, `lucas` | Analista | Vê a fila de incidentes ativos, priorizada por criticidade e com filtros, assume um incidente e o leva até o encerramento. Com os dois, dá para ver a disputa pelo mesmo incidente. |
| `roberto` | Supervisor | Tudo o que o analista faz, e também altera incidentes assumidos por outras pessoas. |

Os analistas e o supervisor também consultam o histórico paginado dos incidentes encerrados. A base de demonstração tem 140 incidentes: 100 ativos na fila e 40 no histórico.

## Como rodar localmente

Pré-requisito: [Docker](https://docs.docker.com/get-docker/). Na raiz do repositório:

```bash
docker compose up -d --build   # aplicação em http://localhost:8080
docker compose down            # para tudo, mantendo os dados (com -v, apaga os dados)
```

O `docker compose` sobe, nesta ordem, o PostgreSQL, as migrations com os dados de demonstração, a API e a interface. A interface roda como em produção: o build do React servido por um nginx, que repassa `/api` para a API no mesmo endereço, então o login funciona sem configuração extra. Use Chrome ou Firefox: o Safari não aceita o cookie seguro em `http://localhost`.

Para desenvolver com recarga automática, rodar os testes e as verificações de código, veja o [`backend/README.md`](backend/README.md) e o [`frontend/README.md`](frontend/README.md).

## Arquitetura

```
                 ┌──────────────── CloudFront (HTTPS) ────────────────┐
 usuário ──────► │  /*      → S3 (build do React)                     │
                 │  /api/*  → EC2 (container FastAPI)                 │
                 └────────────────────────────────────────────────────┘
                                         │
                                         ▼
                           RDS PostgreSQL (subnet privada)
```

A interface e a API ficam no mesmo domínio, atrás do CloudFront, então a sessão é um cookie `httpOnly` e `SameSite=Strict` e não há CORS. O deploy é feito pelo GitHub Actions, autenticado na AWS por OIDC, sem nenhuma chave guardada no repositório. O passo a passo da infraestrutura, incluindo como removê-la, está em [`docs/deploy.md`](docs/deploy.md).

**Backend.** O código é organizado por área do negócio (`auth`, `incidents`, `users`), não por camada técnica. Dentro de cada área, as regras de negócio ficam só no `service`, e o `repository` só acessa dados. Os services dependem de uma interface do repository, o que permite testar as regras sem banco.

**Frontend.** Também organizado por área (`features/queue`, `features/driver`...). As chamadas à API passam por um único cliente, com tipos gerados a partir do contrato OpenAPI, tempo limite e erros já traduzidos em mensagens para o usuário. Cada tela trata os estados de carregando, erro e vazio.

### Decisões principais

| Tema | Decisão | ADR |
|---|---|---|
| Stack e hospedagem | FastAPI, PostgreSQL e React na AWS, com CloudFront como ponto único de entrada | [ADR-01](docs/adr/ADR-01-stack-tecnologica.md) |
| Dois analistas no mesmo incidente | Controle de concorrência otimista: uma alteração sobre uma versão antiga recebe 409 com o estado atual, e a tela mostra a versão nova sem perder o que foi preenchido | [ADR-02](docs/adr/ADR-02-controle-de-concorrencia.md) |
| Segurança da API | Login com JWT em cookie `httpOnly`, papéis por usuário, senhas com hash bcrypt | [ADR-03](docs/adr/ADR-03-autenticacao-e-papeis.md) |
| Permissões | Regras que dependem só do papel ficam na rota; as que dependem do incidente (quem assumiu, quem reportou), no service | [ADR-06](docs/adr/ADR-06-verificacao-de-permissoes.md) |
| Ciclo de vida | _Fechado_ e _Inconclusivo_ são estados finais: um incidente encerrado não é reaberto, e o histórico não muda | [ADR-05](docs/adr/ADR-05-estados-finais.md) |
| Reporte com sinal instável | Chave de idempotência: "tentar novamente" nunca cria um incidente duplicado | [ADR-08](docs/adr/ADR-08-idempotencia-do-reporte.md) |
| Rotas do React | Uma CloudFront Function entrega o `index.html` nas rotas da interface sem alterar as respostas da API | [ADR-09](docs/adr/ADR-09-rotas-do-frontend-no-cloudfront.md) |
| Trecho CloudFront → API | HTTP, com a EC2 aceitando conexões só do CloudFront | [ADR-07](docs/adr/ADR-07-http-entre-cloudfront-e-api.md) |
| Rate limit | Retirado do escopo do MVP; a decisão fica registrada para depois | [ADR-04](docs/adr/ADR-04-rate-limit.md) |

### Bibliotecas

| Parte | Biblioteca | Por quê |
|---|---|---|
| API | **FastAPI** + **Pydantic** | Validação de todas as entradas (dado inválido vira 422, nunca 500) e documentação OpenAPI gerada |
| | **SQLAlchemy** + **Alembic** | `UPDATE` condicional para o controle de concorrência e migrations versionadas |
| | **PostgreSQL** | Transações e garantias de concorrência confiáveis |
| | **pytest** + **testcontainers** | Testes de integração contra um PostgreSQL real e descartável |
| | **uv**, **ruff**, **mypy** (strict) | Dependências reproduzíveis, lint com regras de segurança e checagem de tipos |
| Interface | **React** + **Vite** + **TypeScript** | Exigência do desafio, com build rápido e contratos tipados com a API |
| | **TanStack Query** | Cache, novas tentativas só em falhas temporárias e estados de carregando e erro |
| | **React Router** | Rotas por papel e filtros na URL, que sobrevivem a recarregar a página |
| | **Tailwind CSS** | Consistência visual e tema claro/escuro |
| | **openapi-typescript** + **openapi-fetch** | Tipos gerados do contrato da API: uma mudança na API que quebre a interface falha no CI |
| | **Vitest** + **MSW** | Testes das telas e das chamadas à API sem um servidor real |

## Qualidade

- **Testes:** no backend, unitários (regras de negócio com repositórios em memória), de integração (repositórios, migrations e concorrência no PostgreSQL) e de API (do HTTP ao banco). No frontend, a lógica de cada tela e cada estado da interface.
- **CI** ([`ci.yml`](.github/workflows/ci.yml)): a cada push no `dev` e em cada pull request, lint, formatação, tipos e testes do backend e do frontend, o build e a conferência de que o contrato da API e os tipos gerados estão em dia.
- **Deploy** ([`deploy-backend.yml`](.github/workflows/deploy-backend.yml) e [`deploy-frontend.yml`](.github/workflows/deploy-frontend.yml)): a cada push na `main` que altere o backend ou o frontend, repete as verificações daquela parte e só publica se todas passarem.

## Estrutura do repositório

| Pasta | Conteúdo |
|---|---|
| [`backend/`](backend/README.md) | API em Python (FastAPI) |
| [`frontend/`](frontend/README.md) | Interface em React |
| [`docs/`](docs/) | [Desafio](docs/desafio.md), [requisitos](docs/requisitos.md) (personas, regras de negócio e histórias de usuário), [ADRs](docs/adr/) e [deploy](docs/deploy.md) |
| [`infra/`](infra/) | Configurações da AWS usadas no deploy |
| [`.github/workflows/`](.github/workflows/) | CI e deploy |

**Uso de IA:** o desenvolvimento contou com um assistente de IA (_Claude Code_) como par de programação, para discutir alternativas, revisar código e gerar testes. As decisões de produto e de arquitetura foram minhas e estão registradas nas ADRs. O `AGENTS.md` descreve as convenções do projeto para essas ferramentas.
