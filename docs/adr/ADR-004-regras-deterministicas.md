# ADR-004 — Regras de negócio determinísticas, sem IA no produto

**Status:** Proposto, aguardando revisão | **Issue:** #4 | **Data:** 2026-11-26

## Contexto

A fila, fidelidade, estoque e financeiro exigem decisões verificáveis e reproduzíveis. O professor permite IA no produto, mas não a exige. Não há necessidade de inferência probabilística para essas regras.

## Decisão

Implementar regras determinísticas: fila FIFO por compatibilidade e id, oferta exclusiva por até 15 minutos ou início da vaga; dez créditos por cortes elegíveis pagos convertem em recompensa; comissão sobre valor pago; estoque não negativo. Processar ofertas expiradas por interação com a aplicação, sem worker externo. Usar agente de IA exclusivamente como apoio à elaboração e codificação, com revisão humana.

## Alternativas consideradas

LLM no produto adicionaria variabilidade, custo e dependência. Worker agendado dedicado melhoraria pontualidade das notificações, mas exigiria infraestrutura e operação adicional.

## Consequências

Resultado previsível e testável, sem API paga. A expiração é respeitada na próxima operação, mas a notificação do próximo cliente pode atrasar até nova interação. Para operação comercial, avaliar agendador persistente. Alterar parâmetros apenas com revisão da spec quando forem regras fixas.

## Rastreabilidade

RF-15–28, RF-36; RN-03–08, RN-11–15; Issues #7–10, #14. Consulte [spec.md](../../spec.md) e [plan.md](../../plan.md) (proposta da Issue #2).

Elaboração assistida por IA; decisão sujeita à validação humana. Não constitui evidência de implementação ou teste.
