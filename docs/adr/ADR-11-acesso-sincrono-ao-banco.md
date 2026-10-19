# ADR-11: Acesso síncrono ao banco de dados

- **Status:** Aceito
- **Data:** 2026-10-19

## Contexto

Esta decisão foi tomada no início da construção e registrada depois.

O FastAPI aceita rotas síncronas (`def`) e assíncronas (`async def`), e o SQLAlchemy oferece as duas formas de acesso ao banco. A escolha afeta todo o backend: rotas, services, repositórios e testes.

O que pesa na decisão:

- **Volume:** a meta é a fila responder em menos de 300 ms com até 100 incidentes ativos (RNF-04), com poucos analistas usando ao mesmo tempo. Não há milhares de conexões abertas.
- **Transações:** cada requisição é uma transação, e as alterações de incidentes dependem dela para o controle de concorrência (ADR-02) e a idempotência (ADR-08).
- **Trabalho de CPU:** o login calcula um hash bcrypt (ADR-03), que bloqueia enquanto roda, qualquer que seja o modelo.
- **Prazo curto**, com testes contra PostgreSQL real.

## Decisão

O backend é **síncrono**: rotas declaradas com `def`, `Session` síncrona do SQLAlchemy e o driver `psycopg` no modo síncrono.

- O FastAPI executa cada rota síncrona num pool de threads, então uma requisição esperando o banco não bloqueia as outras.
- Cada requisição recebe uma sessão com uma transação (`get_session`), confirmada antes de a resposta ser enviada.
- Uma consulta tem no máximo 5 segundos (`statement_timeout`), e a conexão, 5 segundos para abrir. Se o banco não responder, a API devolve 503 em vez de prender a thread indefinidamente.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| **SQLAlchemy assíncrono** (`AsyncSession` com `asyncpg` ou `psycopg` assíncrono) | Atende melhor milhares de requisições simultâneas, que este sistema não tem. Em troca, exige `await` em todas as camadas, impede o carregamento preguiçoso de relacionamentos (o acesso a um atributo não carregado vira erro) e complica os testes, que precisam de fixtures assíncronas e de cuidado com o loop de eventos. O bcrypt continuaria precisando de uma thread à parte. |

## Consequências

**Positivas**

- Código mais simples de ler e de testar: sem `await`, sem fixtures assíncronas, com transações explícitas.
- O bcrypt roda numa thread do pool, sem bloquear as outras requisições.
- Os tempos limite garantem que um banco lento vire 503 rapidamente, sem esgotar as threads.

**Negativas**

- A concorrência fica limitada pelo pool de threads do FastAPI (40 por padrão) e pelo pool de conexões do SQLAlchemy (5 mais 10 extras por padrão). É suficiente para o volume do MVP, mas não para milhares de usuários simultâneos.
- Cada requisição em espera ocupa uma thread, que consome mais memória que uma tarefa assíncrona.

**Evolução:** se o volume crescer, o primeiro passo é rodar mais processos do uvicorn e ajustar os pools, o que não muda o código. Migrar para o modelo assíncrono só compensa se o gargalo passar a ser o número de requisições esperando o banco ao mesmo tempo. Como as regras ficam no service e o acesso aos dados fica atrás da interface do repository (ADR-10), a migração mudaria a forma das chamadas (`async` e `await` nas rotas, nos services e nos repositórios), mas não as regras.
