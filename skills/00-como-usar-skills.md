# Skills de IA - Como Usar

Esta pasta contem **skills especializadas** para guiar a IA (Cursor, Copilot, Claude) no desenvolvimento deste sistema.

Cada skill e um arquivo de contexto que deve ser fornecido para a IA **antes de pedir para gerar codigo** de um modulo especifico.

---

## Como Usar no Cursor

### Metodo 1: @file direto no chat
```
@skills/01-skill-fastapi-backend.md
@docs/01-modulo-estoque.md

Implemente o endpoint POST /api/products seguindo as specs acima.
```

### Metodo 2: Adicionar como contexto persistente
1. Abra o Cursor Settings
2. Va em Rules for AI
3. Cole o conteudo da skill relevante
4. A IA vai seguir as convencoes em todos os chats

### Metodo 3: .cursorrules (recomendado)
Crie um arquivo `.cursorrules` na raiz do projeto com as skills mais importantes concatenadas. A IA vai ler automaticamente em todo chat.

---

## Qual Skill Usar em Cada Situacao

| Voce quer fazer... | Skill para incluir |
|--------------------|-----------------|
| Criar endpoint FastAPI | `01-skill-fastapi-backend.md` |
| Criar migration / model | `02-skill-sqlalchemy-alembic.md` |
| Criar tela React | `03-skill-react-frontend.md` |
| Implementar login/MFA | `04-skill-auth-jwt-mfa.md` |
| Integrar pagamento Pix | `05-skill-integracao-asaas-pix.md` |
| Integrar WhatsApp | `06-skill-evolution-api-whatsapp.md` |
| Configurar Docker/Deploy | `07-skill-docker-deploy.md` |
| Adicionar funcao com IA | `08-skill-openai-ia.md` |

---

## Fluxo Recomendado por Sprint

### Sprint 1 (Fundacao + Auth)
```
@skills/01-skill-fastapi-backend.md
@skills/02-skill-sqlalchemy-alembic.md
@skills/04-skill-auth-jwt-mfa.md
@docs/05-arquitetura-tecnica.md
@docs/06-banco-de-dados.md
```

### Sprint 2 (Estoque)
```
@skills/01-skill-fastapi-backend.md
@skills/02-skill-sqlalchemy-alembic.md
@skills/03-skill-react-frontend.md
@docs/01-modulo-estoque.md
```

### Sprint 3 (Financeiro + PDV)
```
@skills/01-skill-fastapi-backend.md
@skills/03-skill-react-frontend.md
@skills/05-skill-integracao-asaas-pix.md
@docs/02-modulo-financeiro.md
```

### Sprint 5 (Agendamento + WhatsApp)
```
@skills/01-skill-fastapi-backend.md
@skills/03-skill-react-frontend.md
@skills/06-skill-evolution-api-whatsapp.md
@docs/03-modulo-agendamento.md
```

---

## Regras Globais para a IA

Sempre que gerar codigo neste projeto, a IA DEVE:

1. **Seguir o SDD** - nao inventar features que nao estao nos docs
2. **Usar UUID** como chave primaria em todos os models
3. **Incluir store_id** em todos os models (isolamento por loja)
4. **Usar async/await** em todos os endpoints FastAPI
5. **Validar com Pydantic v2** em todos os schemas
6. **Retornar erros padronizados** no formato `{detail: string, code: string}`
7. **Nunca deletar registros** - usar soft delete (`is_active = False`)
8. **Sempre tipar** variaveis em TypeScript e Python
9. **Nomear em ingles** variaveis, funcoes e arquivos
10. **Comentar em portugues** logica complexa de negocio

---

## Estrutura de Prompt Ideal

```
[CONTEXTO DO PROJETO]
@skills/XX-skill-relevante.md
@docs/XX-modulo-relevante.md

[TAREFA ESPECIFICA]
Implemente o [nome da feature] seguindo:
- User Story: US-XX do modulo XX
- Endpoint: METHOD /api/rota
- Schema: tabela_relevante
- Regras de negocio: item 1, item 2

[RESTRICOES]
- Nao criar novas tabelas
- Reutilizar o servico X ja existente
- Seguir o padrao de resposta dos outros endpoints
```

---

## Arquivos de Skill Disponiveis

```
skills/
  00-como-usar-skills.md          <- Este arquivo
  01-skill-fastapi-backend.md     <- Padroes FastAPI, routers, middlewares
  02-skill-sqlalchemy-alembic.md  <- Models, migrations, queries
  03-skill-react-frontend.md      <- Componentes, hooks, estado, formularios
  04-skill-auth-jwt-mfa.md        <- Login, JWT, refresh, MFA TOTP
  05-skill-integracao-asaas-pix.md <- Cobranca Pix, webhook, QR Code
  06-skill-evolution-api-whatsapp.md <- Envio de mensagens, conexao
  07-skill-docker-deploy.md       <- Compose, Dokploy, Traefik, CI/CD
  08-skill-openai-ia.md           <- Prompts, streaming, funcoes com IA
```
