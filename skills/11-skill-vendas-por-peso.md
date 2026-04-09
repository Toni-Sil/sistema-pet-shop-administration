# Skill: Vendas por Peso

## Objetivo

Implementar suporte a produtos vendidos por peso (ração a granel, petiscos, areia) com integração a balanças e precificação automática.

---

## Quando Usar Esta Skill

- Desenvolver formulário de cadastro de produtos por peso
- Implementar lógica de cálculo `peso * preço/kg`
- Integrar com balanças USB/Serial
- Gerar relatórios de estoque em kg
- Criar validações de estoque fracionado

---

## Modelagem de Dados

### Modelo de Produto (SQLAlchemy)

```python
# models/product.py
from sqlalchemy import Column, String, Numeric, Integer, Enum
import enum

class SaleType(str, Enum):
    UNIT = "UNIT"
    WEIGHT = "WEIGHT"

class Product(Base):
    __tablename__ = "products"
    
    # ... outros campos
    sale_type = Column(String, default=SaleType.UNIT)
    
    # Estoque Unidade
    quantity = Column(Integer, nullable=True)
    
    # Estoque Peso (kg)
    weight_in_stock = Column(Numeric(precision=10, scale=3), nullable=True)
    
    # Preço pode ser por Unidade ou por KG
    sale_price = Column(Numeric(precision=10, scale=2), nullable=False)
```

---

## Lógica de Negócio

### Cálculo de Preço

```python
# utils/pricing.py
from decimal import Decimal

def calculate_item_total(sale_type: str, price_per_unit: Decimal, amount: Decimal) -> Decimal:
    \"\"\"
    Calcula o total do item
    amount pode ser Quantidade (int) ou Peso (kg)
    \"\"\"
    return (price_per_unit * amount).quantize(Decimal('0.01'))
```

---

## Integração com Balança (Backend)

### Leitor de Balança Serial

```python
# utils/scale_reader.py
import serial
import re

class ScaleReader:
    def __init__(self, port='/dev/ttyUSB0'):
        self.port = port
        
    def get_weight(self) -> float:
        try:
            with serial.Serial(self.port, 9600, timeout=1) as ser:
                # Enviar comando de leitura (depende do modelo da balança)
                ser.write(b'\x05') 
                line = ser.readline().decode()
                
                # Extrair números (ex: \"  2.500 kg\")
                match = re.search(r'(\d+\.\d+)', line)
                if match:
                    return float(match.group(1))
                return 0.0
        except Exception:
            return 0.0
```

---

## Componentes Frontend (React)

### Input de Peso com Leitura Automática

```tsx
// components/PDV/WeightInput.tsx
import React, { useState } from 'react';

interface Props {
  pricePerKg: number;
  onConfirm: (weight: number) => void;
}

export const WeightInput: React.FC<Props> = ({ pricePerKg, onConfirm }) => {
  const [weight, setWeight] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);

  const readScale = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/scale/weight');
      const data = await res.json();
      setWeight(data.weight_kg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className=\"weight-input-container\">
      <h3>Venda por Peso</h3>
      <div className=\"flex gap-2\">
        <input 
          type=\"number\" 
          step=\"0.001\"
          value={weight}
          onChange={(e) => setWeight(parseFloat(e.target.value))}
          className=\"input\"
        />
        <button onClick={readScale} disabled={isLoading}>
          {isLoading ? 'Lendo...' : '⚖️ Ler Balança'}
        </button>
      </div>
      
      <div className=\"mt-4\">
        <p>Preço/kg: R$ {pricePerKg.toFixed(2)}</p>
        <p className=\"text-xl font-bold\">
          Total: R$ {(weight * pricePerKg).toFixed(2)}
        </p>
      </div>
      
      <button 
        onClick={() => onConfirm(weight)}
        className=\"btn-primary w-full mt-4\"
        disabled={weight <= 0}
      >
        Confirmar Item
      </button>
    </div>
  );
};
```

---

## Validações Importantes

### 1. Precisão Decimal
Sempre usar 3 casas decimais para peso (gramas) e 2 para preço.

```python
# schemas/sale.py
class SaleItem(BaseModel):
    product_id: UUID
    quantity: Optional[int] # Se UNIT
    weight: Optional[Decimal] # Se WEIGHT (ex: 0.250)
```

### 2. Baixa de Estoque
Tratar tipos diferentes na mesma transação.

```python
# services/inventory.py
def process_stock_exit(product, amount):
    if product.sale_type == SaleType.UNIT:
        product.quantity -= int(amount)
    else:
        product.weight_in_stock -= Decimal(amount)
```

---

## Boas Práticas

### ✅ O QUE FAZER
- [x] Permitir digitação manual caso a balança falhe
- [x] Exibir o peso em tempo real na tela do PDV
- [x] Validar se o peso solicitado existe em estoque
- [x] Usar o tipo `Numeric` ou `Decimal` para evitar erros de arredondamento de float
- [x] Emitir alerta visual quando o estoque em KG estiver baixo

### ❌ O QUE NÃO FAZER
- [ ] Usar tipo `Float` para cálculos financeiros ou de peso
- [ ] Bloquear a venda se a balança estiver desconectada (permitir manual)
- [ ] Arredondar o peso para cima sem autorização (ser preciso nas gramas)

---

## Referências
- Documentação SQLAlchemy Numeric: https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Numeric
- PySerial Guide: https://pythonhosted.org/pyserial/
- Toledo Prix 3 Protocol: https://www.toledobrasil.com/suporte/softwares-e-manuais
