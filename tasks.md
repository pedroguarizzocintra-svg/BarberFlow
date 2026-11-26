# BarberFlow — Backlog técnico e rastreabilidade

**Versão:** 0.1, proposta para revisão | **Issue:** #3
**Fontes:** [spec.md](spec.md) e proposta de [plan.md](plan.md) (Issue #2). As decisões de arquitetura são propostas na Issue #4. As tarefas abaixo são planejadas, não executadas. Cada tarefa tem identificador, responsável, prioridade, dependência de grupo e critério verificável. As Issues #5–16 agrupam tarefas atômicas; criar sub-issues se necessário sem perder o vínculo.

## Convenções

- Alta: essencial ao fluxo ou à entrega; Média: funcionalidade complementar conforme spec.
- As dependências de cada grupo são pré-requisitos da implementação; tarefas internas devem seguir a ordem lógica, salvo integrações explicitadas. T11 é a integração final, não bloqueia o desenvolvimento isolado de T15–23. T32–34 podem começar junto aos módulos. Em tarefas de ambos, dividir execução e revisão entre os integrantes de forma explícita no PR.
- Marcar caixas somente após evidência real. Referenciar Issue e IDs de requisitos nos commits e PRs. Não fechar Issue antes de cumprir critérios ou revisar escopo.
- Ordem inicial: #1 (spec incorporada via PR #17), #2 (plan), #3 (este arquivo), #4 (ADRs). As revisões de #2–4 são independentes mas devem ficar coerentes antes da implementação.

## #5 — Infraestrutura e autenticação

**Responsável:** Gianlucca | **Prioridade:** Alta | **Dependências:** #2–4

- [ ] **T01** — Criar fábrica Flask, configuração e dependências; inicialização local. **Rastreio:** RNF-03, RNF-09. **Aceite:** Aplicação inicia com configuração de teste e banco separado.
- [ ] **T02** — Criar schema, índices, chaves estrangeiras e helpers transacionais. **Rastreio:** RNF-03–04, RN-11–12. **Aceite:** Schema inicializa; FK e restrições rejeitam dados inválidos.
- [ ] **T03** — Implementar cadastro de cliente e login/logout com hash. **Rastreio:** RF-01–02, RNF-01. **Aceite:** Cadastro não aceita perfil privilegiado; credenciais inválidas negadas.
- [ ] **T04** — Implementar guardas de papel, titularidade e CSRF. **Rastreio:** RF-03, RNF-02, RNF-08. **Aceite:** Testes negam acesso cruzado e POST sem token.
- [ ] **T05** — Criar comando de inicialização e contas fictícias de demonstração. **Rastreio:** RF-06, RNF-09. **Aceite:** Admin inicial criado localmente; nenhuma credencial real versionada.

## #6 — Catálogo e agendamento

**Responsável:** Pedro | **Prioridade:** Alta | **Dependências:** T01–05

- [ ] **T06** — Criar gestão administrativa de serviços ativos e catálogo público ao cliente. **Rastreio:** RF-04–05, RN-10. **Aceite:** Preços, duração e elegibilidade validados; cliente não altera catálogo.
- [ ] **T07** — Criar gestão de barbeiros e expediente. **Rastreio:** RF-06, RN-02. **Aceite:** Expediente válido e comissão configurável; conflitos não descartam reservas existentes.
- [ ] **T08** — Calcular disponibilidade e bloquear sobreposições transacionais. **Rastreio:** RF-07–09, RN-01–02. **Aceite:** CT-02 passa; oferta ativa bloqueia terceiros quando integrada.
- [ ] **T09** — Criar reserva, cancelamento e reagendamento atômico. **Rastreio:** RF-08, RF-10–11. **Aceite:** CT-03 passa; horário anterior preservado em falha.
- [ ] **T10** — Implementar início e ausência por barbeiro titular. **Rastreio:** RF-12, RF-14, RN-16, RN-20. **Aceite:** Estado inválido e barbeiro alheio são rejeitados.
- [ ] **T11** — Integrar conclusão aos módulos de estoque, financeiro e fidelidade após T15–T23. **Rastreio:** RF-13, RF-36, RNF-04. **Aceite:** CT-06–09 passam; nenhum efeito parcial ou duplicado.

## #7 — Fila de espera

**Responsável:** Pedro | **Prioridade:** Alta | **Dependências:** T08–09

- [ ] **T12** — Registrar preferências e retirada da fila. **Rastreio:** RF-15, RN-14. **Aceite:** Preferências persistidas e titularidade verificada.
- [ ] **T13** — Ofertar vaga liberada ao primeiro compatível, com notificação. **Rastreio:** RF-16–17, RN-08, RN-13. **Aceite:** FIFO, desempate por id, uma oferta ativa por vaga.
- [ ] **T14** — Aceitar, recusar e expirar oferta; avançar fila. **Rastreio:** RF-18–19, RN-13–14. **Aceite:** CT-04 passa; reserva única e oferta vencida rejeitada.

## #8 — Fidelidade

**Responsável:** Pedro | **Prioridade:** Alta | **Dependências:** T02, T09; integrar T11

- [ ] **T15** — Registrar crédito único por corte pago elegível. **Rastreio:** RF-20, RN-03–04. **Aceite:** Corte gratuito, ausência e cancelamento não pontuam.
- [ ] **T16** — Converter dez créditos em recompensa; preservar excedentes. **Rastreio:** RF-21, RN-03. **Aceite:** CT-05 passa; créditos não são convertidos duas vezes.
- [ ] **T17** — Reservar, liberar e consumir recompensa; consultar saldo. **Rastreio:** RF-22–23, RN-15. **Aceite:** CT-06 passa; resgate único e devolução após cancelamento/ausência.

## #9 — Estoque

**Responsável:** Gianlucca | **Prioridade:** Alta | **Dependências:** T02, T04, T06; integrar T11

- [ ] **T18** — Criar cadastro de insumos, mínimos e configuração de consumo. **Rastreio:** RF-24, RN-10. **Aceite:** Administrador gerencia quantidades inteiras e consumo positivo.
- [ ] **T19** — Registrar movimentações manuais sem saldo negativo. **Rastreio:** RF-24, RF-26, RN-12. **Aceite:** Saída insuficiente é rejeitada; histórico persiste.
- [ ] **T20** — Aplicar baixas por atendimento e gerar alertas. **Rastreio:** RF-25–27, RN-05–06, RN-11–12. **Aceite:** CT-07–08 passam; baixa única por insumo e atendimento.

## #10 — Financeiro

**Responsável:** Gianlucca | **Prioridade:** Alta | **Dependências:** T02, T04, T07; integrar T11

- [ ] **T21** — Registrar receita e comissão usando centavos e preço congelado. **Rastreio:** RF-28, RN-07, RN-11. **Aceite:** CT-09 passa; gratuitos não geram receita.
- [ ] **T22** — Registrar despesas e filtrar por período. **Rastreio:** RF-29. **Aceite:** Valores positivos, data válida e acesso admin.
- [ ] **T23** — Calcular totais e resultado operacional estimado. **Rastreio:** RF-30, RN-17. **Aceite:** CT-11 passa; despesas não duplicam comissões.

## #11 — Interface do cliente

**Responsável:** Pedro | **Prioridade:** Alta | **Dependências:** T03–04, T06–09, T12–17, T27

- [ ] **T24** — Construir layout responsivo, navegação e catálogo. **Rastreio:** RF-05, RNF-05. **Aceite:** Telas em 360/1280 px; sem dados fictícios apresentados como reais.
- [ ] **T25** — Implementar telas de agendamento, fila, recompensa e notificações. **Rastreio:** RF-07–11, RF-15–19, RF-23, RF-33. **Aceite:** Fluxos funcionam com dados persistidos e feedback de erro.
- [ ] **T26** — Implementar perfil e histórico acessível pelo cliente. **Rastreio:** RF-33, RN-20. **Aceite:** Cliente vê apenas os próprios registros; total de visitas e gastos corretos.

## #12 — Dashboard e painel do barbeiro

**Responsável:** Gianlucca | **Prioridade:** Alta | **Dependências:** T07, T10–11, T20–23, T27

- [ ] **T27** — Calcular indicadores e médias por período. **Rastreio:** RF-30–32, RN-17–19. **Aceite:** Valores calculados do banco; zero/sem avaliação tratados.
- [ ] **T28** — Construir painel administrativo com serviços, equipe, estoque, financeiro. **Rastreio:** RF-06, RF-27, RF-31, RNF-05. **Aceite:** Admin consulta indicadores e executa operações autorizadas.
- [ ] **T29** — Construir agenda e painel individual do barbeiro. **Rastreio:** RF-12–14, RF-32, RN-20. **Aceite:** Barbeiro realiza ações somente nos próprios atendimentos.

## #13 — Histórico e avaliações

**Responsável:** Pedro | **Prioridade:** Média | **Dependências:** T02, T04, T10–11

- [ ] **T30** — Consultar visitas e gastos por titular. **Rastreio:** RF-23, RF-33, RN-18. **Aceite:** Visitas incluem gratuitos; gastos somam valores pagos.
- [ ] **T31** — Registrar avaliação única de atendimento concluído. **Rastreio:** RF-34–35, RN-09. **Aceite:** CT-10 passa; notas inválidas e avaliações alheias negadas.

## #14 — Testes

**Responsável:** Ambos | **Prioridade:** Alta | **Dependências:** Incremental; integração após T01–31

- [ ] **T32** — Configurar fixtures de banco temporário e suíte pytest. **Rastreio:** RNF-03–04. **Aceite:** Testes isolados e reproduzíveis; sem tocar banco real.
- [ ] **T33** — Testar autenticação, agenda, fila e concorrência. **Rastreio:** RF-01–19, RNF-01–02, RNF-08. **Aceite:** CT-01–04; concorrência não duplica reservas.
- [ ] **T34** — Testar conclusão, fidelidade, estoque, financeiro e avaliações. **Rastreio:** RF-13, RF-20–36, RNF-04. **Aceite:** CT-05–11; rollback e idempotência demonstrados.
- [ ] **T35** — Testar reinicialização, interface e performance. **Rastreio:** RNF-03, RNF-05–06. **Aceite:** CT-12; registrar viewport e p95 real com ambiente e amostra.
- [ ] **T36** — Configurar CI e consolidar evidências. **Rastreio:** RNF-09. **Aceite:** Workflow executa pytest e documenta resultado real.

## #15 — Revisão e SSDLC

**Responsável:** Ambos | **Prioridade:** Alta | **Dependências:** T01–36

- [ ] **T37** — Revisar arquitetura e aderência spec/código. **Rastreio:** RF-01–36, RN-01–20. **Aceite:** Achados com severidade, evidência, responsável e remediação.
- [ ] **T38** — Revisar segurança e registrar SSDLC. **Rastreio:** RNF-01–02, RNF-08. **Aceite:** Ameaças e controles verificados; riscos residuais explícitos.
- [ ] **T39** — Revisar performance e observabilidade. **Rastreio:** RNF-06–07. **Aceite:** Métricas reais ou ausência explicitada; logs sem segredos.
- [ ] **T40** — Corrigir achados críticos e repetir testes afetados. **Rastreio:** RNF-04, RNF-09. **Aceite:** Correções rastreadas em PR e resultado de reteste registrado.

## #16 — Entrega

**Responsável:** Ambos | **Prioridade:** Alta | **Dependências:** T01–40

- [ ] **T41** — Escrever README com instalação, execução, contas fictícias e testes. **Rastreio:** RNF-09. **Aceite:** Outra pessoa executa em ambiente limpo seguindo instruções.
- [ ] **T42** — Conferir artefatos, Kanban, PRs e escopo realmente entregue. **Rastreio:** RNF-09. **Aceite:** docs, src, tests, .specify presentes; pendências não mascaradas.
- [ ] **T43** — Validar demonstração e consolidar entrega. **Rastreio:** RNF-09, CT-01–12. **Aceite:** Fluxo demonstrável; evidências reais e acesso do professor conferidos.

## Critérios de conclusão por PR

- Issue vinculada e requisitos identificados.
- Código e documentação alinhados à baseline aprovada.
- Testes relevantes executados e evidência real registrada (ou justificativa quando não aplicável).
- Revisão humana pelo outro integrante antes do merge.
- Kanban atualizado; lacunas e limitações documentadas.

## Matriz de cobertura para validação final

| Requisitos | Tarefas | Evidência prevista |
| --- | --- | --- |
| RF-01–03, RNF-01–02, RNF-08 | T03–04, T33, T38 | CT-01 e testes de sessão/CSRF |
| RF-04–14 | T06–11, T33–34 | CT-02–03, CT-08–09 |
| RF-15–19 | T12–14, T33 | CT-04 |
| RF-20–23 | T15–17, T26, T34 | CT-05–06 |
| RF-24–27 | T18–20, T34 | CT-07–08 |
| RF-28–32 | T21–23, T27–29, T34 | CT-09, CT-11 e indicadores |
| RF-33–36 | T11, T25–26, T30–31, T34 | CT-09–10 e histórico |
| RNF-03–04 | T01–02, T11, T32, T34–35 | CT-08, CT-12 |
| RNF-05–07 | T24, T28–29, T35, T39 | Viewports, p95 e logs |
| RNF-09 | T05, T36, T41–43 | README e execução reproduzível |

Elaboração assistida por IA; responsáveis devem validar prioridades, dependências e critérios antes do merge. Nenhum teste foi executado nesta etapa.
