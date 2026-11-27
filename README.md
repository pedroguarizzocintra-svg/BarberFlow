# BarberFlow

**Gestão de barbearias com agendamento inteligente e fidelidade.**

Projeto acadêmico de Engenharia da Computação — Modelagem de Software, Mackenzie, 2026-2. Equipe: Pedro Guarizzo Cintra e Gianlucca (GitHub: [pedroguarizzocintra-svg](https://github.com/pedroguarizzocintra-svg), [ItsNeymar](https://github.com/ItsNeymar)).

## Problema e solução

Pequenas barbearias precisam organizar horários, evitar conflitos, recuperar vagas canceladas e acompanhar estoque e resultados sem depender de planilhas isoladas. BarberFlow reúne esses processos em uma aplicação web com três perfis.

| Perfil | Funcionalidades |
|---|---|
| Cliente | Catálogo, reservas, reagendamento, cancelamento, fila FIFO, notificações, fidelidade, histórico e avaliação |
| Barbeiro | Agenda própria, início/ausência/conclusão, comissões e avaliação média |
| Administrador | Serviços, equipe, expediente, estoque, despesas, faturamento e indicadores |

A conclusão é transacional: consumo de insumos, receita, comissão e fidelidade são persistidos juntos; estoque insuficiente desfaz a operação. A fila oferece vagas liberadas por ordem de chegada, com prazo de até 15 minutos.

## Executar localmente

Requisitos: Python 3.12, Git e terminal. Clone o repositório e entre na pasta:

```bash
git clone https://github.com/pedroguarizzocintra-svg/BarberFlow.git
cd BarberFlow
```

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:BARBERFLOW_SECRET = (python -c "import secrets; print(secrets.token_hex(32))")
python -m flask --app src init-db
python -m flask --app src seed-demo
python -m flask --app src seed-catalog
python -m flask --app src run
```

**Linux/macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export BARBERFLOW_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python -m flask --app src init-db
python -m flask --app src seed-demo
python -m flask --app src seed-catalog
python -m flask --app src run
```

Acesse [http://127.0.0.1:5000](http://127.0.0.1:5000). No seed-demo, escolha uma senha fictícia com pelo menos 10 caracteres, confirmando quando solicitado.

| Perfil | E-mail fictício |
|---|---|
| Cliente | cliente@example.test |
| Barbeiro | barbeiro@example.test |
| Admin | admin@example.test |

O seed-catalog adiciona três serviços, expediente de segunda a sábado e estoque inicial fictício, sem sobrescrever registros existentes. Use um banco limpo para demonstração. O banco SQLite fica em instance/ e não é versionado. Não utilize senhas reais nem dados pessoais no ambiente de teste. Para criar somente um administrador, use `python -m flask --app src create-admin`.

## Testes e qualidade

```bash
python -m pytest -q
```

Validação adicional (Chromium, capturas e p95):

```bash
python -m pip install playwright==1.51.0
python -m playwright install chromium
python -m scripts.validate
```

Consulte [Actions](https://github.com/pedroguarizzocintra-svg/BarberFlow/actions) e [estratégia/evidências de testes](docs/testing.md). Resultados correspondem ao commit executado.

## Arquitetura e SDD

Flask/Jinja, SQLite e CSS responsivo; funções de domínio em módulos, transações de escrita, autenticação por sessão com RBAC e CSRF. Desenvolvimento orientado à especificação, assistido por agente de IA e sujeito à revisão humana.

- [Spec — EARS, personas, regras, casos de uso e domínio](spec.md)
- [Plano técnico](plan.md)
- [Tasks e rastreabilidade](tasks.md)
- [Documentação e ADRs](docs/)
- [Diagramas UML](docs/uml.md)
- [Diretrizes SDD](.specify/)
- [Revisão multidimensional](docs/review/README.md)
- [SSDLC](docs/review/ssdlc.md)
- [Roteiro de demonstração e pendências](docs/delivery.md)
- [Issues](https://github.com/pedroguarizzocintra-svg/BarberFlow/issues), [Kanban](https://github.com/users/pedroguarizzocintra-svg/projects/5) e [Pull Requests](https://github.com/pedroguarizzocintra-svg/BarberFlow/pulls)

## Limites do MVP

Aplicação acadêmica local, sem pagamentos reais, notificações externas ou IA no produto. A fila processa expirações por interação. Recompensas são escolhidas em reservas diretas. O resultado financeiro é operacional estimado, não lucro contábil. Não é uma implantação de produção; rate limiting, HTTPS obrigatório, backups automatizados e monitoramento externo são evoluções. Consulte a revisão para pendências verificáveis.
