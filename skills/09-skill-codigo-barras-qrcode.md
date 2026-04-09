# Skill: Leitura de Código de Barras e QR Code

## Objetivo
Implementar funcionalidade de leitura e busca de produtos por código de barras (1D) e QR Code (2D) no sistema pet shop, integrando com scanners USB, Bluetooth e câmera.

## Como Funciona a Tecnologia

### Código de Barras (1D)
- **Estrutura:** Barras pretas e brancas de larguras variadas
- **Funcionamento:** Leitor emite luz (laser/LED) → barras pretas absorvem, brancas refletem → padrão convertido em binário (0 e 1) → decodificado em números
- **Capacidade:** Apenas números (EAN-13: 13 dígitos, Code 128: até ~48 caracteres)
- **Uso:** Identificar produto no banco de dados pelo ID numérico

### QR Code (2D)
- **Estrutura:** Grade bidimensional de pixels pretos e brancos
- **Funcionamento:** Câmera captura imagem → decodifica padrão horizontal e vertical → retorna string
- **Capacidade:** Até ~4.000 caracteres alfanuméricos (100x mais que código de barras)
- **Uso:** Pode armazenar diretamente dados estruturados (JSON), URLs, texto completo

## Como o Sistema "Enxerga" os Códigos

**Do ponto de vista do software, ambos funcionam igual:**

```
Scanner/Câmera lê o código
        ↓
Decodifica e retorna STRING de texto
        ↓
Sistema recebe essa string no campo de input
        ↓
Busca no banco de dados usando essa string
        ↓
Retorna o produto encontrado
```

**Importante:** O scanner USB funciona como um **teclado virtual** — ele digita o código automaticamente no campo focado e pressiona Enter.

## Tipos de Leitores

| Tipo | Como integra com o sistema | Complexidade |
|---|---|---|
| **Scanner USB (pistola)** | Funciona como teclado — digita e pressiona Enter | Muito fácil |
| **Scanner Bluetooth** | Igual ao USB, só que sem fio | Muito fácil |
| **Câmera/Webcam** | Precisa biblioteca Python (`pyzbar`) ou JS | Média |
| **Câmera celular** | Frontend detecta via JS (`html5-qrcode`) | Média |

## Implementação Backend (FastAPI)

### Endpoint de Busca por Código

```python
# app/routers/produtos.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_any_role, get_current_store_id
from app.models.produto import Produto
from app.schemas.produto import ProdutoResponse
import uuid

router = APIRouter(prefix='/produtos', tags=['Produtos'])

@router.get('/codigo/{codigo}', response_model=ProdutoResponse)
async def buscar_produto_por_codigo(
    codigo: str,  # aceita tanto barras quanto QR Code
    db: Session = Depends(get_db),
    current_user = Depends(get_any_role),
    store_id: uuid.UUID = Depends(get_current_store_id)
):
    """Busca produto pelo código de barras ou QR Code."""
    produto = db.query(Produto).filter(
        Produto.codigo_barras == codigo,
        Produto.store_id == store_id,
        Produto.is_active == True
    ).first()
    
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Produto com código {codigo} não encontrado'
        )
    
    return produto
```

### Model com suporte a código

O campo `codigo_barras` no modelo `Produto` já suporta ambos os tipos:

```python
# app/models/produto.py
from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Produto(Base):
    __tablename__ = 'produtos'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(255), nullable=False)
    codigo_barras = Column(String(100), index=True)  # EAN, Code128, QR Code
    preco = Column(Float, nullable=False)
    estoque_atual = Column(Integer, default=0)
    estoque_minimo = Column(Integer, default=5)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'))
```

**Índice importante:** `codigo_barras` tem índice para busca rápida.

## Implementação Frontend (Next.js)

### Input com Scanner USB (mais simples)

```typescript
// components/estoque/ScannerInput.tsx
'use client'
import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import api from '@/lib/api'
import { Produto } from '@/types'

interface ScannerInputProps {
  onProdutoEncontrado: (produto: Produto) => void
  onErro: (mensagem: string) => void
}

export function ScannerInput({ onProdutoEncontrado, onErro }: ScannerInputProps) {
  const [codigo, setCodigo] = useState('')
  const [loading, setLoading] = useState(false)

  const buscarProduto = async (codigoLido: string) => {
    if (!codigoLido.trim()) return
    
    setLoading(true)
    try {
      const response = await api.get(`/produtos/codigo/${codigoLido}`)
      onProdutoEncontrado(response.data)
      setCodigo('') // Limpar para próximo scan
    } catch (err: any) {
      onErro(err.response?.data?.detail || 'Produto não encontrado')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Label htmlFor="scanner-input">Escaneie o código de barras</Label>
      <Input
        id="scanner-input"
        placeholder="Posicione o cursor aqui e escaneie..."
        value={codigo}
        onChange={(e) => setCodigo(e.target.value)}
        onKeyDown={(e) => {
          // Scanner USB pressiona Enter automaticamente
          if (e.key === 'Enter') {
            e.preventDefault()
            buscarProduto(codigo)
          }
        }}
        disabled={loading}
        autoFocus // Importante: manter foco para scanner
      />
      {loading && <p className="text-sm text-gray-500 mt-1">Buscando...</p>}
    </div>
  )
}
```

### Uso no Fluxo de Movimentação de Estoque

```typescript
// app/(dashboard)/estoque/movimentacao/page.tsx
'use client'
import { useState } from 'react'
import { ScannerInput } from '@/components/estoque/ScannerInput'
import { Button } from '@/components/ui/button'
import { Produto } from '@/types'
import api from '@/lib/api'

export default function MovimentacaoPage() {
  const [produtoSelecionado, setProdutoSelecionado] = useState<Produto | null>(null)
  const [quantidade, setQuantidade] = useState(1)

  const registrarEntrada = async () => {
    if (!produtoSelecionado) return
    
    await api.post('/estoque/movimentacao', {
      produto_id: produtoSelecionado.id,
      tipo: 'entrada',
      quantidade,
      motivo: 'Reposição via scanner'
    })
    
    alert('Entrada registrada com sucesso!')
    setProdutoSelecionado(null)
    setQuantidade(1)
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Movimentação de Estoque</h1>
      
      <ScannerInput
        onProdutoEncontrado={(produto) => setProdutoSelecionado(produto)}
        onErro={(msg) => alert(msg)}
      />
      
      {produtoSelecionado && (
        <div className="mt-6 p-4 border rounded">
          <h3 className="font-bold">{produtoSelecionado.nome}</h3>
          <p>Estoque atual: {produtoSelecionado.estoque_atual}</p>
          <p>Código: {produtoSelecionado.codigo_barras}</p>
          
          <div className="mt-4">
            <label>Quantidade de entrada:</label>
            <input
              type="number"
              value={quantidade}
              onChange={(e) => setQuantidade(Number(e.target.value))}
              className="border p-2 ml-2"
            />
          </div>
          
          <Button onClick={registrarEntrada} className="mt-4">
            Confirmar Entrada
          </Button>
        </div>
      )}
    </div>
  )
}
```

## Leitura via Câmera (Opcional - Futuro)

### Backend com `pyzbar` (Python)

```python
# requirements.txt adicionar:
pyzbar==0.1.9
opencv-python==4.x
Pillow==10.x

# app/services/scanner_service.py
from pyzbar import pyzbar
import cv2
from PIL import Image
import numpy as np

def ler_codigo_da_imagem(imagem_bytes: bytes) -> str:
    """Lê código de barras ou QR Code de uma imagem."""
    # Converter bytes para array numpy
    nparr = np.frombuffer(imagem_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Decodificar códigos na imagem
    codigos = pyzbar.decode(img)
    
    if not codigos:
        raise ValueError('Nenhum código detectado na imagem')
    
    return codigos[0].data.decode('utf-8')
```

### Frontend com `html5-qrcode` (JavaScript)

```typescript
// components/estoque/CameraScanner.tsx
'use client'
import { useEffect, useRef } from 'react'
import { Html5Qrcode } from 'html5-qrcode'

interface CameraScannerProps {
  onScanSuccess: (codigo: string) => void
}

export function CameraScanner({ onScanSuccess }: CameraScannerProps) {
  const scannerRef = useRef<Html5Qrcode | null>(null)

  useEffect(() => {
    const scanner = new Html5Qrcode('qr-reader')
    scannerRef.current = scanner

    scanner.start(
      { facingMode: 'environment' }, // Câmera traseira no celular
      { fps: 10, qrbox: 250 },
      (decodedText) => {
        onScanSuccess(decodedText)
        scanner.stop()
      },
      (errorMessage) => {
        // Ignora erros de leitura contínua
      }
    )

    return () => {
      scanner.stop().catch(() => {})
    }
  }, [])

  return <div id="qr-reader" style={{ width: '100%' }} />
}
```

## Fluxo Completo de Uso

1. **Cadastro de Produto:** Funcionário digita ou escaneia o código de barras do fabricante e cadastra o produto
2. **Entrada de Estoque:** Escaneia código → sistema busca produto → confirma quantidade → registra movimentação
3. **Venda no PDV:** Escaneia código → adiciona ao carrinho → repete até finalizar venda
4. **Inventário:** Escaneia produtos em estoque → compara com banco de dados → gera relatório de divergências

## Boas Práticas

1. **Input sempre em foco:** Use `autoFocus` e reconheça o foco após cada scan
2. **Feedback visual:** Mostrar loading/sucesso/erro imediatamente
3. **Limpar campo:** Após scan bem-sucedido, limpar o input para próxima leitura
4. **Validar formato:** Códigos EAN têm 13 dígitos, validar antes de buscar
5. **Índice no banco:** Campo `codigo_barras` deve ter índice para busca rápida
6. **Beep de confirmação:** Opcional — emitir som quando produto for encontrado

## Hardware Recomendado

- **Scanner USB básico:** R$ 80-150 (ex: Honeywell 1900, Datalogic QD2430)
- **Scanner Bluetooth:** R$ 200-400 (mobilidade para inventário)
- **Celular com câmera:** Grátis (usar navegador para ler QR Code)

## Limitações

- Scanner USB só funciona em desktop/notebook (não mobile)
- Câmera precisa boa iluminação para ler códigos
- QR Code danificado pode não ser lido
- Código de barras amassado/riscado pode falhar na leitura
