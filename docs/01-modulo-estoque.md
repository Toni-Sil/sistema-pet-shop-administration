# 01 - Modulo de Estoque

**Status:** MVP | **Prioridade:** Alta | **Sprint:** 1-2

---

## User Stories

### US-01: Cadastro de Produto
> Como funcionario, quero cadastrar um produto com nome, SKU, preco de custo, preco de venda, quantidade minima e data de validade.

**Criterios de Aceite:**
- [ ] Campo SKU unico por loja
- [ ] Preco de venda deve ser maior que preco de custo
- [ ] Data de validade opcional (produtos sem validade aceitos)
- [ ] Categoria obrigatoria (Racao, Medicamento, Acessorio, Higiene, Outro)
- [ ] Foto do produto opcional (upload)

### US-02: Entrada de Estoque
> Como funcionario, quero registrar entrada de produtos (compra de fornecedor) para atualizar o estoque.

**Criterios de Aceite:**
- [ ] Selecionar produto existente ou cadastrar novo
- [ ] Informar quantidade, preco de custo e fornecedor
- [ ] Gerar historico de entrada com data e usuario
- [ ] Atualizar saldo de estoque automaticamente

### US-03: Saida de Estoque
> Como sistema, quero baixar o estoque automaticamente quando uma venda e finalizada no PDV.

**Criterios de Aceite:**
- [ ] Saida vinculada a venda no modulo financeiro
- [ ] Saida manual disponivel para perdas/ajustes
- [ ] Motivo obrigatorio em saidas manuais
- [ ] Nao permitir saldo negativo (bloquear venda se sem estoque)

### US-04: Alerta de Estoque Baixo
> Como dono, quero receber alerta quando produto atingir quantidade minima.

**Criterios de Aceite:**
- [ ] Alerta no dashboard (badge vermelho)
- [ ] Lista de produtos criticos na tela de estoque
- [ ] Notificacao por email (opcional, configuravel)

### US-05: Alerta de Vencimento
> Como dono, quero ver produtos proximos ao vencimento (30 dias) e vencidos.

**Criterios de Aceite:**
- [ ] Painel de vencimentos na tela de estoque
- [ ] Categorias: Vencido (vermelho), Vence em 7 dias (laranja), Vence em 30 dias (amarelo)
- [ ] Exportar lista de vencidos em CSV

### US-06: Relatorio de Estoque
> Como dono, quero ver relatorio completo do estoque atual com valor total.

**Criterios de Aceite:**
- [ ] Lista paginada com filtro por categoria
- [ ] Valor total em estoque (quantidade x preco custo)
- [ ] Exportar em PDF e CSV

---

## Endpoints da API

```
GET    /api/products              - Listar produtos (paginado, filtros)
POST   /api/products              - Cadastrar produto
GET    /api/products/{id}         - Detalhe do produto
PUT    /api/products/{id}         - Atualizar produto
DELETE /api/products/{id}         - Desativar produto (soft delete)

GET    /api/stock/movements        - Historico de movimentacoes
POST   /api/stock/entry            - Entrada de estoque
POST   /api/stock/exit             - Saida manual de estoque

GET    /api/stock/alerts           - Produtos com estoque baixo
GET    /api/stock/expiring         - Produtos proximos ao vencimento
GET    /api/stock/report           - Relatorio completo
```

---

## Schema de Dados

```sql
-- Produtos
CREATE TABLE products (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id    UUID NOT NULL REFERENCES stores(id),
  name        VARCHAR(255) NOT NULL,
  sku         VARCHAR(100) UNIQUE,
  category    VARCHAR(50) NOT NULL,
  cost_price  DECIMAL(10,2) NOT NULL,
  sale_price  DECIMAL(10,2) NOT NULL,
  quantity    INTEGER NOT NULL DEFAULT 0,
  min_qty     INTEGER NOT NULL DEFAULT 5,
  expires_at  DATE,
  image_url   TEXT,
  is_active   BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMP DEFAULT NOW()
);

-- Movimentacoes de Estoque
CREATE TABLE stock_movements (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id  UUID NOT NULL REFERENCES products(id),
  type        VARCHAR(10) NOT NULL, -- 'entry' | 'exit'
  quantity    INTEGER NOT NULL,
  reason      VARCHAR(100),         -- 'purchase' | 'sale' | 'loss' | 'adjust'
  cost_price  DECIMAL(10,2),
  supplier    VARCHAR(255),
  user_id     UUID REFERENCES users(id),
  created_at  TIMESTAMP DEFAULT NOW()
);
```

---

## Regras de Negocio

1. **Saldo negativo bloqueado:** Sistema nao permite saida maior que saldo disponivel
2. **SKU unico por loja:** Mesmo SKU pode existir em lojas diferentes
3. **Soft delete:** Produtos nao sao deletados, apenas desativados
4. **Historico imutavel:** Movimentacoes de estoque nao podem ser editadas, apenas estornadas
5. **Calculo de margem:** Sistema mostra margem de lucro automaticamente (preco venda - custo) / custo

---

## Componentes de Frontend

```
src/pages/stock/
  ProductList.tsx       - Lista principal com filtros
  ProductForm.tsx       - Formulario de cadastro/edicao
  ProductDetail.tsx     - Detalhe com historico de movimentacoes
  StockEntry.tsx        - Tela de entrada de estoque
  StockAlerts.tsx       - Painel de alertas (criticos + vencimentos)
  StockReport.tsx       - Relatorio exportavel

src/components/stock/
  ProductCard.tsx       - Card do produto
  StockBadge.tsx        - Badge de status (ok/baixo/critico)
  ExpirationTag.tsx     - Tag de vencimento colorida
  MovementHistory.tsx   - Tabela de historico
```

---

## Dependencias

- Modulo Financeiro (saida automatica ao finalizar venda)
- Auth (usuario logado para auditoria)

---

## Criterios de Conclusao (Definition of Done)

- [ ] Todos os endpoints implementados e testados
- [ ] Testes unitarios com cobertura > 80%
- [ ] Tela de lista, cadastro e alertas funcionando
- [ ] Alerta de estoque baixo aparece no dashboard
- [ ] Exportacao CSV funcionando
- [ ] Documentacao Swagger atualizada


---

## Leitura de Código de Barras e QR Code

**Referência:** Consultar `skills/09-skill-codigo-barras-qrcode.md` para implementação detalhada.

### Objetivo

Permitir busca rápida de produtos usando scanner USB (pistola) ou câmera (QR Code) para otimizar o fluxo de entrada de estoque e vendas.

### Tipos de Leitura Suportados

1. **Scanner USB** (recomendado para desktop)
   - Funciona como teclado virtual
   - Digita o código e pressiona Enter automaticamente
   - Zero configuração necessária no software

2. **Câmera** (futuro - opcional)
   - Leitura via webcam ou celular
   - Requer biblioteca `pyzbar` (backend) ou `html5-qrcode` (frontend)

### Funcionamento

```
Funcionário escaneia código de barras/QR Code
        ↓
Sistema busca produto pelo campo `codigo_barras`
        ↓
Exibe dados do produto (nome, preço, estoque atual)
        ↓
Funcionário confirma quantidade
        ↓
Registra movimentação de estoque
```

### Endpoint Adicional

```
GET  /api/products/barcode/{codigo}  - Busca produto por código de barras
```

### Campo no Banco de Dados

O campo `codigo_barras` no modelo `Produto` já suporta:
- Códigos de barras 1D (EAN-13, Code 128, etc.)
- QR Code
- Qualquer string alfanumérica de até 100 caracteres
- **Tem índice** para busca rápida

### Componente Frontend

```
src/components/estoque/
  ScannerInput.tsx      - Input com autoFocus para scanner USB
  CameraScanner.tsx     - (futuro) Leitura via câmera
```

### Fluxo de Uso Principal

1. **Entrada de Estoque:**
   - Funcionário acessa tela de movimentação
   - Posiciona cursor no campo de busca (autoFocus)
   - Escaneia produto com pistola USB
   - Sistema busca e exibe produto
   - Confirma quantidade e registra entrada

2. **Venda no PDV:**
   - Cliente traz produtos
   - Operador escaneia cada item
   - Produtos são adicionados ao carrinho
   - Finaliza venda

### Hardware Recomendado

- **Scanner USB básico:** R$ 80-150 (Honeywell, Datalogic)
- **Scanner Bluetooth:** R$ 200-400 (mobilidade para inventário)

### Boas Práticas

- [ ] Campo de input sempre com `autoFocus`
- [ ] Limpar campo após scan bem-sucedido
- [ ] Feedback visual imediato (loading/sucesso/erro)
- [ ] Emitir beep sonoro ao encontrar produto (opcional)
- [ ] Validar formato do código antes de buscar


---

## Venda por Peso (kg/g)

### Objetivo

Suportar produtos vendidos por peso (ração a granel, petiscos naturais, areia) com precificação automática baseada no peso.

### US-07: Cadastro de Produto por Peso

> Como funcionário, quero cadastrar produtos que são vendidos por peso, informando o preço por kg.

**Critérios de Aceite:**

- [ ] Campo `sale_type` com opções: UNIT (unidade) ou WEIGHT (peso)
- [ ] Para produtos WEIGHT: campo `weight_in_stock` (kg) obrigatório
- [ ] Preço por kg informado no campo `sale_price`
- [ ] Quantidade mínima em kg para alerta de estoque baixo
- [ ] Estoque mostrado em kg com 3 casas decimais (ex: 45.250 kg)

### US-08: Venda com Balança

> Como operador de caixa, quero pesar o produto na balança e o sistema calcular automaticamente o valor total.

**Critérios de Aceite:**

- [ ] Botão "Ler da Balança" integrado com balança USB/Serial
- [ ] Campo manual para digitar peso caso balança não esteja disponível
- [ ] Cálculo automático: `peso (kg) × preço/kg = total`
- [ ] Exibir peso com 3 casas decimais (ex: 2.350 kg)
- [ ] Total calculado em tempo real ao alterar peso
- [ ] Validar que peso não excede estoque disponível

### Exemplos de Uso

**Exemplo 1: Ração a Granel**
```
Produto: Ração Premium Adulto
- Tipo: WEIGHT
- Preço: R$ 28,00/kg
- Estoque: 45.500 kg

Venda:
- Cliente quer: 3.5 kg
- Total: 3.5 × R$ 28,00 = R$ 98,00
- Estoque após venda: 42.000 kg
```

**Exemplo 2: Petisco Natural**
```
Produto: Bifinho de Fígado
- Tipo: WEIGHT  
- Preço: R$ 85,00/kg
- Estoque: 2.800 kg

Venda:
- Cliente quer: 0.250 kg (250g)
- Total: 0.250 × R$ 85,00 = R$ 21,25
- Estoque após venda: 2.550 kg
```

### Schema de Dados (Atualizado)

```sql
-- Produtos com suporte a peso
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  store_id UUID NOT NULL REFERENCES stores(id),
  name VARCHAR(255) NOT NULL,
  sku VARCHAR(100) UNIQUE,
  category VARCHAR(50) NOT NULL,
  codigo_barras VARCHAR(100), -- Para scanner
  
  -- Tipo de venda
  sale_type VARCHAR(20) NOT NULL DEFAULT 'UNIT',
  -- 'UNIT' = unidade | 'WEIGHT' = peso
  
  -- Preços
  cost_price DECIMAL(10, 2) NOT NULL,
  sale_price DECIMAL(10, 2) NOT NULL,
  
  -- Para venda por UNIDADE
  quantity INTEGER,
  min_qty INTEGER DEFAULT 5,
  
  -- Para venda por PESO  
  weight_in_stock DECIMAL(10, 3), -- kg
  min_weight DECIMAL(10, 3), -- alerta se < X kg
  
  -- Comum
  expires_at DATE,
  image_url TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  
  -- Constraints
  CONSTRAINT valid_sale_type CHECK (sale_type IN ('UNIT', 'WEIGHT')),
  CONSTRAINT unit_requires_quantity CHECK (
    (sale_type = 'UNIT' AND quantity IS NOT NULL) OR
    (sale_type = 'WEIGHT' AND weight_in_stock IS NOT NULL)
  )
);

-- Movimentações com suporte a peso
CREATE TABLE stock_movements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID NOT NULL REFERENCES products(id),
  type VARCHAR(10) NOT NULL, -- 'entry' | 'exit'
  
  -- Para UNIT
  quantity INTEGER,
  
  -- Para WEIGHT
  weight DECIMAL(10, 3), -- kg
  
  reason VARCHAR(100), -- 'purchase' | 'sale' | 'loss' | 'adjust'
  cost_price DECIMAL(10, 2),
  supplier VARCHAR(255),
  user_id UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT movement_has_qty_or_weight CHECK (
    quantity IS NOT NULL OR weight IS NOT NULL
  )
);
```

### Endpoints da API (Adicionais)

```
GET  /api/scale/weight           - Ler peso atual da balança
POST /api/sales/items/by-weight  - Adicionar item por peso ao carrinho
GET  /api/products/by-weight     - Listar apenas produtos vendidos por peso
```

### Componentes de Frontend (Adicionais)

```
src/components/sales/
  WeightInput.tsx        - Input com botão "Ler da Balança"
  WeightProductCard.tsx  - Card de produto com cálculo por peso
  ScaleReader.tsx        - Integração com balança USB/Serial
  
src/pages/stock/
  WeightProductForm.tsx  - Formulário para produto por peso
```

### Integração com Balança

#### Balanças Suportadas:
- **Toledo Prix 3**
- **Filizola Platina**
- **Urano POP-Z**
- **Generic USB Scale** (protocolo HID)

#### Protocolo de Comunicação:

```python
# Backend: utils/scale.py
import serial
import re

class Scale:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=1,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
    
    def read_weight(self) -> float:
        """Ler peso da balança em kg"""
        # Enviar comando de leitura
        self.serial.write(b'\x05')  # ENQ (request)
        
        # Ler resposta
        response = self.serial.readline()
        
        # Parse: formato comum "  2.350 kg\r\n"
        weight_match = re.search(r'([0-9]+\.[0-9]+)', response.decode())
        
        if weight_match:
            weight_kg = float(weight_match.group(1))
            return round(weight_kg, 3)
        
        raise ValueError("Não foi possível ler o peso")
    
    def tare(self):
        """Zerar/Tarar balança"""
        self.serial.write(b'T')
```

#### Endpoint FastAPI:

```python
from fastapi import APIRouter, HTTPException
from utils.scale import Scale

router = APIRouter()

@router.get("/api/scale/weight")
async def get_scale_weight():
    """Obter peso atual da balança"""
    try:
        scale = Scale()
        weight = scale.read_weight()
        return {
            "weight_kg": weight,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(500, f"Erro ao ler balança: {str(e)}")

@router.post("/api/scale/tare")
async def tare_scale():
    """Zerar/Tarar balança"""
    scale = Scale()
    scale.tare()
    return {"status": "tared"}
```

### Regras de Negócio Adicionais

1. **Conversão de Unidades:**
   - Sistema armazena sempre em kg
   - Interface pode exibir em g (multiplicar por 1000)
   - Exemplo: 0.250 kg = 250 g

2. **Precisão:**
   - Estoque: 3 casas decimais (0.001 kg = 1g)
   - Preço: 2 casas decimais (centavos)
   - Total: 2 casas decimais (centavos)

3. **Validações:**
   - Peso mínimo: 0.001 kg (1g)
   - Peso máximo por venda: não exceder estoque
   - Alerta se estoque < `min_weight`

4. **Relatórios:**
   - Valor total em estoque (peso): `Σ(weight_in_stock × cost_price)`
   - Produtos mais vendidos por peso (kg/mês)

### Fluxo de Venda Completo

```
1. Operador inicia venda no PDV
2. Escaneia código de barras ou busca produto
3. Sistema identifica: sale_type = WEIGHT
4. Exibe interface de peso:
   - Botão "Ler da Balança"
   - Campo manual para peso
5. Operador:
   a) Clica "Ler da Balança" → peso automático
   OU
   b) Digita peso manualmente
6. Sistema calcula: peso × preço/kg = total
7. Operador confirma
8. Item adicionado ao carrinho
9. Estoque atualizado: weight_in_stock -= peso_vendido
```

### Configuração de Balança

```yaml
# .env
SCALE_ENABLED=true
SCALE_PORT=/dev/ttyUSB0
SCALE_BAUDRATE=9600
SCALE_TIMEOUT=2
SCALE_MODEL=toledo_prix3
```

### Testes

```python
# tests/test_weight_sales.py
import pytest

def test_weight_product_creation():
    product = create_product(
        name="Ração Granel",
        sale_type="WEIGHT",
        sale_price=28.00,
        weight_in_stock=50.0
    )
    assert product.sale_type == "WEIGHT"
    assert product.weight_in_stock == 50.0

def test_weight_sale_calculation():
    product = get_product(sale_type="WEIGHT", sale_price=28.00)
    weight = 3.5
    total = weight * product.sale_price
    assert total == 98.00

def test_weight_stock_update():
    product = get_product(weight_in_stock=50.0)
    sell_weight(product.id, weight=3.5)
    product.refresh()
    assert product.weight_in_stock == 46.5

def test_scale_reading():
    scale = Scale()
    weight = scale.read_weight()
    assert 0 < weight < 50  # peso razoável
    assert isinstance(weight, float)
```

### Alertas Específicos para Peso

- **Estoque Baixo:** `weight_in_stock < min_weight`
- **Estoque Crítico:** `weight_in_stock < (min_weight / 2)`
- **Balança Offline:** Permitir venda manual digitando peso
- **Peso Inválido:** Rejeitar se `weight <= 0` ou `weight > weight_in_stock`
