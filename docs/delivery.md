# Checklist de entrega e demonstração

- [x] Repositório público, código e documentação versionados.
- [x] Spec EARS, plano, tasks, ADRs e estrutura mínima.
- [x] Três perfis, persistência SQLite e fluxo de agenda/fila/conclusão.
- [x] PRs #17–24 e CI anterior verificados.
- [ ] CI do PR final aprovado e revisão humana registrada.
- [ ] Inspeção visual humana das capturas 360/1280 px.
- [ ] Instalação limpa e demonstração executada por integrante.
- [ ] Conferir convite do professor niltonmack@mackenzie.br e acesso.
- [ ] Conferir encerramento das issues e status do Project.
- [ ] Registrar contribuição efetiva de cada integrante e confirmação do tema pelo docente (não presumir evidência inexistente).

## Roteiro
1. Executar os comandos do README com dados fictícios.
2. Login admin: mostrar catálogo, expediente, estoque e indicadores.
3. Login cliente: reservar horário futuro e verificar fidelidade.
4. Outro cliente: entrar na fila; cancelar reserva original; aceitar oferta.
5. No horário previsto, login barbeiro: iniciar, confirmar recebimento e concluir.
6. Cliente avalia atendimento; admin consulta receita, comissão e baixa de estoque.
7. Abrir Actions e mostrar logs, JSON e capturas; apresentar spec, ADRs, PRs e Kanban.

Para a apresentação ao vivo, agende um horário próximo ou prepare dados fictícios previamente; não altere o relógio do sistema para simular evidência. Testes de dez cortes e concorrência demonstram cenários demorados.
