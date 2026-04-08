# Skill: Frontend Next.js

## Objetivo
Desenvolver o frontend do sistema pet shop com Next.js 14 (App Router), TypeScript, Tailwind CSS e shadcn/ui, integrado com o backend FastAPI.

## Stack Frontend
- **Next.js 14** - App Router, Server Components
- **TypeScript** - tipagem estatica
- **Tailwind CSS** - estilizacao utilitaria
- **shadcn/ui** - componentes acessiveis e customizaveis
- **Axios** - cliente HTTP com interceptors
- **React Hook Form + Zod** - formularios com validacao
- **Recharts** - graficos financeiros
- **TanStack Query** - cache e estado do servidor (opcional)

## Regras Fundamentais

1. **Autenticacao via token no localStorage** - access token apenas
2. **Axios interceptor para auth** - adicionar token em todas as requests
3. **Redirect automatico** para `/login` se 401
4. **Tipagem forte** - nunca usar `any`
5. **Componentes pequenos** - max 150 linhas por componente

## Configuracao do Axios

```typescript
// lib/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Adicionar token em toda request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirecionar para login se 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

## Tipos TypeScript

```typescript
// types/index.ts
export interface Produto {
  id: string
  nome: string
  descricao?: string
  preco: number
  categoria_id: string
  codigo_barras?: string
  estoque_atual: number
  estoque_minimo: number
  is_active: boolean
  store_id: string
  created_at: string
}

export interface ProdutoCreate {
  nome: string
  preco: number
  categoria_id: string
  descricao?: string
  codigo_barras?: string
  estoque_atual?: number
  estoque_minimo?: number
}

export interface MovimentacaoEstoque {
  id: string
  produto_id: string
  tipo: 'entrada' | 'saida' | 'ajuste'
  quantidade: number
  motivo?: string
  custo_unitario?: number
  store_id: string
  created_at: string
}

export interface Transacao {
  id: string
  tipo: 'receita' | 'despesa'
  valor: number
  descricao: string
  categoria: string
  status: 'pendente' | 'pago' | 'cancelado'
  store_id: string
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface Usuario {
  id: string
  nome: string
  email: string
  role: 'admin' | 'gerente' | 'funcionario'
  is_active: boolean
  store_id: string
}
```

## Hook de Auth

```typescript
// hooks/useAuth.ts
'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { Usuario } from '@/types'

export function useAuth() {
  const [user, setUser] = useState<Usuario | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setLoading(false)
      router.push('/login')
      return
    }
    // Decodificar token para pegar dados do usuario
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      setUser({
        id: payload.sub,
        nome: payload.nome,
        email: '',
        role: payload.role,
        is_active: true,
        store_id: payload.store_id
      })
    } catch {
      localStorage.removeItem('access_token')
      router.push('/login')
    }
    setLoading(false)
  }, [])

  const logout = () => {
    localStorage.removeItem('access_token')
    router.push('/login')
  }

  return { user, loading, logout }
}
```

## Pagina de Login

```typescript
// app/(auth)/login/page.tsx
'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import api from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const loginSchema = z.object({
  email: z.string().email('Email invalido'),
  senha: z.string().min(6, 'Senha deve ter no minimo 6 caracteres'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function LoginPage() {
  const [error, setError] = useState('')
  const router = useRouter()

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    try {
      const response = await api.post('/auth/login', data)
      localStorage.setItem('access_token', response.data.access_token)
      router.push('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao fazer login')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Pet Shop - Acesso</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" {...register('email')} />
              {errors.email && <p className="text-red-500 text-sm">{errors.email.message}</p>}
            </div>
            <div>
              <Label htmlFor="senha">Senha</Label>
              <Input id="senha" type="password" {...register('senha')} />
              {errors.senha && <p className="text-red-500 text-sm">{errors.senha.message}</p>}
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? 'Entrando...' : 'Entrar'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
```

## Componente de Tabela de Produtos

```typescript
// components/produtos/ProdutoTable.tsx
'use client'
import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { Produto } from '@/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatCurrency } from '@/lib/formatters'

export function ProdutoTable() {
  const [produtos, setProdutos] = useState<Produto[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/produtos').then((res) => {
      setProdutos(res.data.items)
      setLoading(false)
    })
  }, [])

  if (loading) return <p>Carregando...</p>

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left p-3">Nome</th>
            <th className="text-left p-3">Preco</th>
            <th className="text-left p-3">Estoque</th>
            <th className="text-left p-3">Status</th>
            <th className="text-left p-3">Acoes</th>
          </tr>
        </thead>
        <tbody>
          {produtos.map((produto) => (
            <tr key={produto.id} className="border-b hover:bg-gray-50">
              <td className="p-3">{produto.nome}</td>
              <td className="p-3">{formatCurrency(produto.preco)}</td>
              <td className="p-3">
                <span className={produto.estoque_atual <= produto.estoque_minimo ? 'text-red-600 font-bold' : ''}>
                  {produto.estoque_atual}
                </span>
                {produto.estoque_atual <= produto.estoque_minimo && (
                  <Badge variant="destructive" className="ml-2">Baixo</Badge>
                )}
              </td>
              <td className="p-3">
                <Badge variant={produto.is_active ? 'default' : 'secondary'}>
                  {produto.is_active ? 'Ativo' : 'Inativo'}
                </Badge>
              </td>
              <td className="p-3 space-x-2">
                <Button variant="outline" size="sm">Editar</Button>
                <Button variant="outline" size="sm">Estoque</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

## Formatadores

```typescript
// lib/formatters.ts
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

export function formatDate(date: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(new Date(date))
}

export function formatDateTime(date: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date))
}
```

## package.json (dependencias principais)

```json
{
  "dependencies": {
    "next": "14.x",
    "react": "18.x",
    "react-dom": "18.x",
    "typescript": "5.x",
    "tailwindcss": "3.x",
    "axios": "1.x",
    "react-hook-form": "7.x",
    "@hookform/resolvers": "3.x",
    "zod": "3.x",
    "recharts": "2.x",
    "lucide-react": "0.x",
    "@radix-ui/react-dialog": "1.x",
    "class-variance-authority": "0.x",
    "clsx": "2.x",
    "tailwind-merge": "2.x"
  }
}
```

## Boas Praticas

1. **'use client' apenas quando necessario** - preferir Server Components
2. **Loading states** - sempre mostrar feedback de carregamento
3. **Error handling** - tratar erros de API e mostrar mensagens claras
4. **Componentes reutilizaveis** - DataTable, ConfirmDialog, PageTitle
5. **Validacao client-side com Zod** - antes de enviar para API
