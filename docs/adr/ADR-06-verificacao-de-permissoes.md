# ADR-06: Verificação de permissões em camadas

- **Status:** Aceito
- **Data:** 2026-10-18

## Contexto

A ADR-03 define o que cada papel pode fazer, e a RNF-01 exige que cada ação seja permitida apenas aos papéis autorizados. Falta decidir **onde** essa verificação acontece no backend.

As regras de permissão do Logos são de dois tipos:

- **Dependem só do papel:** "apenas motoristas reportam incidentes". Basta saber quem é o usuário.
- **Dependem do dado:** "apenas o responsável pelo incidente ou um supervisor altera seu status" (RN-03). É preciso carregar o incidente para decidir.

Verificar a mesma regra em dois lugares cria duplicação e um efeito colateral: a verificação que roda primeiro esconde a outra, e o usuário recebe uma mensagem diferente da esperada.

## Decisão

Cada regra tem **um único lugar**, definido pelo que ela precisa saber para decidir:

| Tipo de regra | Onde é verificada | Como |
|---|---|---|
| Depende só do papel | Na rota | Dependência `require_role(...)`, declarada na assinatura da rota |
| Depende do dado | No service | O service recebe o usuário (`CurrentUser`) e decide com o dado carregado |

Uma regra nunca é verificada nas duas camadas.

O usuário não autenticado recebe 401 antes de qualquer verificação de papel, porque `require_role` depende de `get_current_user`. O papel não autorizado recebe 403 com uma mensagem genérica: "Você não tem permissão para realizar esta ação."

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| **Tudo no service** | Mantém cada service autocontido e testável sem HTTP, mas a permissão não aparece na rota: é preciso abrir o service para saber quem pode chamar um endpoint. É o padrão menos comum em FastAPI, Spring (`@PreAuthorize`) e .NET (`[Authorize(Roles = ...)]`). |
| **Tudo na rota** | Impossível para as regras que dependem do dado, porque a rota não conhece o incidente sem consultá-lo. Levar essa lógica para a rota espalharia regras de negócio pela camada HTTP. |
| **Nas duas camadas** | Duplica a regra, e a verificação da rota esconde a do service, com mensagem diferente para o mesmo caso. |

## Consequências

**Positivas**

- A permissão de cada endpoint fica visível na própria rota.
- O usuário sem permissão é recusado antes de qualquer consulta ao banco.
- Cada regra tem um único lugar e um único teste.

**Negativas**

- O service deixa de se proteger sozinho nas regras que dependem só do papel. Um novo ponto de entrada que chame o service diretamente (script, tarefa agendada) precisa verificar o papel por conta própria.
- As regras de papel passam a ser testadas por testes de API, que precisam de banco e são mais lentos que os testes de unidade do service.
- A regra do `AGENTS.md` "regras de negócio ficam só no service" passa a ter uma exceção: as permissões que dependem só do papel ficam na rota.
