# Revisão multidimensional — 26/11/2026

Escopo: MVP na main após PR #24, remediações no PR de #14–16. Revisão assistida por IA; não equivale a auditoria independente. Responsáveis indicados são responsáveis propostos pelas issues, não declaração de autoria ou execução individual.

| ID | Dimensão / severidade | Evidência e achado | Remediação / responsável | Estado |
|---|---|---|---|---|
| A1 | Arquitetura / média | src/scheduling.py e waitlist.py: expiração ocorria em transação separada antes da mutação, abrindo janela de concorrência | Revalidar expiração dentro da transação de escrita; Pedro | Corrigido no código, CI a confirmar |
| A2 | Arquitetura / baixa | Views chamam funções de domínio e SQL; alguns módulos concentram várias responsabilidades | Separar repositórios/serviços se crescer; Gianlucca | Dívida aceita no MVP |
| S1 | Segurança / média | src/__init__.py não configurava cabeçalhos defensivos | CSP, anti-frame, nosniff, referrer-policy e no-store; ambos | Corrigido no código, CI a confirmar |
| S2 | Segurança / média | auth.py usa hash e CSRF, mas não limita tentativas de login | Rate limiting persistente e HTTPS obrigatório antes de produção; Gianlucca | Risco residual, uso local |
| S3 | Segurança / baixa | Imagens HTTPS externas e estilo inline | CSP limita scripts e framing; manter imagens confiáveis, remover inline em versão futura; Pedro | Parcial |
| P1 | Performance / média | RNF-06 exige p95 com 1000 registros e 30 requisições; ausência de medição anterior | scripts/validate.py mede painel admin com amostra e ambiente; ambos | Execução CI pendente |
| P2 | Performance / baixa | Histórico e movimentações sem paginação | Paginação e índices adicionais se crescer; Pedro | Risco residual |
| O1 | Observabilidade / média | Logs antes restritos a login negado e provisionamento | Registro de método mutável, endpoint e status HTTP, sem payload; ambos | Corrigido no código; teste pendente |
| O2 | Observabilidade / baixa | Redirecionamento 302 não distingue erro de domínio de sucesso; sem monitor externo | Instrumentar resultados de domínio e métricas em versão futura; ambos | Parcial, RNF-07 não integralmente demonstrado |
| UX1 | Interface / média | Responsividade CSS sem verificação em navegador | Chromium em 360 e 1280 px; capturas de painéis e detecção de overflow; Pedro | Execução CI pendente; inspeção humana necessária |

## Verificação de aderência

- RF-01–06: auth/catalog, RBAC e hash; profissional ativo é consultado na reserva. Desativação de profissional ainda não possui formulário; extensão futura.
- RF-07–19: scheduling/waitlist; transações BEGIN IMMEDIATE, janelas semiabertas e FIFO. Expiração por interação, não em segundo plano.
- RF-20–30: loyalty/inventory/finance/operations; conclusão atômica, valores inteiros em centavos. Resgate em reserva direta; oferta da fila não tem seleção de recompensa.
- RF-31–36: dashboards/customer; indicadores persistidos e avaliação única.
- RNF-05/06: execução de navegador/benchmark e análise dos resultados necessárias; RNF-07 parcialmente atendido; RNF-09 README e CI.
- Não há garantia de produção, pagamentos externos, notificações externas ou testes de carga concorrente de alta escala. Não usar dados reais no ambiente demonstrativo.

## Reteste e rota de remediação

A1, S1, O1: rota direta de código, manter spec e repetir testes de agenda, segurança e autenticação. P1/UX1: rota de validação, sem alterar limiar especificado. Demais pontos: registrar dívida técnica; não alterar requisitos silenciosamente. Evidências em GitHub Actions e [estratégia de testes](../testing.md).
