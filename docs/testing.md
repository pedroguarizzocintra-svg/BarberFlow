# Estratégia de testes e evidências

## Execução comprovada anterior
PR #24: [Actions 45917644205](https://github.com/pedroguarizzocintra-svg/BarberFlow/actions/runs/45917644205), job 140240605429. Log consultado: **27 passed in 9.23s**. Esse resultado se refere ao código do PR #24, não ao PR final.

## Matriz de rastreabilidade
| Aceite | Evidência automatizada |
|---|---|
| CT-01 | test_auth, test_dashboards, test_business: papéis, titularidade |
| CT-02–03 | test_scheduling: sobreposição, adjacência, reagendamento |
| CT-04 | test_scheduling: FIFO, recusa e expiração |
| CT-05–07 | test_business: 10 créditos, resgate, consumo e alerta |
| CT-08–09 | test_scheduling: rollback, comissão, duplicidade |
| CT-10 | test_dashboards: avaliação única e propriedade |
| CT-11 | test_business e test_dashboards: totais/indicadores |
| CT-12 | test_auth: persistência em banco; fixtures independentes |

Comandos: `python -m pytest -q`. CI em Python 3.12. Fixtures usam banco temporário e dados fictícios. Testes adicionais de cabeçalhos, escape e seed idempotente incluídos no PR final.

## Validação não funcional
`python -m pip install playwright==1.51.0`, `python -m playwright install chromium`, `python -m scripts.validate`. Em Linux CI, use --with-deps.

O script cria 1000 atendimentos fictícios em SQLite temporário. Mede 30 GET /admin sequenciais autenticados (Flask test client, uma requisição de aquecimento excluída), p95 nearest rank, limiar 2000 ms. Não mede rede, concorrência ou ambiente de produção. Chromium testa ausência de rolagem horizontal em 13 rotas, 360/1280 px, e captura seis painéis. A inspeção humana de legibilidade e operação continua necessária. Artefato validation-evidence em Actions contém JSON, amostras e PNGs quando a execução conclui.

Resultado da nova execução: consultar o PR e o workflow correspondente; não atribuir o resultado anterior ao código novo.
