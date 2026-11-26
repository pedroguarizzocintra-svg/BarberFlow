# ADR-002 — SQLite e integridade transacional

**Status:** Proposto, aguardando revisão | **Issue:** #4 | **Data:** 2026-11-26

## Contexto

O fluxo de atendimento precisa persistir registros e impedir agendamentos simultâneos, estoques negativos e lançamentos duplicados. O MVP opera uma unidade e não exige banco remoto.

## Decisão

Adotar SQLite via sqlite3, chaves estrangeiras habilitadas, constraints CHECK e UNIQUE, índices e consultas parametrizadas. Usar BEGIN IMMEDIATE para operações concorrentes de escrita, revalidar disponibilidade dentro da transação e concluir atendimento com rollback integral. Representar dinheiro em centavos inteiros e comissão em pontos-base.

## Alternativas consideradas

PostgreSQL oferece maior concorrência, mas requer configuração extra. Arquivos JSON não oferecem as mesmas garantias relacionais e transacionais. ORM reduziria SQL manual, porém adicionaria dependências e abstração.

## Consequências

Persistência simples e atômica, testes com banco temporário. SQLite serializa escritas; sob alta concorrência podem ocorrer locks, mitigados com transações curtas e timeout. Necessidade de migração se escala exceder o MVP. Não versionar bancos com dados reais.

## Rastreabilidade

RF-08–11, RF-13, RF-17–22, RF-25–28, RF-36; RNF-03–04; RN-01, RN-11–12; Issues #5–10, #14. Consulte [spec.md](../../spec.md) e [plan.md](../../plan.md) (proposta da Issue #2).

Elaboração assistida por IA; decisão sujeita à validação humana. Não constitui evidência de implementação ou teste.
