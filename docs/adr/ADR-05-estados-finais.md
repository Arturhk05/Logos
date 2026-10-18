# ADR-05: Fechado e Inconclusivo como estados finais

- **Status:** Aceito
- **Data:** 2026-10-17

## Contexto

O desafio define quatro status para um incidente: Aberto, Em Investigação, Fechado e Inconclusivo, mas não define as transições permitidas entre eles.

A principal dúvida era o que fazer quando um incidente encerrado (Fechado ou Inconclusivo) volta a exigir atenção: reabrir o mesmo incidente ou criar um novo.

## Decisão

Fechado e Inconclusivo são estados finais. Um incidente encerrado não muda mais de status. Se o problema voltar a ocorrer, um novo incidente é criado.

Transições permitidas (RN-04):

```
Aberto ──► Em Investigação ──► Fechado       (final)
  ▲              │
  └──────────────┤
                 └──────────► Inconclusivo   (final)
```

A volta de *Em Investigação* para *Aberto* é mantida. Ela não é uma reabertura: é o analista devolvendo à fila um incidente que assumiu (ex.: fim de turno), para que outro possa assumi-lo.

As transições são validadas no backend. Uma transição não permitida é rejeitada com HTTP 422 e uma mensagem clara.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| **Permitir reabrir** Fechado ou Inconclusivo | Aumenta o número de transições e de casos a tratar (quem é o responsável após reabrir? o motivo de fechamento ainda vale?), distorce métricas como tempo de resolução e torna o histórico mutável. |
| **Sem regras de transição** | Permite estados sem sentido, como voltar de Fechado para Aberto sem rastro. |

## Consequências

**Positivas**

- Máquina de estados pequena, fácil de testar e de explicar.
- Incidentes encerrados são registros imutáveis, bons para auditoria (RN-05) e métricas.
- Reflete o domínio: um novo problema na estrada é, na prática, uma nova ocorrência.

**Negativas**

- O novo incidente não carrega o contexto do anterior.
- Um encerramento feito por engano não pode ser desfeito pela interface. **Evolução:** adicionar janela de correção para desfazer o encerramento.