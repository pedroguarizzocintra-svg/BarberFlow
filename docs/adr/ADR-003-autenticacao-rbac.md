# ADR-003 — Autenticação por sessão e controle de acesso por perfil

**Status:** Proposto, aguardando revisão | **Issue:** #4 | **Data:** 2026-11-26

## Contexto

A spec define cliente, barbeiro e administrador com permissões distintas. Informações de clientes e receitas não devem ser visíveis a usuários não autorizados.

## Decisão

Utilizar sessão Flask com chave secreta externa ao Git, hash salgado de senha via Werkzeug e CSRF via Flask-WTF. Cadastro público apenas para cliente, provisionamento de profissionais/admin por acesso autorizado e primeiro admin via comando local. Autorizar operações por papel e titularidade no servidor. Cookies HttpOnly, SameSite=Lax e Secure em HTTPS.

## Alternativas consideradas

JWT adicionaria gestão de tokens sem necessidade para aplicação renderizada no servidor. Login terceirizado dependeria de serviço externo. Controle só no frontend não protege dados.

## Consequências

Reduz exposição e facilita testes. Sessão assinada não é armazenamento de segredos; guardar somente identificadores mínimos. TLS, rate limiting, recuperação de conta e revisão de implantação são necessários antes de produção. Dados fictícios na demonstração.

## Rastreabilidade

RF-01–03, RF-06, RF-33–35; RNF-01–02, RNF-08; RN-10, RN-20; Issues #5, #14–15. Consulte [spec.md](../../spec.md) e [plan.md](../../plan.md) (proposta da Issue #2).

Elaboração assistida por IA; decisão sujeita à validação humana. Não constitui evidência de implementação ou teste.
