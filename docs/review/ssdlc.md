# SSDLC — BarberFlow

| Fase | Prática / artefato |
|---|---|
| Requisitos | RNF-01/02/04/08 e RN-10/20: autenticação, autorização, transações, validação |
| Design | Flask monolítico modular, SQLite, papéis e titularidade; ADRs e spec versionados |
| Implementação | Hash de senha Werkzeug, CSRF Flask-WTF, parâmetros SQL, templates escapados, chaves estrangeiras, segredos por variável de ambiente |
| Verificação | Testes de RBAC, CSRF, injeção de papel, titularidade, rollback, concorrência, XSS e cabeçalhos; revisão humana de PR |
| Entrega | CI, branch/PR, configuração local e banco fora do Git; não executar seed em produção |
| Operação | Logs de endpoint/status sem senha ou payload; backup e monitoramento ainda não automatizados |

## Ameaças e riscos residuais

| Ameaça | Controle | Risco restante |
|---|---|---|
| Escalada de privilégio / IDOR | require_role, consultas por proprietário, testes 403 | Revisão contínua de novas rotas |
| CSRF | Token global, logout POST | Cookie Secure depende de HTTPS |
| SQL injection | Parâmetros para entrada de usuário, nomes de tabelas fixos | Não introduzir SQL dinâmico não controlado |
| XSS / clickjacking | Autoescape Jinja, CSP, X-Frame-Options | Imagens externas HTTPS e estilo inline |
| Força bruta / abuso | Hash, resposta genérica, limite de tamanho | Rate limit, lockout e monitoramento não implementados |
| Corrida e efeitos duplicados | BEGIN IMMEDIATE, índices únicos e teste de concorrência | SQLite serializa escritas; escala não avaliada |
| Vazamento de dados | Banco local fora do Git, no-store, logs sem payload | Backup, retenção, HTTPS, privacidade e gestão de segredos para produção |

Nenhum scan externo ou pentest foi executado nesta revisão. Antes de produção: revisar dependências e vulnerabilidades, TLS, rate limit, backups, retenção de logs e política de acesso. Não declarar conformidade legal ou segurança absoluta.
