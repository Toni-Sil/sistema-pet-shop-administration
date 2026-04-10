# Especificação de Segurança

## 1. Objetivos de segurança

- Proteger dados de clientes, pets, vendas e integrações (WhatsApp, Asaas).
- Minimizar impacto na experiência do usuário, priorizando controles "invisíveis" e autenticação de baixo atrito.
- Estar alinhado às boas práticas de OWASP Top 10:2025 (auth, controle de acesso, exposição de dados sensíveis, logs, rate limiting).

---

## 2. Autenticação

### 2.1. Login

- Autenticação via e-mail + senha forte (mínimo de requisitos de complexidade + checagem contra listas de senhas vazadas, se possível).
- Senhas **hash + salt** com algoritmo moderno (ex.: Argon2id, bcrypt com custo adequado).
- Limite de tentativas de login com backoff e bloqueio temporário (rate limiting em endpoint `/auth/login`).

### 2.2. Tokens e sessões

- Backend emite **JWT de acesso** de curta duração (15–30 min) + token de refresh de longa duração (8–12h).
- Opção de armazenar JWT em **cookie httpOnly + Secure** para mitigar XSS; se usar storage, reforçar CSP e sanitização.
- Revogação de tokens em eventos críticos: troca de senha, desativação de usuário, revogação manual por admin.
- "Lock screen" após inatividade prolongada: pedir apenas senha (ou MFA se configurado), mantendo o contexto sem jogar para o login completo.

### 2.3. MFA por risco

- MFA opcional por usuário, recomendada para donos/admin.
- **Risk-based MFA**: pedir confirmação extra apenas quando:
  - novo dispositivo detectado,
  - IP geograficamente distante do padrão,
  - múltiplas falhas de login em sequência,
  - horário de acesso muito fora do padrão.
- Permitir "lembrar este dispositivo" por N dias para reduzir atrito no dia a dia.

---

## 3. Autorização e papéis (RBAC)

- **Escopo por tenant**: todo usuário pertence a uma ou mais lojas (tenants); cada requisição carrega `tenant_id` e é validada no backend.
- Papéis disponíveis:

| Papel | Acesso |
|---|---|
| Dono / Administrador | Acesso total à loja |
| Financeiro | Financeiro + relatórios, sem configurações críticas |
| Atendente | Serviços + caixa, sem usuários nem configurações |
| Groomer / Vet | Agenda e atendimentos apenas |

- Autorização sempre validada no backend (middleware/policy por rota), nunca apenas no frontend.

---

## 4. Isolamento por cliente (tenant)

- Instância ou banco de dados separado por pet shop (modelo "tenant isolado"), reduzindo risco de vazamento cruzado.
- Onde houver multi-tenant, usar `tenant_id` em todas as queries + validação automática na camada de repositório.

---

## 5. Proteção de API e dados

### 5.1. Transporte

- Todo tráfego sobre HTTPS/TLS; HSTS ativado.
- Cabeçalhos de segurança obrigatórios: `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Strict-Transport-Security`.

### 5.2. Validação e sanitização

- Validação de entrada no backend (tipos, ranges, formatos) para todas as rotas públicas.
- Sanitização de campos de texto livre para mitigar XSS/HTML injection.
- Rate limiting em endpoints sensíveis: `/auth/login`, `/auth/reset-password`, `/payments/pix`, `/webhooks/*`.

### 5.3. Dados sensíveis

- Dados sensíveis em repouso com criptografia em nível de disco ou coluna: tokens de integração, segredos, dados fiscais.
- Nunca logar dados sensíveis em texto puro (senhas, tokens, dados de cartão).
- Princípio do menor privilégio: cada serviço e integração acessa somente o que precisa.

---

## 6. Integrações externas (Evolution API, Asaas, etc.)

- Credenciais **apenas em variáveis de ambiente / secret manager**, nunca no repositório.
- Webhooks protegidos com:
  - Autenticação via **HMAC/assinatura** em header (ex.: `X-Signature`), validada no backend antes de processar o payload.
  - Validação de IP remetente, quando suportado pelo provedor.
- Rotação de tokens/keys suportada: endpoint para atualizar credenciais e invalidar as antigas.
- Escopos mínimos solicitados em cada integração (princípio do menor privilégio).

---

## 7. Logs, auditoria e monitoramento

- Logar eventos-chave:
  - Logins (sucesso e falha), com IP aproximado, dispositivo e horário.
  - Alterações de senha e permissões.
  - Criação, edição e remoção de integrações.
  - Ações administrativas relevantes (ex.: excluir dados, desativar usuário).
- Logs com: timestamp, `user_id`, `tenant_id`, IP aproximado; **sem dados sensíveis**.
- Retenção: 6–12 meses; acesso restrito a admins e suporte.
- Alertas automáticos para padrões críticos (implementados via Agente de Segurança — ver `ai-security-agent.md`).

---

## 8. UX segura por padrão

- Mensagens de erro sem revelar detalhes internos:
  - ✅ "Usuário ou senha incorretos."
  - ❌ "Usuário não encontrado."
- Tela de "Configurações de segurança" para o usuário final com:
  - Alterar senha.
  - Ativar / desativar MFA.
  - Ver sessões ativas + "Encerrar outras sessões".
  - Ver e remover dispositivos confiáveis.
- Tooltips discretos em campos sensíveis explicando por que o dado é necessário.
- Notificações de segurança em linguagem simples, sem jargão técnico.
