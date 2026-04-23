import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Search, Plus, Minus, Trash2, ArrowLeft, CreditCard, DollarSign, QrCode, ShoppingCart, Package } from "lucide-react";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

interface Product {
  id: string;
  name: string;
  sale_price: number;
  category?: string;
  image_url?: string;
  unit?: string;
}

interface CartItem {
  id: string;
  name: string;
  price: number;
  qty: number;
}

interface POSModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialData?: {
    client_id?: string;
    items?: CartItem[];
    appointment_id?: string;
  };
}

const CATEGORIES = ["Todos", "Pacotes", "Ração", "Medicamento", "Acessório", "Higiene", "Outro"];

export const POSModal = ({ open, onOpenChange, initialData }: POSModalProps) => {
  const [search, setSearch] = useState("");
  const [cart, setCart] = useState<CartItem[]>(initialData?.items || []);
  const [payment, setPayment] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [activeCategory, setActiveCategory] = useState("Todos");
  const [cashReceived, setCashReceived] = useState<string>("");
  const [pixData, setPixData] = useState<{qr: string, code: string, id: string} | null>(null);
  const [checkingPix, setCheckingPix] = useState(false);

  const [paymentList, setPaymentList] = useState<{method: string, amount: number}[]>([]);
  const [currentPaymentMethod, setCurrentPaymentMethod] = useState("");
  const [paymentAmount, setPaymentAmount] = useState<string>("");

  useEffect(() => {
    if (open && initialData?.items) {
      setCart(initialData.items);
    }
    if (!open) {
      setCart([]);
      setPayment("");
      setPixData(null);
    }
  }, [open, initialData]);

  useEffect(() => {
    if (open) {
      const carregarProdutos = async () => {
        try {
          if (activeCategory === "Pacotes") {
            const { data } = await api.get("/pacotes/");
            // Adaptar formato de pacote para o formato de produto do PDV
            setProducts(data.map((p: any) => ({
              id: p.id,
              name: p.name,
              sale_price: p.price,
              category: "Pacotes",
              is_package: true
            })));
          } else {
            const { data } = await api.get("/products");
            setProducts(data);
          }
        } catch (err) {
          toast.error("Erro ao carregar itens.");
        }
      };
      carregarProdutos();
    }
  }, [open, activeCategory]);

  const filtered = products.filter((p) => {
    const matchesSearch = (p.name || "").toLowerCase().includes(search.toLowerCase());
    const matchesCategory = activeCategory === "Todos" || p.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  const addToCart = (product: Product) => {
    setCart((prev) => {
      const existing = prev.find((i) => i.id === product.id);
      if (existing) {
        return prev.map((i) => (i.id === product.id ? { ...i, qty: i.qty + 1 } : i));
      }
      return [...prev, { 
        id: product.id, 
        name: product.name, 
        price: Number(product.sale_price || 0), 
        qty: 1 
      }];
    });
    toast.success(`${product.name} adicionado`, { duration: 1000, position: "bottom-center" });
  };

  const updateQty = (id: string, delta: number) => {
    setCart((prev) =>
      prev
        .map((i) => (i.id === id ? { ...i, qty: i.qty + delta } : i))
        .filter((i) => i.qty > 0)
    );
  };

  const removeItem = (id: string) => setCart((prev) => prev.filter((i) => i.id !== id));

  const total = cart.reduce((sum, i) => sum + i.price * i.qty, 0);

  const [loadingSale, setLoadingSale] = useState(false);

  const handleCheckout = async () => {
    if (cart.length === 0 || (!payment && paymentList.length === 0)) return;
    setLoadingSale(true);
    
    const payload = {
      client_id: initialData?.client_id,
      items: cart.map(i => ({
        product_id: i.id.includes('-') && !(i as any).is_package ? i.id : null,
        pacote_id: (i as any).is_package ? i.id : null,
        service_id: !i.id.includes('-') ? i.id : null,
        quantity: i.qty,
        unit_price: i.price,
        total: i.price * i.qty
      })),
      discount: 0,
      payments: paymentList.length > 0 ? paymentList : [{ method: payment, amount: total }],
      payment_method: payment || (paymentList.length > 0 ? paymentList[0].method : ""),
    };
    
    try {
      const { data: venda } = await api.post("/vendas", payload);
      
      if (payment === 'pix') {
        try {
          const { data: pix } = await api.post("/payments/pix", { sale_id: venda.id });
          setPixData({ qr: pix.pix_qr_code, code: pix.pix_code, id: pix.charge_id });
          toast.success("QR Code Pix gerado!");
        } catch (err) {
          toast.error("Venda registrada, mas erro ao gerar QR Code Pix.");
          onOpenChange(false);
          setCart([]);
          setPayment("");
        }
      } else {
        toast.success("Venda finalizada com sucesso!");
        
        // Se veio de um agendamento, marca como concluído
        if (initialData?.appointment_id) {
          try {
            await api.patch(`/agendamentos/${initialData.appointment_id}`, { status: 'done' });
          } catch (e) {
            console.error("Erro ao atualizar status do agendamento");
          }
        }

        setCart([]);
        setPayment("");
        onOpenChange(false);
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erro ao registrar a venda.");
    } finally {
      setLoadingSale(false);
      if (payment !== 'pix') {
        setPaymentList([]);
      }
    }
  };

  const addPayment = () => {
    const val = Number(paymentAmount.replace(",", ".")) || 0;
    if (val <= 0 || !currentPaymentMethod) return;
    
    setPaymentList(prev => [...prev, { method: currentPaymentMethod, amount: val }]);
    setPaymentAmount("");
    setCurrentPaymentMethod("");
  };

  const removePayment = (index: number) => {
    setPaymentList(prev => prev.filter((_, i) => i !== index));
  };

  const totalPaid = paymentList.reduce((sum, p) => sum + p.amount, 0);
  const remaining = total - totalPaid;

  const checkPixStatus = async () => {
    if (!pixData) return;
    setCheckingPix(true);
    try {
      const { data } = await api.post(`/payments/pix/${pixData.id}/status`);
      if (data.status === 'CONFIRMED' || data.status === 'RECEIVED') {
        toast.success("Pagamento via Pix confirmado!");
        setPixData(null);
        setCart([]);
        setPayment("");
        onOpenChange(false);
      } else {
        toast.info("Pagamento ainda pendente.");
      }
    } catch (err) {
      toast.error("Erro ao verificar status.");
    } finally {
      setCheckingPix(false);
    }
  };

  const cashValue = Number(cashReceived.replace(",", ".")) || 0;
  const change = cashValue > 0 ? cashValue - total : 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95vw] w-[1200px] h-[90vh] p-0 overflow-hidden flex flex-col glass-card border-none shadow-2xl">
        <DialogHeader className="sr-only">
          <DialogTitle>Nova Venda</DialogTitle>
        </DialogHeader>
        <div className="flex flex-1 overflow-hidden">
          {/* Main Content: Product Picker */}
          <div className="flex-1 flex flex-col p-4 md:p-6 space-y-6 overflow-hidden bg-secondary/30">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-heading font-bold">Nova Venda</h2>
                <p className="text-xs text-muted-foreground">Registre os itens de forma rápida</p>
              </div>
              
              <div className="relative w-full max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Buscar produto..."
                    className="pl-9 bg-background shadow-sm border-none ring-1 ring-border"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
              </div>
            </div>

            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
              {CATEGORIES.map(cat => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                    activeCategory === cat 
                    ? "bg-primary text-primary-foreground shadow-md" 
                    : "bg-background text-muted-foreground hover:bg-accent"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                {filtered.map((p) => (
                  <Card 
                    key={p.id} 
                    className="glass-card flex flex-col cursor-pointer hover:ring-2 hover:ring-primary/20 transition-all group overflow-hidden"
                    onClick={() => addToCart(p)}
                  >
                    <div className="aspect-square bg-muted flex items-center justify-center relative">
                      {p.image_url ? (
                        <img src={p.image_url} alt={p.name} className="object-cover w-full h-full group-hover:scale-110 transition-transform" />
                      ) : (
                        <Package className="h-10 w-10 text-muted-foreground/30" />
                      )}
                    </div>
                    <CardContent className="p-3 bg-card">
                      <p className="font-bold text-sm line-clamp-2 leading-tight h-10">{p.name || "Sem nome"}</p>
                      <div className="mt-2 flex items-center justify-between">
                         <span className="text-primary font-bold text-base">R$ {Number(p.sale_price || 1).toFixed(2).replace(".", ",")}</span>
                         <Plus className="h-4 w-4 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar: Cart */}
          <div className="w-[400px] bg-card border-l shadow-2xl flex flex-col z-20">
            <div className="p-6 border-b flex items-center justify-between">
              <h2 className="text-lg font-bold flex items-center gap-2">
                <ShoppingCart className="h-5 w-5 text-primary" /> Carrinho
              </h2>
              <Badge variant="secondary" className="rounded-full">{cart.reduce((s,i) => s + i.qty, 0)} itens</Badge>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {cart.map((item) => (
                <div key={item.id} className="flex gap-4 p-3 rounded-xl bg-secondary/50 border border-border group">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold truncate">{item.name || "Sem nome"}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <button onClick={() => updateQty(item.id, -1)} className="h-7 w-7 rounded bg-background border border-border flex items-center justify-center hover:bg-secondary text-foreground"><Minus className="h-3 w-3" /></button>
                      <span className="text-sm font-bold">{item.qty}</span>
                      <button onClick={() => updateQty(item.id, 1)} className="h-7 w-7 rounded bg-background border border-border flex items-center justify-center hover:bg-secondary text-foreground"><Plus className="h-3 w-3" /></button>
                    </div>
                  </div>
                  <div className="flex flex-col items-end justify-between">
                    <button onClick={() => removeItem(item.id)} className="text-muted-foreground/30 hover:text-destructive transition-colors"><Trash2 className="h-4 w-4" /></button>
                    <p className="font-bold text-primary text-sm">R$ {(item.price * item.qty).toFixed(2).replace(".", ",")}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="p-6 bg-secondary/30 border-t space-y-4">
               <div className="flex justify-between items-center font-heading font-black text-2xl text-foreground">
                  <span>Total</span>
                  <span>R$ {total.toFixed(2).replace(".", ",")}</span>
               </div>

               {/* Multi-payment Section */}
               <div className="space-y-3">
                  <div className="flex gap-2">
                    <select 
                      className="flex-1 h-10 rounded-xl border bg-background px-3 text-sm"
                      value={currentPaymentMethod}
                      onChange={(e) => setCurrentPaymentMethod(e.target.value)}
                    >
                      <option value="">Método...</option>
                      <option value="pix">Pix</option>
                      <option value="dinheiro">Dinheiro</option>
                      <option value="credit_card">Cartão Crédito</option>
                      <option value="debit_card">Cartão Débito</option>
                    </select>
                    <Input 
                      className="w-24 h-10 text-right font-bold"
                      placeholder={remaining > 0 ? remaining.toFixed(2) : "0,00"}
                      value={paymentAmount}
                      onChange={(e) => setPaymentAmount(e.target.value)}
                    />
                    <Button onClick={addPayment} variant="secondary" className="h-10 w-10 p-0 rounded-xl"><Plus className="h-4 w-4"/></Button>
                  </div>

                  {paymentList.length > 0 && (
                    <div className="space-y-2 py-2">
                      {paymentList.map((p, idx) => (
                        <div key={idx} className="flex justify-between items-center text-xs bg-background/50 p-2 rounded-lg border border-border/50">
                          <span className="capitalize font-bold">{p.method.replace("_", " ")}</span>
                          <div className="flex items-center gap-3">
                            <span className="font-black text-primary">R$ {p.amount.toFixed(2)}</span>
                            <button onClick={() => removePayment(idx)} className="text-destructive"><Trash2 className="h-3 w-3"/></button>
                          </div>
                        </div>
                      ))}
                      <div className="flex justify-between pt-2 border-t border-border font-black text-sm">
                        <span className="text-muted-foreground">Pago: R$ {totalPaid.toFixed(2)}</span>
                        <span className={remaining <= 0 ? "text-emerald-500" : "text-amber-500"}>
                          {remaining > 0 ? `Falta: R$ ${remaining.toFixed(2)}` : "Quitado"}
                        </span>
                      </div>
                    </div>
                  )}
               </div>

               <Button 
                 className="w-full py-7 text-lg shadow-xl shadow-primary/20 rounded-2xl mt-2" 
                 size="lg" 
                 disabled={cart.length === 0 || (paymentList.length === 0 && !payment) || (paymentList.length > 0 && remaining > 0) || loadingSale}
                 onClick={handleCheckout}
               >
                 {loadingSale ? "Processando..." : (paymentList.some(p => p.method === 'pix') ? "Gerar Pix" : "Finalizar Venda")}
               </Button>
            </div>
          </div>
        </div>

        {/* Modal Sobreposto para PIX */}
        {pixData && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-300">
             <div className="bg-white rounded-3xl p-8 max-w-sm w-full space-y-6 text-center shadow-2xl animate-in zoom-in-95 duration-300">
               <div className="flex justify-center">
                  <div className="bg-emerald-50 p-4 rounded-full">
                    <QrCode className="h-12 w-12 text-emerald-600" />
                  </div>
               </div>
               <div>
                  <h3 className="text-xl font-bold">Pagamento via Pix</h3>
                  <p className="text-sm text-muted-foreground mt-1">Aguardando confirmação do pagamento</p>
               </div>

               <div className="aspect-square bg-slate-50 rounded-2xl flex items-center justify-center p-4 border border-slate-100">
                 {pixData.qr ? (
                   <img src={`data:image/png;base64,${pixData.qr}`} alt="QR Code" className="w-full h-full" />
                 ) : (
                   <div className="text-xs text-muted-foreground">QR Code Indisponível</div>
                 )}
               </div>

               <div className="space-y-4">
                  <Button 
                    variant="outline" 
                    className="w-full text-xs font-mono h-auto py-3 bg-slate-50 border-dashed"
                    onClick={() => {
                       navigator.clipboard.writeText(pixData.code);
                       toast.success("Código copiado!");
                    }}
                  >
                    Clique aqui para copiar o código
                  </Button>
                  
                  <div className="flex gap-2">
                    <Button 
                      variant="ghost" 
                      className="flex-1"
                      onClick={() => setPixData(null)}
                      disabled={checkingPix}
                    >
                      Voltar
                    </Button>
                    <Button 
                      className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                      onClick={checkPixStatus}
                      disabled={checkingPix}
                    >
                      {checkingPix ? "Verificando..." : "Já paguei"}
                    </Button>
                  </div>
               </div>
             </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
