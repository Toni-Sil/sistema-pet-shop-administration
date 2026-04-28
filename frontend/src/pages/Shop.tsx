import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Package, TrendingUp, Plus, CircleDollarSign, Boxes, AlertTriangle, Search, ChevronDown, ArrowDown, ArrowUp, Pencil, PlusCircle, Trash2, ImageIcon, Sparkles, Upload } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface Product {
  id: string;
  name: string;
  category: string;
  qty: number;
  quantity: number;
  weight_in_stock?: number;
  sale_type?: string;
  min_weight?: number;
  sale_price: number;
  cost_price: number;
  image_url?: string;
}

const LOW_STOCK_THRESHOLD = 5;

const BRL = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

const getQty = (product: Product) => {
  if (product.sale_type === 'WEIGHT') return Number(product.weight_in_stock || 0);
  return Number(product.quantity ?? product.qty ?? 0);
};

const isLowStock = (product: Product) => {
  if (product.sale_type === 'WEIGHT') {
    return getQty(product) < (product.min_weight || 0.5);
  }
  return getQty(product) < LOW_STOCK_THRESHOLD;
};

const getStockDisplay = (product: Product) => {
  if (product.sale_type === 'WEIGHT') {
    return `${getQty(product).toFixed(3)} kg`;
  }
  return `${getQty(product)} un.`;
};

const Shop = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"critical" | "name">("critical");
  const [predictions, setPredictions] = useState<any[]>([]);

  // Form State
  const [name, setName] = useState("");
  const [category, setCategory] = useState("Outro");
  const [costPrice, setCostPrice] = useState("");
  const [salePrice, setSalePrice] = useState("");
  const [quantity, setQuantity] = useState("0");
  const [imageUrl, setImageUrl] = useState("");

  // Edit/Adjustment State
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isMovementModalOpen, setIsMovementModalOpen] = useState(false);
  const [movementQty, setMovementQty] = useState("");
  const [movementType, setMovementType] = useState<"entry" | "exit">("entry");
  const [movementReason, setMovementReason] = useState("Ajuste manual");

  const loadProducts = async () => {
    setLoading(true);
    try {
      const response = await api.get("/produtos");
      setProducts(response.data);
    } catch (error) {
      toast.error("Erro ao puxar dados do estoque.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
    const loadPredictions = async () => {
      try {
        const { data } = await api.get("/ai/inventory-predictions");
        setPredictions(data);
      } catch { /* silently */ }
    };
    loadPredictions();
  }, []);

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/produtos", {
        name,
        category,
        cost_price: parseFloat(costPrice),
        sale_price: parseFloat(salePrice),
        quantity: parseInt(quantity) || 0,
        image_url: imageUrl,
        min_qty: 5,
        unit: "un"
      });
      toast.success("Produto cadastrado com sucesso!");
      setIsModalOpen(false);
      setName(""); setCostPrice(""); setSalePrice(""); setQuantity("0"); setImageUrl("");
      loadProducts();
    } catch (error) {
      toast.error("Erro ao salvar produto.");
    } finally {
      setLoading(false);
    }
  };

  const handleImportCSV = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      setLoading(true);
      await api.post('/produtos/import/csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success("Produtos importados com sucesso!");
      loadProducts();
    } catch (error) {
      console.error(error);
      toast.error("Erro ao importar CSV.");
    } finally {
      setLoading(false);
      // Limpa o input para permitir selecionar o mesmo arquivo novamente se necessário
      e.target.value = '';
    }
  };

  const handleUpdateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;
    setLoading(true);
    try {
      await api.patch(`/produtos/${editingProduct.id}`, {
        name,
        category,
        cost_price: parseFloat(costPrice),
        sale_price: parseFloat(salePrice),
        image_url: imageUrl,
        unit: "un"
      });
      toast.success("Produto atualizado!");
      setIsEditModalOpen(false);
      setImageUrl("");
      loadProducts();
    } catch (error) {
      toast.error("Erro ao atualizar produto.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProduct = async (id: string) => {
    if (!confirm("Deseja realmente excluir este produto?")) return;
    try {
      await api.delete(`/produtos/${id}`);
      toast.success("Produto removido.");
      loadProducts();
    } catch {
      toast.error("Erro ao remover produto.");
    }
  };

  const handleRegisterMovement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;
    setLoading(true);
    try {
      const payload: any = {
        product_id: editingProduct.id,
        type: movementType,
        reason: movementReason
      };
      
      if (editingProduct.sale_type === 'WEIGHT') {
        payload.weight = parseFloat(movementQty);
      } else {
        payload.quantity = parseInt(movementQty);
      }

      await api.post("/estoque/movimentacoes", payload);
      toast.success("Movimentação registrada!");
      setIsMovementModalOpen(false);
      setMovementQty("");
      loadProducts();
    } catch (error) {
      toast.error("Erro ao registrar movimentação.");
    } finally {
      setLoading(false);
    }
  };

  const openEdit = (p: Product) => {
    setEditingProduct(p);
    setName(p.name);
    setCategory(p.category || "Outro");
    setCostPrice(String(p.cost_price));
    setSalePrice(String(p.sale_price));
    setImageUrl(p.image_url || "");
    setIsEditModalOpen(true);
  };

  const openMovement = (p: Product) => {
    setEditingProduct(p);
    setMovementQty("");
    setIsMovementModalOpen(true);
  };

  const categories = useMemo(() => {
    const set = new Set<string>(["all"]);
    products.forEach((p) => {
      if (p.category) set.add(p.category);
    });
    return Array.from(set).sort();
  }, [products]);

  const filteredProducts = useMemo(() => {
    let result = [...products];
    const term = search.trim().toLowerCase();
    if (term) {
      result = result.filter((product) => {
        const name = (product.name || "").toLowerCase();
        const category = (product.category || "").toLowerCase();
        return name.includes(term) || category.includes(term);
      });
    }
    if (categoryFilter && categoryFilter !== "all") {
      result = result.filter((p) => (p.category || "Geral") === categoryFilter);
    }
    if (sortBy === "critical") {
      result.sort((a, b) => getQty(a) - getQty(b));
    } else if (sortBy === "name") {
      result.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
    }
    return result;
  }, [products, search, categoryFilter, sortBy]);

  const totals = useMemo(() => {
    const itemsInStock = products.reduce((sum, product) => sum + getQty(product), 0);
    const inventoryValue = products.reduce((sum, product) => sum + (getQty(product) * Number(product.cost_price || 0)), 0);
    const expectedRevenue = products.reduce((sum, product) => sum + (getQty(product) * Number(product.sale_price || 0)), 0);
    const lowStock = products.filter((product) => isLowStock(product));

    return {
      productsCount: products.length,
      itemsInStock,
      inventoryValue,
      expectedRevenue,
      lowStock,
    };
  }, [products]);

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      <Card className="border-none shadow-lg bg-gradient-to-r from-emerald-500/10 via-cyan-500/10 to-sky-500/10">
        <CardContent className="pt-6 pb-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide font-semibold text-emerald-600">Operação</p>
              <h1 className="text-3xl font-heading font-bold text-foreground">Estoque</h1>
              <p className="text-muted-foreground mt-1">Controle inteligente de produtos, margem e itens críticos.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline"><Plus className="h-4 w-4 mr-2" /> Cadastrar produto</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle>Novo produto</DialogTitle></DialogHeader>
                  <form onSubmit={handleCreateProduct} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Nome</Label>
                      <Input required value={name} onChange={e => setName(e.target.value)} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Custo (R$)</Label>
                        <Input type="number" step="0.01" required value={costPrice} onChange={e => setCostPrice(e.target.value)} />
                      </div>
                      <div className="space-y-2">
                        <Label>Venda (R$)</Label>
                        <Input type="number" step="0.01" required value={salePrice} onChange={e => setSalePrice(e.target.value)} />
                      </div>
                    </div>
                    <Button type="submit" className="w-full">Salvar</Button>
                  </form>
                </DialogContent>
              </Dialog>
              
              <div className="relative">
                <input
                  type="file"
                  id="csv-upload"
                  className="hidden"
                  accept=".csv"
                  onChange={handleImportCSV}
                />
                <Button variant="outline" onClick={() => document.getElementById('csv-upload')?.click()}>
                  <Upload className="h-4 w-4 mr-2" /> Importar CSV
                </Button>
              </div>
              <Button onClick={() => navigate("/caixa")}>Nova venda</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StockKPI title="Produtos" value={String(totals.productsCount)} icon={Package} tone="blue" />
        <StockKPI title="Estoque Total" value={String(totals.itemsInStock)} icon={Boxes} tone="indigo" />
        <StockKPI title="Valor em Custo" value={BRL.format(totals.inventoryValue)} icon={CircleDollarSign} tone="emerald" />
        <StockKPI title="Críticos" value={String(totals.lowStock.length)} icon={AlertTriangle} tone="amber" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card className="xl:col-span-2 shadow-lg">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Catálogo</CardTitle>
              <div className="flex gap-2">
                <Input placeholder="Buscar..." value={search} onChange={e => setSearch(e.target.value)} className="w-48" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
             <div className="space-y-2 max-h-[500px] overflow-auto pr-1">
                {filteredProducts.map((p) => (
                  <div key={p.id} className="p-4 border rounded-xl flex items-center justify-between hover:bg-muted/30 transition-all">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                        <Package className="h-5 w-5 text-muted-foreground/50" />
                      </div>
                      <div>
                        <p className="font-bold text-sm">{p.name}</p>
                        <p className="text-xs text-muted-foreground">{p.category} • Venda {BRL.format(p.sale_price)}</p>
                      </div>
                    </div>
                    <div className="text-right">
                       <p className={`font-black ${isLowStock(p) ? 'text-rose-500' : 'text-emerald-500'}`}>{getStockDisplay(p)}</p>
                       <div className="flex gap-1 mt-1">
                         <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(p)}><Pencil className="h-3 w-3" /></Button>
                         <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openMovement(p)}><PlusCircle className="h-3 w-3" /></Button>
                       </div>
                    </div>
                  </div>
                ))}
             </div>
          </CardContent>
        </Card>

        <Card className="shadow-lg border-amber-500/20 bg-amber-500/5">
          <CardHeader><CardTitle className="text-amber-600 text-sm flex items-center gap-2"><AlertTriangle className="h-4 w-4" /> Alerta de Reposição</CardTitle></CardHeader>
          <CardContent>
            {totals.lowStock.length === 0 ? <p className="text-xs text-muted-foreground italic">Nenhum item abaixo do mínimo.</p> : totals.lowStock.map(p => (
              <div key={p.id} className="flex justify-between py-2 border-b border-amber-500/10 text-xs">
                <span>{p.name}</span>
                <span className="font-bold text-amber-600">{getStockDisplay(p)}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* AI Shopping Intelligence Card */}
        <Card className="shadow-xl border-primary/20 bg-primary/5 ring-1 ring-primary/20 animate-in fade-in slide-in-from-bottom-4">
          <CardHeader>
            <CardTitle className="text-primary text-sm flex items-center gap-2">
              <Sparkles className="h-4 w-4 animate-pulse" /> Inteligência de Compras (IA)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {predictions.length === 0 ? (
              <p className="text-[10px] text-muted-foreground italic">A IA está analisando sua velocidade de vendas para gerar previsões...</p>
            ) : (
              predictions.slice(0, 4).map(p => (
                <div key={p.id} className="space-y-1.5 p-3 rounded-xl bg-white/40 border border-primary/10">
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-black truncate max-w-[140px]">{p.nome}</span>
                    <Badge variant="secondary" className="text-[9px] bg-primary/10 text-primary border-none">
                      {p.dias_restantes} dias rest.
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground font-bold">
                    <TrendingUp className="h-3 w-3 text-emerald-500" />
                    Venda: {p.venda_diaria_media}/dia
                  </div>
                  <div className="pt-1">
                    <Button variant="ghost" className="h-7 w-full text-[9px] font-black uppercase tracking-tighter bg-primary text-white hover:bg-primary/90">
                      Sugerido: Comprar {p.sugestao_compra} un.
                    </Button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Modals */}
      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Editar Produto</DialogTitle></DialogHeader>
          <form onSubmit={handleUpdateProduct} className="space-y-4 pt-4">
            <Input value={name} onChange={e => setName(e.target.value)} placeholder="Nome" />
            <div className="grid grid-cols-2 gap-4">
              <Input type="number" value={costPrice} onChange={e => setCostPrice(e.target.value)} placeholder="Custo" />
              <Input type="number" value={salePrice} onChange={e => setSalePrice(e.target.value)} placeholder="Venda" />
            </div>
            <Button type="submit" className="w-full">Atualizar</Button>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={isMovementModalOpen} onOpenChange={setIsMovementModalOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Ajustar Estoque: {editingProduct?.name}</DialogTitle></DialogHeader>
          <form onSubmit={handleRegisterMovement} className="space-y-4 pt-4">
            <div className="grid grid-cols-2 gap-4">
              <select value={movementType} onChange={e => setMovementType(e.target.value as any)} className="h-10 border rounded-md px-2 bg-background">
                <option value="entry">Entrada (+)</option>
                <option value="exit">Saída (-)</option>
              </select>
              <Input 
                type="number" 
                step={editingProduct?.sale_type === 'WEIGHT' ? '0.001' : '1'} 
                value={movementQty} 
                onChange={e => setMovementQty(e.target.value)} 
                placeholder={editingProduct?.sale_type === 'WEIGHT' ? "Quilos (kg)" : "Qtd"} 
              />
            </div>
            <Input value={movementReason} onChange={e => setMovementReason(e.target.value)} placeholder="Motivo" />
            <Button type="submit" className="w-full">Confirmar</Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const StockKPI = ({ title, value, icon: Icon, tone }: any) => {
  const toneMap: Record<string, string> = {
    blue: "bg-blue-500/10 text-blue-500",
    indigo: "bg-indigo-500/10 text-indigo-500",
    emerald: "bg-emerald-500/10 text-emerald-500",
    amber: "bg-amber-500/10 text-amber-500",
  };
  return (
    <Card className="border-none shadow-sm overflow-hidden">
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <div className={`h-12 w-12 rounded-2xl flex items-center justify-center ${toneMap[tone]}`}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground font-medium">{title}</p>
            <p className="text-xl font-bold">{value}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default Shop;
