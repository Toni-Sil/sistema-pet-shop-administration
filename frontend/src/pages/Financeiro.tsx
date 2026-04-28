import { useEffect, useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  DollarSign, 
  Plus, 
  CheckCircle, 
  Trash2, 
  TrendingUp, 
  TrendingDown, 
  Calendar,
  Filter,
  ArrowUpRight,
  ArrowDownRight,
  Wallet,
  FileText
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";

interface Despesa {
  id: string;
  description: string;
  amount: number;
  category: string;
  due_date: string;
  is_paid: boolean;
}

interface FinancialSummary {
  receitaMes: number;
  despesasMes: number;
  lucroMes: number;
  receitaHoje: number;
  vendasHoje: number;
}

const CATEGORIES = ["Aluguel", "Fornecedor", "Salário", "Serviços", "Marketing", "Outros"];

const Financeiro = () => {
  const [despesas, setDespesas] = useState<Despesa[]>([]);
  const [summary, setSummary] = useState<FinancialSummary>({
    receitaMes: 0,
    despesasMes: 0,
    lucroMes: 0,
    receitaHoje: 0,
    vendasHoje: 0
  });
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State
  const [desc, setDesc] = useState("");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("Outros");
  const [dueDate, setDueDate] = useState(new Date().toISOString().split("T")[0]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [despRes, summaryRes] = await Promise.all([
        api.get("/despesas?limit=100"),
        api.get("/reports/financial"),
      ]);
      setDespesas(despRes.data || []);
      setSummary(summaryRes.data || { receitaMes: 0, despesasMes: 0, lucroMes: 0, receitaHoje: 0, vendasHoje: 0 });
    } catch (error) {
      console.error(error);
      toast.error("Erro ao carregar dados financeiros.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post("/despesas", {
        description: desc,
        amount: parseFloat(amount),
        category,
        due_date: dueDate
      });
      toast.success("Despesa cadastrada!");
      setIsModalOpen(false);
      setDesc(""); setAmount(""); setCategory("Outros");
      loadData();
    } catch {
      toast.error("Erro ao salvar despesa.");
    }
  };

  const handlePay = async (id: string) => {
    try {
      await api.post(`/despesas/${id}/pagar`);
      toast.success("Pagamento registrado!");
      loadData();
    } catch {
      toast.error("Erro ao processar pagamento.");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Deseja remover esta despesa?")) return;
    try {
      await api.delete(`/despesas/${id}`);
      toast.success("Despesa removida.");
      loadData();
    } catch {
      toast.error("Erro ao remover.");
    }
  };

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImportCSV = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const tId = toast.loading("Importando despesas...");
    try {
      const { data } = await api.post("/despesas/import/csv", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      toast.success(data.message, { id: tId });
      loadData();
    } catch (err) {
      toast.error("Erro ao importar arquivo.", { id: tId });
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const totalPendente = despesas
    .filter(d => !d.is_paid)
    .reduce((s, d) => s + Number(d.amount), 0);

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold">Gestão Financeira</h1>
          <p className="text-muted-foreground mt-1">Acompanhe seu fluxo de caixa, receitas e despesas.</p>
        </div>
        
        <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
          <DialogTrigger asChild>
            <Button className="shadow-lg shadow-primary/20">
              <Plus className="h-4 w-4 mr-2" /> Nova Despesa
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Cadastrar Despesa</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Descrição / Fornecedor</Label>
                <Input required value={desc} onChange={e => setDesc(e.target.value)} placeholder="Ex: Aluguel da loja" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Valor (R$)</Label>
                  <Input type="number" step="0.01" required value={amount} onChange={e => setAmount(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Vencimento</Label>
                  <Input type="date" required value={dueDate} onChange={e => setDueDate(e.target.value)} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Categoria</Label>
                <select 
                  className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20" 
                  value={category} 
                  onChange={e => setCategory(e.target.value)}
                >
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <Button type="submit" className="w-full py-6">Confirmar Lançamento</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-emerald-500/5 border-emerald-500/10">
          <CardContent className="pt-6">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-emerald-600/70">Receita (Mês)</p>
                <h3 className="text-2xl font-black mt-1">R$ {(summary.receitaMes || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</h3>
              </div>
              <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-600">
                <TrendingUp className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-destructive/5 border-destructive/10">
          <CardContent className="pt-6">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-destructive/70">Despesas (Mês)</p>
                <h3 className="text-2xl font-black mt-1">R$ {(summary.despesasMes || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</h3>
              </div>
              <div className="p-2 bg-destructive/10 rounded-lg text-destructive">
                <TrendingDown className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={`${summary.lucroMes >= 0 ? 'bg-primary/5 border-primary/10' : 'bg-amber-500/5 border-amber-500/10'}`}>
          <CardContent className="pt-6">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Lucro Líquido (Mês)</p>
                <h3 className="text-2xl font-black mt-1">R$ {(summary.lucroMes || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</h3>
              </div>
              <div className={`p-2 rounded-lg ${summary.lucroMes >= 0 ? 'bg-primary/10 text-primary' : 'bg-amber-500/10 text-amber-500'}`}>
                <Wallet className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lista de Despesas */}
        <Card className="lg:col-span-2 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <div>
              <CardTitle className="text-lg">Despesas Recentes</CardTitle>
              <CardDescription>Gerencie suas contas a pagar e pagas.</CardDescription>
            </div>
            <div className="flex items-center gap-2">
               <input
                 type="file"
                 ref={fileInputRef}
                 onChange={handleImportCSV}
                 accept=".csv"
                 className="hidden"
               />
               <Button 
                 variant="outline" 
                 size="sm" 
                 className="rounded-lg border-dashed h-8"
                 onClick={() => fileInputRef.current?.click()}
               >
                 <FileText className="h-3 w-3 mr-2" /> Importar CSV
               </Button>
               <Badge variant="outline" className="text-destructive border-destructive/20 bg-destructive/5 px-3 py-1">
                 R$ {totalPendente.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} Pendente
               </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[1,2,3,4].map(i => <Skeleton key={i} className="h-16 w-full rounded-xl" />)}
              </div>
            ) : despesas.length === 0 ? (
              <div className="text-center py-20 border-2 border-dashed rounded-2xl opacity-40">
                <DollarSign className="h-10 w-10 mx-auto mb-2" />
                <p>Nenhuma despesa registrada.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {despesas.map((d) => (
                  <div key={d.id} className={`group flex items-center justify-between p-4 rounded-xl border transition-all ${d.is_paid ? 'bg-muted/30 border-transparent' : 'bg-card border-border hover:border-primary/30'}`}>
                    <div className="flex items-center gap-4 min-w-0">
                      <div className={`h-10 w-10 rounded-full flex items-center justify-center shrink-0 ${d.is_paid ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'}`}>
                        {d.is_paid ? <CheckCircle className="h-5 w-5" /> : <Calendar className="h-5 w-5" />}
                      </div>
                      <div className="min-w-0">
                        <p className={`font-bold text-sm truncate ${d.is_paid ? 'text-muted-foreground line-through' : 'text-foreground'}`}>{d.description}</p>
                        <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-tight">{d.category} · Vence em {new Date(d.due_date).toLocaleDateString('pt-BR')}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className={`font-black text-sm ${d.is_paid ? 'text-muted-foreground' : 'text-foreground'}`}>R$ {Number(d.amount).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                        <Badge className={`text-[9px] h-4 ${d.is_paid ? 'bg-emerald-500/20 text-emerald-600 hover:bg-emerald-500/20' : 'bg-amber-500/20 text-amber-600 hover:bg-amber-500/20'} border-none`}>
                          {d.is_paid ? 'PAGO' : 'PENDENTE'}
                        </Badge>
                      </div>
                      
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {!d.is_paid && (
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-emerald-500" onClick={() => handlePay(d.id)} title="Marcar como Paga">
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                        )}
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => handleDelete(d.id)} title="Excluir">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sidebar Financeira */}
        <div className="space-y-6">
           <Card className="bg-primary/5 border-primary/10 overflow-hidden relative">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                 <ArrowUpRight className="h-20 w-20" />
              </div>
              <CardHeader>
                <CardTitle className="text-base">Análise Mensal</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                 <div className="space-y-1">
                    <p className="text-xs text-muted-foreground font-medium">Margem Operacional</p>
                    <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                       <div className="h-full bg-primary" style={{ width: '65%' }}></div>
                    </div>
                    <p className="text-[10px] text-right text-primary font-bold">65% Estimado</p>
                 </div>
                 <p className="text-xs text-muted-foreground leading-relaxed">
                   Seus custos fixos representam cerca de 35% do faturamento bruto este mês. 
                 </p>
              </CardContent>
           </Card>

           <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Filter className="h-4 w-4" /> Categorias
                </CardTitle>
              </CardHeader>
              <CardContent>
                 <div className="space-y-2">
                    {CATEGORIES.map(cat => (
                      <div key={cat} className="flex justify-between items-center text-xs">
                        <span className="text-muted-foreground">{cat}</span>
                        <span className="font-bold">R$ {despesas.filter(d => d.category === cat).reduce((s,d) => s + Number(d.amount), 0).toFixed(0)}</span>
                      </div>
                    ))}
                 </div>
              </CardContent>
           </Card>
        </div>
      </div>
    </div>
  );
};

export default Financeiro;
