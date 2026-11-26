# ADR-001 — Monólito modular com Flask

**Status:** Proposto, aguardando revisão | **Issue:** #4 | **Data:** 2026-11-26

## Contexto

A equipe possui dois integrantes, prazo curto e precisa integrar agenda, estoque, financeiro e fidelidade sem depender de infraestrutura externa. A spec exige uma solução web funcional, mas não impõe linguagem.

## Decisão

Adotar Python 3.12, Flask, Jinja2, HTML/CSS e JavaScript progressivo. Organizar rotas, regras de negócio e persistência em módulos dentro de uma única aplicação. Centralizar a transação de conclusão na camada de aplicação.

## Alternativas consideradas

Microserviços: aumentariam deploy e coordenação de transações. SPA com backend separado: maior complexidade de build e integração para o MVP.

## Consequências

Menor custo de implantação e teste integrado; separação lógica facilita manutenção. Escala e deploy independentes ficam limitados; manter limites entre módulos para evolução. Dependências deverão ser fixadas após validação.

## Rastreabilidade

RF-01–36; RNF-05–06; Issue #2, #5–13. Consulte [spec.md](../../spec.md) e [plan.md](../../plan.md) (proposta da Issue #2).

Elaboração assistida por IA; decisão sujeita à validação humana. Não constitui evidência de implementação ou teste.
