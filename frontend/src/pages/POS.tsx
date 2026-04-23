import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Wallet, Unlock, Lock, History, ArrowUpRight, ArrowDownLeft, FileText, ShoppingCart, Plus } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { Badge } from "@/components/ui/badge";
import { POSModal } from "@/components/POSModal";

interface CashierSession {
  id: string;
  opening_balance: number;
  closing_balance?: number;
  total_sales: number;
  opened_at: string;
  closed_at?: string;
  notes?: string;
  user_id: string;
}

interface SaleItem {
  id: string;
  product_id: string;
  quantity: number;
  weight: number;
  unit_price: number;
  total: number;
}

interface Sale {
  id: string;
  total: number;
  payment_method: string;
  created_at: string;
  payment_status: string;
  items: SaleItem[];
}

interface Product {
  id: string;
  name: string;
}

const POS = () => {
  const [session, setSession] = useState<CashierSession | null>(null);
  const [history, setHistory] = useState<CashierSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [amount, setAmount] = useState("");
  const [notes, setNotes] = useState("");
  const [currentSales, setCurrentSales] = useState<Sale[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isClosing, setIsClosing] = useState(false);
  const [isPOSOpen, setIsPOSOpen] = useState(false);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const res = await api.get("/caixa/status");
      setSession(res.data);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setSession(null);
      } else {
        toast.error("Erro ao carregar status do caixa");
      }
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const res = await api.get("/caixa/historico");
      setHistory(res.data || []);
    } catch {
      toast.error("Erro ao carregar histórico");
    }
  };

  const loadProducts = async () => {
    try {
      const res = await api.get("/produtos");
      setProducts(res.data || []);
    } catch {
      console.error("Erro ao carregar produtos");
    }
  };

  const loadCurrentSales = async (sessionId: string) => {
    try {
      const res = await api.get(`/vendas?cashier_id=${sessionId}&limit=100`);
      setCurrentSales(res.data || []);
    } catch {
      console.error("Erro ao carregar vendas da sessão");
    }
  };

  useEffect(() => {
    loadStatus();
    loadHistory();
    loadProducts();
  }, []);

  useEffect(() => {
    if (session?.id) {
      loadCurrentSales(session.id);
    } else {
      setCurrentSales([]);
    }
  }, [session?.id]);

  const handleOpen = async () => {
    if (!amount) return toast.warning("Informe o saldo inicial");
    try {
      await api.post("/caixa/abrir", { 
        opening_balance: parseFloat(amount.replace(",", ".")),
        notes 
      });
      toast.success("Caixa aberto com sucesso!");
      setAmount("");
      setNotes("");
      loadStatus();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erro ao abrir caixa");
    }
  };

  const handleClose = async () => {
    const expected = (Number(session?.opening_balance) || 0) + (Number(session?.total_sales) || 0);
    const finalBalance = amount ? parseFloat(amount.replace(",", ".")) : expected;
    
    try {
      await api.post("/caixa/fechar", { 
        closing_balance: finalBalance,
        notes: notes || "Fechamento automático"
      });
      toast.success("Caixa fechado com sucesso!");
      setAmount("");
      setNotes("");
      setIsClosing(false);
      loadStatus();
      loadHistory();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erro ao fechar caixa");
    }
  };

  const getProductSummary = () => {
    const summary: Record<string, { name: string, qty: number, weight: number, total: number }> = {};
    currentSales.forEach(sale => {
      sale.items.forEach(item => {
        const prod = products.find(p => p.id === item.product_id);
        const name = prod?.name || "Produto Desconhecido";
        if (!summary[item.product_id]) {
          summary[item.product_id] = { name, qty: 0, weight: 0, total: 0 };
        }
        summary[item.product_id].qty += item.quantity || 0;
        summary[item.product_id].weight += Number(item.weight || 0);
        summary[item.product_id].total += Number(item.total);
      });
    });
    return Object.values(summary);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-heading font-bold">Registro de Caixa</h1>
          <p className="text-muted-foreground mt-1">Gerencie aberturas, fechamentos e saldo do dia.</p>
        </div>
        <div className="flex items-center gap-3">
          {session && (
            <Button 
              onClick={() => setIsPOSOpen(true)}
              className="bg-emerald-600 hover:bg-emerald-700 shadow-lg shadow-emerald-500/20"
            >
              <Plus className="h-4 w-4 mr-2" />
              Nova Venda
            </Button>
          )}
          {session ? (
             <Badge variant="outline" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20 py-1 px-3 flex items-center gap-2">
               <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
               Caixa Aberto
             </Badge>
          ) : (
             <Badge variant="outline" className="bg-muted text-muted-foreground border-border py-1 px-3 flex items-center gap-2">
               <Lock className="h-3 w-3" />
               Caixa Fechado
             </Badge>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controle Lateral */}
        <div className="space-y-6">
           <Card className="glass-card">
              <CardHeader>
                 <CardTitle className="text-base flex items-center gap-2">
                    {session ? <Lock className="h-5 w-5 text-destructive" /> : <Unlock className="h-5 w-5 text-primary" />}
                    {session ? "Fechar Caixa" : "Abrir Novo Caixa"}
                 </CardTitle>
                 <CardDescription>
                    {session ? "Conclua o turno e registre o saldo final." : "Inicie o dia informando o saldo inicial."}
                 </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                  {!session ? (
                    <>
                      <div className="space-y-2">
                         <Label>Saldo Inicial / Fundo (R$)</Label>
                         <div className="relative">
                            <Wallet className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input 
                              placeholder="0,00" 
                              className="pl-9" 
                              value={amount}
                              onChange={(e) => setAmount(e.target.value)}
                              type="number"
                              step="0.01"
                            />
                         </div>
                      </div>
                      <div className="space-y-2">
                         <Label>Observações (Opcional)</Label>
                         <Input 
                           placeholder="Ex: Troco inicial em moedas..." 
                           value={notes}
                           onChange={(e) => setNotes(e.target.value)}
                         />
                      </div>
                      <Button className="w-full" onClick={handleOpen}>
                         Abrir Caixa
                      </Button>
                    </>
                  ) : (
                    <div className="space-y-4">
                      <div className="p-4 bg-muted/30 rounded-xl border border-border space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Saldo Inicial:</span>
                          <span className="font-bold text-foreground">R$ {Number(session.opening_balance).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Total de Vendas:</span>
                          <span className="font-bold text-emerald-500">+ R$ {Number(session.total_sales).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                        </div>
                        <div className="pt-2 border-t flex justify-between items-center">
                          <span className="font-black text-xs uppercase tracking-wider text-muted-foreground">Saldo Esperado:</span>
                          <span className="font-black text-xl text-primary">R$ {(Number(session.opening_balance) + Number(session.total_sales)).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <p className="text-xs font-bold uppercase text-muted-foreground flex items-center gap-1">
                          <FileText className="h-3 w-3" /> Resumo de Produtos Vendidos
                        </p>
                        <div className="max-h-[200px] overflow-y-auto space-y-1 custom-scrollbar">
                          {getProductSummary().map((item, idx) => (
                            <div key={idx} className="flex justify-between items-center text-[11px] p-2 bg-background rounded-lg border border-border/50">
                              <span className="truncate flex-1 font-medium">{item.name}</span>
                              <div className="flex items-center gap-2">
                                <span className="text-muted-foreground">x{item.qty || item.weight.toFixed(2) + 'kg'}</span>
                                <span className="font-bold text-primary">R$ {item.total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                              </div>
                            </div>
                          ))}
                          {getProductSummary().length === 0 && (
                            <p className="text-[11px] text-center text-muted-foreground py-2 italic">Nenhum produto vendido.</p>
                          )}
                        </div>
                      </div>

                      <div className="space-y-2">
                         <Label>Saldo Final em Dinheiro (R$)</Label>
                         <div className="relative">
                            <Wallet className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input 
                              placeholder={Number(session.opening_balance + session.total_sales).toFixed(2)} 
                              className="pl-9" 
                              value={amount}
                              onChange={(e) => setAmount(e.target.value)}
                              type="number"
                              step="0.01"
                            />
                         </div>
                         <p className="text-[10px] text-muted-foreground italic">Se vazio, usará o saldo esperado de R$ {(Number(session.opening_balance) + Number(session.total_sales)).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                      </div>

                      <Button 
                        className="w-full" 
                        variant="destructive"
                        onClick={handleClose}
                      >
                         Confirmar e Fechar Caixa
                      </Button>
                    </div>
                  )}
               </CardContent>
           </Card>

           {session && (
              <Card className="bg-primary/5 border-primary/10">
                 <CardContent className="p-4 space-y-4">
                    <div className="flex justify-between items-center">
                       <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Vendas do Turno</span>
                       <Badge className="bg-primary/20 text-primary border-none">Hoje</Badge>
                    </div>
                    <div className="text-3xl font-heading font-black text-primary">
                       R$ {Number(session.total_sales || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </div>
                    <p className="text-[10px] text-muted-foreground flex items-center gap-1">
                       <ArrowUpRight className="h-3 w-3 text-emerald-500" />
                       Resultado das vendas desde a abertura
                    </p>
                 </CardContent>
              </Card>
           )}
        </div>

        {/* Histórico Principal */}
        <div className="lg:col-span-2 space-y-6">
             {session && (
               <Card className="glass-card">
                  <CardHeader>
                     <CardTitle className="text-base flex items-center gap-2">
                        <ShoppingCart className="h-5 w-5 text-primary" /> Vendas da Sessão Atual
                     </CardTitle>
                     <CardDescription>Produtos e serviços vendidos neste turno.</CardDescription>
                  </CardHeader>
                  <CardContent>
                     {currentSales.length === 0 ? (
                        <p className="text-center py-10 text-sm text-muted-foreground border-2 border-dashed rounded-xl">Nenhuma venda realizada nesta sessão.</p>
                     ) : (
                        <div className="space-y-3">
                           {currentSales.map(sale => (
                              <div key={sale.id} className="flex justify-between items-center p-3 bg-secondary/50 rounded-lg border border-border">
                                 <div>
                                    <div className="flex items-center gap-2">
                                       <span className="text-xs font-bold uppercase text-muted-foreground">{sale.payment_method}</span>
                                       {sale.payment_status === 'pending' && <Badge variant="outline" className="text-[9px] h-4 bg-amber-500/10 text-amber-500 border-amber-500/20">Pendente</Badge>}
                                    </div>
                                    <p className="text-[10px] text-muted-foreground">{format(new Date(sale.created_at), "HH:mm")}</p>
                                 </div>
                                 <div className="text-right">
                                    <p className="font-bold text-sm">R$ {Number(sale.total).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                                    <p className="text-[9px] text-muted-foreground">ID: {sale.id.slice(0,8)}</p>
                                 </div>
                              </div>
                           ))}
                        </div>
                     )}
                  </CardContent>
               </Card>
             )}

             <Card className="glass-card h-full">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-base flex items-center gap-2">
                       <History className="h-5 w-5 text-muted-foreground" /> Histórico de Sessões
                    </CardTitle>
                    <CardDescription>Visualização dos últimos turnos de caixa.</CardDescription>
                  </div>
               </CardHeader>
               <CardContent>
                  <div className="space-y-4">
                     {history.length === 0 ? (
                        <div className="py-20 text-center space-y-3 opacity-30">
                           <FileText className="h-12 w-12 mx-auto" />
                           <p className="text-sm">Nenhuma sessão de caixa registrada.</p>
                        </div>
                     ) : (
                        <div className="border rounded-xl overflow-hidden divide-y bg-background/50">
                           {history.map((h) => (
                              <div key={h.id} className="p-4 flex items-center justify-between hover:bg-accent/50 transition-colors">
                                 <div className="flex items-center gap-4">
                                    <div className={`p-2 rounded-full ${h.closed_at ? "bg-muted text-muted-foreground" : "bg-emerald-500/20 text-emerald-500"}`}>
                                       {h.closed_at ? <Lock className="h-4 w-4" /> : <Unlock className="h-4 w-4" />}
                                    </div>
                                    <div>
                                       <div className="flex items-center gap-2">
                                          <span className="font-bold text-sm">
                                             {format(new Date(h.opened_at), "dd 'de' MMMM", { locale: ptBR })}
                                          </span>
                                          {h.closed_at && <Badge variant="secondary" className="text-[10px] leading-none h-4">Fechado</Badge>}
                                       </div>
                                       <p className="text-[10px] text-muted-foreground">
                                          Aberto às {format(new Date(h.opened_at), "HH:mm")} 
                                          {h.closed_at && ` • Fechado às ${format(new Date(h.closed_at), "HH:mm")}`}
                                       </p>
                                    </div>
                                 </div>
                                 <div className="text-right">
                                    <div className="font-bold text-sm text-foreground">
                                       R$ {Number(h.total_sales || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                    </div>
                                    <div className="text-[10px] flex items-center justify-end gap-1 text-muted-foreground">
                                       <span className="text-emerald-500 font-medium">Ini: {Number(h.opening_balance).toFixed(0)}</span>
                                       {h.closing_balance && <span> • Fim: {Number(h.closing_balance).toFixed(0)}</span>}
                                    </div>
                                 </div>
                              </div>
                           ))}
                        </div>
                     )}
                  </div>
               </CardContent>
            </Card>
        </div>
      </div>
      <POSModal 
        open={isPOSOpen} 
        onOpenChange={(open) => {
          setIsPOSOpen(open);
          if (!open) {
            loadStatus();
            if (session?.id) loadCurrentSales(session.id);
          }
        }} 
      />
    </div>
  );
};

export default POS;
