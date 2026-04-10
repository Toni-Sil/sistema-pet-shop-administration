# 13 - Modo Offline e Contingência

## Objetivo

Definir o comportamento do sistema quando não houver conexão com a internet, garantindo que as operações críticas do pet shop (vendas, agenda, estoque) continuem funcionando, com sincronização automática ao reconectar.

> A perda de internet não pode travar o dia de trabalho do pet shop.

---

## 1. Princípios gerais

- **Graceful degradation**: o sistema deve degradar com elegância — funcionalidades críticas continuam, funcionalidades dependentes de internet ficam em espera.
- **Sync automático**: ao reconectar, tudo que foi feito offline é sincronizado de forma transparente, sem ação manual do usuário.
- **Fila persistente**: ações que dependem de internet (envio de nota fiscal, Pix, WhatsApp) ficam em fila persistente e são processadas na ordem ao voltar.
- **Transparência**: o sistema deve indicar claramente ao usuário quando está em modo offline e quais funções estão limitadas.

---

## 2. Detecção de modo offline

- Frontend monitora conectividade via `navigator.onLine` + health check periódico no backend (ex.: a cada 30 segundos).
- Ao detectar queda:
  - Exibir banner discreto no topo: "⚠️ Sem conexão — operando em modo offline. Suas ações serão sincronizadas ao reconectar."
  - Desabilitar botões de funções que exigem internet (emitir nota, pagar via Pix, enviar mensagem WhatsApp).
- Ao reconectar:
  - Banner muda para: "✅ Conexão restabelecida — sincronizando dados..."
  - Processar fila de ações pendentes automaticamente.

---

## 3. Funcionalidades por categoria

### 3.1 Funcionam offline ✅

| Funcionalidade | Como funciona offline |
|---|---|
| PDV — registrar venda | Salvar venda localmente (IndexedDB/cache); sync ao reconectar |
| Consultar agenda do dia | Dados já carregados ficam visíveis |
| Consultar estoque | Leitura dos dados em cache local |
| Cadastrar cliente/pet | Salvar localmente; sync ao reconectar |
| Registrar agendamento | Salvar localmente; sync ao reconectar |
| Registrar despesa | Salvar localmente; sync ao reconectar |
| Consultar histórico do pet | Leitura dos dados já carregados |

### 3.2 Funcionam parcialmente ⚠️

| Funcionalidade | Comportamento offline |
|---|---|
| Pagamento via Pix (Asaas) | Indisponível; sugerir dinheiro ou cartão presencial |
| Emissão de NFC-e/NF-e | Modo de contingência da SEFAZ (ver seção 4) |
| Relatórios com dados novos | Mostrar dados do último cache; avisar que pode estar desatualizado |

### 3.3 Indisponíveis offline ❌

| Funcionalidade | Motivo |
|---|---|
| Notificações WhatsApp | Depende de Evolution API; ficam em fila |
| Emissão de NFS-e | Depende de API da prefeitura |
| Agentes de IA | Dependem de LLM externo |
| Agente de segurança | Depende de backend em nuvem |
| Sincronização com marketplaces | Depende de APIs externas |

---

## 4. Contingência fiscal (NFC-e / NF-e sem internet)

A legislação brasileira prevê modos de contingência para emissão de NF-e e NFC-e quando a SEFAZ ou o provedor estão inacessíveis.

### 4.1 NFC-e em contingência

- Utilizar o modo **SVC-AN** ou **SVC-RS** (Serviço Virtual de Contingência), onde a nota é autorizada por um SEFAZ alternativo.
- O provedor de integração (ex.: PlugNotas, Tecnospeed) geralmente lida com isso automaticamente ao detectar indisponibilidade.
- Caso o provedor também esteja inacessível: registrar a venda internamente com `fiscal_status = 'pending'` e emitir nota quando a conexão voltar (dentro do prazo legal).

### 4.2 NF-e em contingência

- Modo **EPEC** (Evento Prévio de Emissão em Contingência): permite emitir NF-e com transmissão posterior.
- Implementar suporte a EPEC pelo provedor integrado.

### 4.3 Armazenamento obrigatório de XMLs

- Toda NF-e/NFC-e/NFS-e autorizada deve ter seu XML armazenado por **mínimo de 5 anos** (obrigação legal).
- Armazenamento em:
  - Bucket de objeto (ex.: S3, MinIO) gerenciado pelo sistema.
  - Backup periódico fora do servidor principal.
- Link para download do DANFE e XML disponível na tela de histórico fiscal.

### 4.4 Cancelamento e inutilização

- **Cancelamento**: permitido em até 30 minutos após autorização (para NFC-e) ou até 24h (para NF-e), via endpoint do provedor.
- **Inutilização**: quando uma numeração de nota não foi utilizada e precisa ser descartada legalmente.
- Ambas as operações devem ser registradas em log com motivo, usuário responsável e timestamp.
- Tela de histórico fiscal deve exibir status: `autorizada`, `cancelada`, `inutilizada`, `pendente`, `rejeitada`.

---

## 5. Fila de sincronização

Todas as ações realizadas offline são armazenadas em uma **fila persistente local** (IndexedDB no frontend ou tabela `sync_queue` no backend local, se houver).

### Estrutura da fila

```sql
CREATE TABLE sync_queue (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id     UUID NOT NULL,
  user_id      UUID,
  action       VARCHAR(50) NOT NULL,   -- 'create_sale', 'create_appointment', etc.
  payload      JSONB NOT NULL,          -- dados da ação
  status       VARCHAR(20) DEFAULT 'pending', -- pending|synced|failed
  attempts     INTEGER DEFAULT 0,
  error_msg    TEXT,
  created_at   TIMESTAMP DEFAULT NOW(),
  synced_at    TIMESTAMP
);
```

### Comportamento da fila

- Ao reconectar, processar fila em ordem de criação (`created_at ASC`).
- Em caso de conflito (ex.: produto já foi alterado por outro usuário), aplicar regra de **last-write-wins** para campos não críticos, e notificar o usuário para revisão em campos críticos (ex.: estoque).
- Após N tentativas falhas (ex.: 3), marcar como `failed` e notificar o admin com resumo do que não foi sincronizado.

---

## 6. Cache local

- Dados carregados ao abrir o sistema são armazenados em cache (IndexedDB ou service worker cache).
- Dados cacheados prioritários:
  - Agenda do dia e próximos 2 dias.
  - Lista completa de produtos (para PDV).
  - Lista de clientes e pets (para busca rápida).
  - Configurações da loja.
- Cache atualizado automaticamente a cada N minutos quando online.
- Expiração do cache: 24 horas (após isso, forçar reconexão para dados frescos).

---

## 7. UX do modo offline

- **Banner persistente** no topo enquanto offline, com cor de alerta (amarelo/laranja).
- Botões de funções indisponíveis ficam **desabilitados com tooltip explicativo**: ex.: "Emissão de nota indisponível sem conexão".
- Ao tentar usar função offline:
  - Não mostrar erro genérico.
  - Mostrar: "Esta função precisa de internet. Suas outras ações estão sendo salvas e serão enviadas ao reconectar."
- Indicador visual de itens na fila: "3 ações pendentes de sincronização".
- Após sync bem-sucedido: toast discreto "Tudo sincronizado ✅".

---

## 8. Relação com outros módulos

- **Módulo Financeiro (02):** vendas offline são registradas localmente e sincronizadas; Pix fica indisponível.
- **Módulo Fiscal (12):** contingência da SEFAZ entra automaticamente; XMLs armazenados localmente até sync.
- **Módulo de Agendamento (03):** agenda do dia fica disponível via cache; novos agendamentos vão para fila.
- **Módulo de Estoque (01):** leitura de estoque via cache; movimentações offline sincronizadas depois.
- **Agente de Segurança:** logs de eventos offline são armazenados localmente e sincronizados ao reconectar.
