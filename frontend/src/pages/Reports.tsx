import { useEffect, useState, useMemo, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  Download, 
  TrendingUp, 
  DollarSign, 
  Scissors, 
  ArrowUp, 
  ArrowDown, 
  Filter, 
  PieChart, 
  BarChart3, 
  RefreshCcw,
  Package,
  CreditCard,
  Target
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Progress } from "@/components/ui/progress";

interface DRE {
  receita_bruta: number;
  despesas: number;
  lucro_liquido: number;
  margem_percent: number;
}

interface FinancialSummary {
  receitaHoje: number;
  receitaSemana: number;
  receitaMes: number;
  despesasMes: number;
  lucroMes: number;
  vendasHoje: number;
  ticketMedio: number;
  totalClientes: number;
}

interface ProductReport {
  categoria: string;
  total: number;
  quantidade: number;
}

interface PaymentMethodReport {
  method: string;
  total: number;
  count: number;
}

interface ServiceSummary {
  service: string;
  count: number;
  revenue: number;
}

const Reports = () => {
  const [activeReport, setActiveReport] = useState<"gestao" | "vendas" | "servicos">("gestao");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Data states
  const [dre, setDre] = useState<DRE | null>(null);
  const [financial, setFinancial] = useState<FinancialSummary | null>(null);
  const [products, setProducts] = useState<ProductReport[]>([]);
  const [payments, setPayments] = useState<PaymentMethodReport[]>([]);
  const [services, setServices] = useState<ServiceSummary[]>([]);

  const loadData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);

    try {
      const [dreRes, finRes, prodRes, payRes, servRes] = await Promise.all([
        api.get("/reports/dre"),
        api.get("/reports/financial"),
        api.get("/reports/sales-by-product"),
        api.get("/reports/sales-by-payment-method"),
        api.get("/reports/appointments-summary"),
      ]);

      setDre(dreRes.data);
      setFinancial(finRes.data);
      setProducts(prodRes.data);
      setPayments(payRes.data);
      setServices(servRes.data);
    } catch (err) {
      console.error(err);
      toast.error("Erro ao atualizar métricas.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Polling for "constant updates"
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      loadData(true);
    }, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, [autoRefresh, loadData]);

  const maxProductTotal = useMemo(() => Math.max(...products.map(p => p.total), 1), [products]);
  const maxServiceCount = useMemo(() => Math.max(...services.map(s => s.count), 1), [services]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCcw className="h-10 w-10 text-primary animate-spin" />
        <p className="text-muted-foreground animate-pulse">Compilando inteligência financeira...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in pb-20">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-heading font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/60">
              Centro de Inteligência
            </h1>
            {autoRefresh && (
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            )}
          </div>
          <p className="text-muted-foreground mt-1">Visão analítica e métricas em tempo real para sua gestão.</p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? "border-emerald-500/50 text-emerald-500 bg-emerald-500/10" : ""}
          >
            <RefreshCcw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            {autoRefresh ? "Live: Ativado" : "Ativar Live Logs"}
          </Button>
          <Button size="sm" onClick={() => loadData(true)} disabled={refreshing}>
            Atualizar Agora
          </Button>
        </div>
      </div>

      {/* Main Navigation Tabs */}
      <div className="flex p-1 bg-muted/50 rounded-xl w-fit">
        {[
          { id: "gestao", label: "Gestão DRE", icon: Target },
          { id: "vendas", label: "Vendas & Produtos", icon: DollarSign },
          { id: "servicos", label: "Desempenho de Serviços", icon: Scissors },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveReport(tab.id as any)}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeReport === tab.id
                ? "bg-background text-primary shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content Areas */}
      {activeReport === "gestao" && financial && dre && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="border-none shadow-md bg-gradient-to-br from-primary/5 to-transparent">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between text-primary">
                  <p className="text-xs font-medium uppercase tracking-wider">Receita Hoje</p>
                  <TrendingUp className="h-4 w-4 opacity-50" />
                </div>
                <p className="text-2xl font-bold mt-2">
                  R$ {(financial.receitaHoje || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </p>
                <p className="text-[10px] text-muted-foreground mt-1">Atualizado há poucos instantes</p>
              </CardContent>
            </Card>
            
            <Card className="border-none shadow-md bg-gradient-to-br from-emerald-500/10 to-transparent">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between text-emerald-500">
                  <p className="text-xs font-medium uppercase tracking-wider">Lucro do Mês</p>
                  <DollarSign className="h-4 w-4 opacity-50" />
                </div>
                <p className="text-2xl font-bold mt-2 text-emerald-500">
                  R$ {(financial.lucroMes || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-500 font-medium">
                    {dre.margem_percent}% margem
                  </span>
                </div>
              </CardContent>
            </Card>
 
            <Card className="border-none shadow-md bg-gradient-to-br from-rose-500/10 to-transparent">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between text-rose-500">
                  <p className="text-xs font-medium uppercase tracking-wider">Despesas (Mês)</p>
                  <ArrowDown className="h-4 w-4 opacity-50" />
                </div>
                <p className="text-2xl font-bold mt-2 text-rose-500">
                  R$ {(financial.despesasMes || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </p>
                <p className="text-[10px] text-muted-foreground mt-1">Custos operacionais</p>
              </CardContent>
            </Card>
 
            <Card className="border-none shadow-md bg-gradient-to-br from-amber-500/10 to-transparent">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between text-amber-500">
                  <p className="text-xs font-medium uppercase tracking-wider">Ticket Médio</p>
                  <BarChart3 className="h-4 w-4 opacity-50" />
                </div>
                <p className="text-2xl font-bold mt-2 text-amber-500">
                  R$ {(financial.ticketMedio || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </p>
                <p className="text-[10px] text-muted-foreground mt-1">Baseado em vendas recentes</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border-none shadow-lg">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Target className="h-5 w-5 text-primary" /> Demonstração de Resultados (DRE)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex justify-between items-end">
                    <div className="space-y-1">
                      <p className="text-sm text-muted-foreground">Receita Bruta Acumulada</p>
                      <p className="text-2xl font-bold">R$ {dre.receita_bruta.toLocaleString("pt-BR")}</p>
                    </div>
                  </div>
                  <Progress value={100} className="h-2" />
                </div>

                <div className="space-y-4">
                  <div className="flex justify-between items-end text-rose-500">
                    <div className="space-y-1">
                      <p className="text-sm font-medium">Despesas Operacionais</p>
                      <p className="text-2xl font-bold">R$ {dre.despesas.toLocaleString("pt-BR")}</p>
                    </div>
                    <div className="text-right font-medium">
                      {((dre.despesas / (dre.receita_bruta || 1)) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <Progress value={(dre.despesas / (dre.receita_bruta || 1)) * 100} className="h-2" />
                </div>

                <div className="pt-6 border-t flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Lucro Líquido</p>
                    <p className="text-3xl font-heading font-black text-emerald-500">
                      R$ {dre.lucro_liquido.toLocaleString("pt-BR")}
                    </p>
                  </div>
                  <div className="h-16 w-16 rounded-full border-4 border-emerald-500/50 flex items-center justify-center text-xs font-bold text-emerald-500 shadow-inner">
                    {dre.margem_percent}%
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-none shadow-lg text-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" /> Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-8">
                  <div className="flex items-start gap-4 p-4 rounded-xl bg-muted/30">
                    <Package className="h-6 w-6 text-primary" />
                    <div>
                      <p className="font-bold">Comercial</p>
                      <p className="text-xs text-muted-foreground">{financial.vendasHoje} vendas hoje.</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4 p-4 rounded-xl bg-muted/30">
                    <Target className="h-6 w-6 text-emerald-600" />
                    <div>
                      <p className="font-bold">Clientes</p>
                      <p className="text-xs text-muted-foreground">{financial.totalClientes} ativos.</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {activeReport === "vendas" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border-none shadow-lg">
            <CardHeader><CardTitle>Produtos por Categoria</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-6">
                {products.map((p) => (
                  <div key={p.categoria} className="space-y-1.5">
                    <div className="flex justify-between text-sm">
                      <p className="font-semibold">{p.categoria}</p>
                      <p className="font-bold">R$ {p.total.toLocaleString("pt-BR")}</p>
                    </div>
                    <Progress value={(p.total / maxProductTotal) * 100} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeReport === "servicos" && (
        <div className="max-w-2xl mx-auto">
          <Card className="border-none shadow-lg">
            <CardHeader><CardTitle>Serviços Executados</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-8">
                {services.map((s) => (
                  <div key={s.service} className="space-y-3">
                    <div className="flex justify-between items-center text-sm font-bold">
                      <span>{s.service}</span>
                      <span>{s.count} agendamentos</span>
                    </div>
                    <Progress value={(s.count / maxServiceCount) * 100} className="h-2" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Reports;
