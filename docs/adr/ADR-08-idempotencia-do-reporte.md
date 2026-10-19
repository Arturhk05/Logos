# ADR-08: Idempotência do reporte de incidentes

- **Status:** Aceito
- **Data:** 2026-10-18

## Contexto

O motorista reporta incidentes pelo celular, muitas vezes com sinal instável. A US-08 exige duas coisas que parecem opostas:

- Se a requisição falhar, ele vê um botão "Tentar novamente" e reenvia os mesmos dados.
- Se ele clicar em enviar mais de uma vez, apenas um incidente é criado.

O caso difícil é a resposta perdida: o reporte chega à API e o incidente é criado, mas a resposta não volta ao celular. Para o motorista, o envio falhou, e o "Tentar novamente" criaria um segundo incidente igual. Desabilitar o botão durante o envio não resolve esse caso.

## Decisão

Cada reporte carrega uma **chave de idempotência**, enviada no cabeçalho `Idempotency-Key`:

- O frontend gera um UUID quando o formulário é aberto e o mantém em todos os reenvios desse formulário, inclusive no "Tentar novamente". Depois de um reporte confirmado, o próximo formulário recebe uma chave nova.
- O cabeçalho é obrigatório. Sem ele, a API responde 422.
- A chave fica gravada no incidente (`incidents.idempotency_key`), com uma restrição única em `(reporter_id, idempotency_key)`.
- Se o mesmo motorista enviar de novo uma chave já usada, nenhum incidente é criado, e a API devolve, com a mesma resposta 201, o incidente criado da primeira vez, no seu estado atual (ele pode já estar em investigação, por exemplo). Diferenças no corpo do reenvio são ignoradas.
- A unicidade é por motorista: a chave de um motorista nunca devolve o incidente de outro.

A restrição única no banco também resolve dois envios simultâneos: o segundo `INSERT` espera o primeiro ser confirmado e então falha na unicidade. O repositório captura essa falha e devolve o incidente que já existe. Se o primeiro for desfeito, o segundo é gravado normalmente.

Isso depende do nível de isolamento READ COMMITTED, o padrão do PostgreSQL: a consulta feita depois da falha enxerga o incidente que o outro envio acabou de confirmar. Num nível mais restrito, como REPEATABLE READ, ela não o enxergaria, e o reenvio terminaria em erro.

A coluna aceita nulo, porque incidentes criados fora da API (como os do seed) não têm chave.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| **Só desabilitar o botão no frontend** | Evita o clique duplo, mas não a resposta perdida: o "Tentar novamente" cria outro incidente. |
| **Deduplicar por conteúdo e janela de tempo** (mesmo motorista, mesma categoria e local em poucos minutos) | Gera falsos positivos: dois incidentes reais e parecidos seriam fundidos em um. |

## Consequências

**Positivas**

- O motorista pode reenviar quantas vezes precisar sem duplicar o incidente.
- A garantia vem de uma restrição do banco, sem janela de corrida.
- Uma coluna e uma restrição, sem tabela nova.

**Negativas**

- O frontend precisa gerar a chave e mantê-la entre os reenvios do mesmo formulário.
- Se o motorista editar o formulário antes do "Tentar novamente" e o primeiro envio já tiver chegado, as alterações são descartadas sem aviso. **Mitigação:** a tela de confirmação mostra os dados devolvidos pela API, ou seja, o que foi de fato registrado.
- O isolamento READ COMMITTED passa a ser um requisito. Mudá-lo exige rever esta decisão.
- As chaves nunca expiram. **Evolução:** limpar chaves antigas, se o volume justificar.
