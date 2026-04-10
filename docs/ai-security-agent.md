# Agente de Segurança (IA)

## 1. Objetivo

O Agente de Segurança é um agente de IA dedicado à **observabilidade, detecção de anomalias e recomendação de resposta** dentro do sistema.

Ele **não substitui** controles tradicionais (autenticação, RBAC, rate limiting, validação de entrada) — atua como uma camada adicional de inteligência sobre os logs e métricas gerados por esses controles.

---

## 2. Fontes de dados

O agente acessa **somente**:

- Logs de autenticação (logins com sucesso/falha, IP aproximado, dispositivo, horário).
- Logs de ações administrativas (criação/remoção de usuários, mudança de papel, alteração de integrações).
- Métricas de uso agregadas por tenant (volume de logins por hora, número de webhooks, volume de vendas, etc.).

**Nunca acessa:**
- Senhas ou hashes de senhas.
- Conteúdo de mensagens de clientes.
- Dados de cartão ou detalhes bancários.
- Dados médicos ou de fichas dos pets.

---

## 3. Capacidades

### 3.1. Detecção de anomalias

O agente aprende o padrão "normal" de cada tenant e sinaliza eventos fora do padrão, como:

| Evento detectado | Exemplo |
|---|---|
| Múltiplos logins falhos | 10+ tentativas em 2 minutos |
| Login em horário incomum | Acesso às 3h quando o padrão é 8h–20h |
| Novo dispositivo ou IP distante | IP de outro estado/país |
| Explosão de chamadas em webhook | 500 chamadas em 1 min quando a média é 10 |
| Ações administrativas incomuns | 20 usuários desativados em sequência |

### 3.2. Resumo de incidentes

Quando um padrão atípico é detectado, o agente gera um **resumo em linguagem simples** para o painel de administração:

> _"No dia 10/04/2026, entre 02:15 e 02:32, foram registradas 47 tentativas de login falhas para a conta admin@loja.com, originadas de um IP não reconhecido (187.x.x.x). As tentativas cessaram após o bloqueio automático do IP."_

### 3.3. Sugestão de ações

O agente sugere ações proporcionais ao risco detectado:

- Baixo risco: alertas informativos no painel.
- Médio risco: sugestão de encerrar sessões suspeitas ou forçar nova autenticação.
- Alto risco: sugestão de suspender usuário, revogar integração, ou forçar redefinição de senha.

> ⚠️ **Todas as ações requerem confirmação humana (human-in-the-loop)** antes de serem executadas.

---

## 4. Limitações e salvaguardas

O agente **não pode, em nenhuma circunstância**:

- Excluir dados permanentemente.
- Alterar permissões de usuários.
- Modificar configurações de segurança sem confirmação de um usuário com papel adequado.
- Acessar dados sensíveis além das fontes listadas na seção 2.

Todas as ações sugeridas e aprovadas são registradas em log com:
- Timestamp.
- ID do usuário que aprovou.
- Contexto do incidente.
- Resultado da ação.

---

## 5. Interface (UX do agente)

### Painel "Segurança" (visível para Dono / Administrador)

- Lista de alertas recentes com nível de severidade:
  - 🔵 Informativo
  - 🟡 Aviso
  - 🔴 Crítico
- Resumo de cada incidente em linguagem simples.
- Botões de ação por alerta:
  - "Aplicar sugestão" — executa a ação recomendada.
  - "Ignorar" — descarta o alerta com justificativa opcional.
  - "Ver detalhes técnicos" — exibe log bruto para quem quiser aprofundar.

### Notificações no app

- Notificações discretas (banner/toast) apenas para eventos relevantes.
- Linguagem simples, sem jargão:
  - ✅ _"Detectamos um acesso suspeito à sua conta. Já encerramos a sessão desse dispositivo e recomendamos redefinir sua senha."_
  - ❌ _"Anomalia detectada: IP 187.x.x.x com score de risco 0.87 excedeu threshold."_

---

## 6. Roadmap do agente

| Fase | Funcionalidade |
|---|---|
| v1.0 | Detecção de brute force + alertas básicos |
| v1.5 | Detecção de padrão por horário e dispositivo |
| v2.0 | Anomalias em webhooks e integrações |
| v2.5 | Resumo automático de incidentes com LLM |
| v3.0 | Sugestões de resposta e ações com aprovação humana |
