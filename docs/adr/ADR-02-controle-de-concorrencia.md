# ADR-02: Controle de concorrência na alteração de incidentes

- **Status:** Aceito
- **Data:** 2026-10-17

## Contexto

Vários analistas trabalham na mesma fila de incidentes ao mesmo tempo, e o supervisor pode alterar qualquer incidente. Sem controle, duas alterações simultâneas no mesmo incidente fazem a última sobrescrever a primeira sem aviso.

A RN-08 exige que nenhuma alteração sobrescreva outra sem que o usuário saiba.

Restrições:

- A comunicação entre frontend e API é HTTP, que não mantém estado entre requisições.
- Entre visualizar um incidente e salvar uma alteração, o analista pode levar de segundos a minutos.
- Conflitos são esperados, mas raros em relação ao volume total de alterações.

## Decisão

Adotar duas camadas complementares:

**1. Reserva de negócio ("Assumir")**

O analista assume um incidente antes de trabalhar nele (RN-02), e só o responsável ou um supervisor pode alterá-lo (RN-03). Isso faz o conflito entre analistas aparecer **no início do trabalho**, em um único clique, e não depois de o formulário estar preenchido.

**2. Controle de concorrência otimista**

- Cada incidente tem um campo `version`, incrementado a cada alteração.
- O frontend recebe a versão junto com o incidente e a envia de volta ao salvar.
- O service valida as regras de negócio sobre o estado lido do banco (papel do usuário, status, responsável) e confere se a versão enviada ainda é a atual.
- O repository grava com um `UPDATE` condicional e atômico. Por exemplo, ao assumir um incidente:

  ```sql
  UPDATE incidents
  SET status = 'INVESTIGATING', assignee_id = :analista, version = version + 1, updated_at = now()
  WHERE id = :id AND version = :versao_vista
  RETURNING *;
  ```

- A condição `version = :versao_vista` garante que ninguém alterou o incidente entre a leitura e a gravação. Como a verificação e a escrita acontecem no mesmo comando, duas requisições simultâneas nunca conseguem gravar a mesma versão.
- Se nenhuma linha for afetada, o service levanta um conflito e a API responde **HTTP 409 Conflict** com o estado atual do incidente.

Todos os casos de uso que alteram um incidente (assumir, mudar status, devolver à fila, encerrar) usam esse mesmo mecanismo.

**No frontend**, ao receber um 409:

- os dados que o usuário preencheu são mantidos.
- o estado atual do incidente é exibido, com quem o alterou.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| **Last write wins** (sem controle) | Perde alterações em silêncio. |
| **Lock pessimista** (`SELECT ... FOR UPDATE`) | Só funciona dentro de uma transação curta. Manter a linha travada enquanto o analista decide exigiria uma conexão aberta por minutos, o que esgota o pool de conexões e não sobrevive a quedas de rede. |
| **Lock distribuído** | Infraestrutura extra sem benefício com um único banco de dados. |

## Consequências

**Positivas**

- Nenhum recurso fica travado enquanto o usuário pensa.
- Verificação e escrita acontecem em um único comando atômico, sem janela de corrida.
- Implementação simples: um campo a mais e uma condição no `WHERE`.
- A mesma regra protege todos os papéis, inclusive o supervisor.

**Negativas**

- O usuário pode receber um conflito depois de preencher dados. **Mitigação:** manter o formulário preenchido no conflito e consultar periodicamente a versão do incidente aberto e avisar se ela mudar.
- Todo endpoint de alteração precisa receber o campo de versão. **Mitigação:** schema de entrada com campo versão obrigatório e teste automatizado de conflito para cada endpoint de escrita.
