# Execução inicial — Issue #5

Esta entrega implementa infraestrutura e autenticação. Os painéis são iniciais; agendamentos, estoque, financeiro e outras regras ainda serão implementados nas Issues correspondentes.

Python 3.12 recomendado. No terminal, a partir da raiz:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:BARBERFLOW_SECRET = (python -c "import secrets; print(secrets.token_hex(32))")
python -m flask --app src init-db
python -m flask --app src seed-demo
python -m flask --app src run
```

O comando seed-demo pede uma senha local (mínimo de 10 caracteres). Use exclusivamente dados fictícios. Os e-mails são cliente@example.test, barbeiro@example.test e admin@example.test. O comando create-admin permite criar um administrador local sem gerar contas de demonstração. Não execute seed-demo em produção.

Abra http://127.0.0.1:5000. Para testes: python -m pytest -q. Em Linux/macOS, ative com source .venv/bin/activate e export BARBERFLOW_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')".

O banco fica na pasta instance (ignorada pelo Git). init-db é não destrutivo; não constitui mecanismo completo de migrações. HTTPS, limitação de tentativas, políticas operacionais e revisão de segurança de produção estão fora desta entrega.
