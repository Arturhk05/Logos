# ADR-10: Organização do backend em módulos e camadas

- **Status:** Aceito
- **Data:** 2026-10-19

## Contexto

Esta decisão foi tomada no início da construção e registrada depois, quando a estrutura já tinha se mostrado estável.

A API tem poucas áreas de negócio (autenticação, usuários, incidentes), mas regras com muitos detalhes: transições de status (ADR-05), permissões que dependem de quem assumiu ou reportou o incidente (ADR-06), controle de concorrência (ADR-02) e idempotência (ADR-08). Essas regras precisam ser fáceis de achar, de ler e de testar, e o desafio avalia a organização do repositório.

Duas perguntas definem a estrutura:

- **Como agrupar os arquivos:** por área de negócio ou por tipo técnico (todas as rotas juntas, todos os modelos juntos).
- **Onde ficam as regras de negócio:** nas rotas, nos modelos, no banco ou numa camada própria.

## Decisão

### Módulos por área de negócio

O código fica em `app/modules/<área>/`, e cada módulo reúne tudo daquela área. `app/shared/` guarda o que não pertence a nenhuma área: configuração, sessão do banco, erros de domínio e o tratamento desses erros na API.

Um módulo pode importar de `shared` e de outros módulos (`incidents` usa `users`), mas `shared` nunca importa de um módulo.

Os arquivos de um módulo são criados conforme a necessidade: `health` só tem `router.py`, e `users` não tem rotas próprias.

### Camadas dentro do módulo

| Arquivo | Responsabilidade |
|---|---|
| `router.py` | Recebe a requisição, valida a entrada com os schemas, verifica o papel (ADR-06) e chama o service. Não decide nada sobre o negócio. |
| `service.py` | **Todas as regras de negócio:** transições permitidas, quem pode alterar o quê, motivo obrigatório ao encerrar, criticidade travada em Alta para acidente com vítimas. Lança os erros de `app.shared.errors`, que a API traduz em 404, 403, 422 e 409. |
| `repository.py` | Só acesso a dados: buscar, inserir, atualizar com verificação de versão. Nenhuma regra. |
| `models.py` | Tabelas do banco (SQLAlchemy). |
| `enums.py` | Valores do domínio e propriedades intrínsecas deles (por exemplo, a prioridade de cada criticidade). |
| `schemas.py` | Entrada e saída da API (Pydantic). As respostas nunca expõem modelos do ORM, que vazariam campos como `password_hash`. |

O repository é declarado como uma interface (`Protocol`) e implementado com SQLAlchemy. O service depende da interface, e a implementação é montada em `dependencies.py`, pela injeção de dependências do FastAPI. Nos testes unitários, o service recebe repositórios em memória (`tests/fakes.py`) e as regras são testadas sem banco e sem HTTP.

### O banco só valida valores

O banco garante que cada coluna tenha um valor válido, mas não aplica regras de negócio:

- As colunas de enum (status, criticidade, categoria, papel) são `VARCHAR` com uma restrição `CHECK` que aceita só os valores do enum (`enum_check` em `app/shared/db/constraints.py`). Não é usado o tipo `ENUM` nativo do PostgreSQL.
- Regras como "um incidente fechado não muda de status" ou "só quem assumiu pode alterar" ficam apenas no service, nunca em `CHECK` ou triggers.

A exceção são as restrições que garantem integridade sob concorrência, que só o banco consegue garantir: a verificação de versão no `UPDATE` (ADR-02) e a unicidade da chave de idempotência (ADR-08). Elas são o mecanismo que torna as regras seguras, e não uma segunda cópia delas.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| **Organização por camada técnica** (`routers/`, `models/`, `services/` na raiz) | Espalha cada área por várias pastas: entender os incidentes exige abrir quatro diretórios, e nada indica quais arquivos mudam juntos. |
| **Regras nas rotas, sem service** | Menos arquivos, mas as regras ficam misturadas com HTTP e só podem ser testadas fazendo requisições. As permissões que dependem dos dados acabariam repetidas em cada rota. |
| **Service usando a sessão do SQLAlchemy direto, sem repository** | Menos uma camada, mas todo teste de regra passaria a precisar de banco. Com a interface, os testes unitários rodam em milissegundos e sem Docker. |
| **Arquitetura hexagonal completa** (entidades de domínio separadas dos modelos do ORM, portas e adaptadores para tudo) | Isola o domínio por completo, mas exige converter entre entidades e modelos em cada operação. Para três áreas de negócio, o custo é maior que o benefício. Aqui o service usa os próprios modelos do SQLAlchemy. |
| **Tipo `ENUM` nativo do PostgreSQL** | Acrescentar ou renomear um valor exige `ALTER TYPE`, que não roda dentro de uma transação em todas as versões e que o Alembic não gera sozinho. Com `VARCHAR` e `CHECK`, uma mudança de valores é uma migration comum, que troca a restrição. |

## Consequências

**Positivas**

- Cada área fica em uma pasta, e as regras de negócio, em um arquivo por área.
- As regras são testadas sem banco nem HTTP, com repositórios em memória.
- As mensagens de erro para o usuário saem sempre do service, em português.
- Mudar os valores de um enum é uma migration comum.

**Negativas**

- Os repositórios em memória precisam se comportar como os reais. Hoje, essa equivalência é garantida só pelos testes de integração do repositório real, não por um teste que rode os dois com os mesmos casos.
- O service depende dos modelos do SQLAlchemy, então o domínio não é independente do ORM.
- Uma escrita que não passe pelo service (por exemplo, SQL manual no banco) pode deixar os dados num estado que as regras não permitiriam.
