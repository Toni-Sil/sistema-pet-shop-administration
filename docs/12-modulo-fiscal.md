# 12 - Módulo Fiscal (NF-e, NFC-e e NFS-e)

## Objetivo

Definir, em alto nível, como o sistema poderá lidar com emissão de **notas fiscais eletrônicas** para pet shops no Brasil, de forma incremental e flexível:

1. Começar com **NFC-e integrada ao PDV** (vendas de balcão para consumidor).
2. Evoluir para **NF-e** em vendas específicas (B2B, grande volume).
3. Adicionar **NFS-e** para serviços (banho, tosa, hospedagem, consultas) quando o módulo de serviços/CRM estiver consolidado.

> Este documento é instrucional. A implementação deverá ser feita em parceria com contador e adaptada à legislação de cada estado/município.

---

## 1. Tipos de Nota

### 1.1 NFC-e (Nota Fiscal do Consumidor Eletrônica)

- Uso principal: vendas de produtos no balcão (ração, brinquedos, medicamentos, acessórios).
- Substitui o cupom fiscal em grande parte dos estados.
- Ideal para integrar diretamente ao **PDV** do sistema. [web:102][web:105]

### 1.2 NF-e (Nota Fiscal Eletrônica)

- Uso principal: operações de mercadorias que exigem documentação mais completa, como:
  - Vendas para outras empresas (B2B).
  - Vendas interestaduais.
- Em pet shop, é mais comum em vendas em grande volume ou para clientes PJ. [web:99][web:111]

### 1.3 NFS-e (Nota Fiscal de Serviços Eletrônica)

- Uso principal: serviços prestados, como:
  - Banho, tosa, hospedagem.
  - Consultas e procedimentos veterinários.
- Em geral, emitida via sistema da prefeitura ou padrão nacional, com regras que variam por município. [web:99][web:104][web:111]

---

## 2. Estratégia de Implementação

### 2.1 Fase 1 – NFC-e integrada ao PDV

**Objetivo:** permitir que a venda no PDV já gere a NFC-e correspondente.

- Fluxo esperado no PDV:
  1. Operador registra itens no carrinho.
  2. Seleciona forma de pagamento (Pix, dinheiro, cartão). [cite:51]
  3. Ao finalizar, o sistema:
     - Cria registro de venda (módulo financeiro).
     - Baixa estoque (módulo de estoque). [cite:50]
     - Dispara requisição para emissão de NFC-e.

- Recomendação: usar **API de terceiros** (ex.: PlugNotas/Tecnospeed/NFe.io) em vez de integrar diretamente com cada SEFAZ estadual, para simplificar:
  - Backend envia JSON com dados da venda (produtos, CFOP, NCM, CST/CSOSN, alíquotas, dados do emitente/destinatário).
  - API externa cuida de XML, assinatura, autorização, contingência e armazenamento do DANFE. [web:100][web:106][web:109]

### 2.2 Fase 2 – NF-e para operações específicas

**Quando ativar:**
- Quando um cliente do sistema precisar emitir NF-e para vendas específicas (B2B, grandes volumes, interestaduais).

**Estratégia:**
- Reaproveitar a integração da Fase 1 com o mesmo provedor (endpoint de NF-e).
- Permitir que o usuário escolha, por venda, se deseja NFC-e ou NF-e (conforme regras e orientação do contador).

### 2.3 Fase 3 – NFS-e para serviços

**Quando ativar:**
- Após o módulo de serviços/CRM estar estável (agendamento, CRM, histórico clínico). [cite:49]

**Estratégia:**
- Permitir configuração de municípios/credenciais de NFS-e por loja.
- Usar, se possível, API que normalize chamadas a múltiplas prefeituras.
- Associar notas de serviço a:
  - `appointments` (agendamentos realizados).
  - `services` (tipos de serviço cadastrados).

---

## 3. Campos Fiscais Mínimos

### 3.1 Por Produto

Além dos campos já definidos em `products` (nome, preços, categoria, etc.), será necessário acrescentar campos fiscais (a serem detalhados com contador): [cite:50]

- `ncm` – Nomenclatura Comum do Mercosul.
- `cfop` – Código Fiscal de Operações e Prestações.
- `cst` ou `csosn` – Situação tributária.
- `origem` – Origem da mercadoria.
- `aliquota_icms`, `aliquota_pis`, `aliquota_cofins` (quando aplicável).

Esses campos podem ser configurados:
- Diretamente no cadastro de produto.
- Ou herdados de uma **configuração padrão** por categoria.

### 3.2 Por Serviço (NFS-e)

- Código de serviço municipal.
- Descrição padrão para nota.
- Aliquota de ISS.

### 3.3 Configurações da Loja

- Dados do emitente (CNPJ, IE, endereço, regime tributário, CNAE, etc.).
- Certificado digital (quando necessário) ou credenciais do provedor de notas.
- Série/numeração de nota (controlada pelo provedor ou sistema, conforme caso).

---

## 4. Integração com o Módulo Financeiro

O módulo fiscal deve se integrar principalmente com o **módulo financeiro/PDV**:

- Cada `sale` pode ter um campo `fiscal_status` e `fiscal_document_id`:

```sql
ALTER TABLE sales
  ADD COLUMN fiscal_status VARCHAR(20) DEFAULT 'none',
  ADD COLUMN fiscal_document_id VARCHAR(255);
```

- Possíveis valores para `fiscal_status`:
  - `none` – sem emissão.
  - `pending` – emissão solicitada, aguardando retorno.
  - `authorized` – nota autorizada.
  - `rejected` – rejeitada (com motivo armazenado em tabela de log).

- A aplicação deve permitir:
  - Visualizar o status fiscal de cada venda.
  - Reenviar tentativas (quando permitido).
  - Baixar/visualizar DANFE ou espelho da nota.

---

## 5. Telas e Configurações

### 5.1 Tela de Configurações Fiscais

- Local: painel do dono/administrador da loja.
- Itens mínimos:
  - Dados cadastrais da empresa (CNPJ, IE, regime tributário).
  - Seleção/integração com provedor de notas (ex.: PlugNotas) + credenciais.
  - Estado/município de atuação.
  - Parâmetros padrões (CFOP, CST/CSOSN padrão por operação).

### 5.2 Tela de Histórico Fiscal

- Listagem de notas emitidas (NFC-e, NF-e, NFS-e) com filtros por período, status, tipo.
- Acesso rápido a PDFs/XMLs via links fornecidos pelo provedor.

---

## 6. Papel do Contador

O sistema deve **facilitar** a vida do contador, não substituí-lo:

- Permitir exportar dados consolidados (XMLs/CSVs) para conferência.
- Permitir que o contador configure regras fiscais (CFOP, CST, NCM, alíquotas) em conjunto com o dono.
- Deixar claro, na documentação, que a responsabilidade por parametrização fiscal é compartilhada com o contador. [web:99][web:107][web:108]

---

## 7. Relação com outros módulos

- **Módulo Financeiro (02):** origem das vendas e pagamentos; controla caixa e relatórios financeiros. [cite:51]
- **Módulo de Estoque (01):** fornece informações sobre produtos e garante baixa de estoque quando a venda é concluída. [cite:50]
- **Módulo de Serviços/CRM (03/04):** base para emissão de NFS-e associada a serviços e histórico de pets/tutores. [cite:49]

A implementação do módulo fiscal deve respeitar o roadmap: começar simples (NFC-e no PDV via API de terceiros) e evoluir conforme a demanda real dos clientes e a maturidade dos demais módulos.
