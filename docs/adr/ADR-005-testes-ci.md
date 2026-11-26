# ADR-005 — Testes automatizados e integração contínua

**Status:** Proposto, aguardando revisão | **Issue:** #4 | **Data:** 2026-11-26

## Contexto

O professor exige evidências de qualidade, rastreabilidade e revisão. O fluxo integrado pode gerar inconsistências se mudanças não forem validadas.

## Decisão

Usar pytest com fixtures de banco temporário, testes unitários das regras e integração HTTP pelo cliente Flask. Configurar GitHub Actions para pytest em PRs e pushes à main; associar cenários CT da spec aos testes. Revisão humana antes de merge e evidência real para verificações manuais de segurança, responsividade e performance.

## Alternativas consideradas

Somente testes manuais: baixa repetibilidade e risco de regressão. Testes end-to-end completos de navegador: maior custo de manutenção inicial; poderão complementar o MVP.

## Consequências

Regressões detectadas cedo e histórico verificável. CI não comprova sozinho segurança, usabilidade ou desempenho de produção. Métricas e testes só podem ser declarados após execução. Branch protection poderá exigir checks quando CI estiver disponível; não pressupor configuração ativa.

## Rastreabilidade

RNF-01–09; CT-01–12; Issues #14–16. Consulte [spec.md](../../spec.md) e [plan.md](../../plan.md) (proposta da Issue #2).

Elaboração assistida por IA; decisão sujeita à validação humana. Não constitui evidência de implementação ou teste.
