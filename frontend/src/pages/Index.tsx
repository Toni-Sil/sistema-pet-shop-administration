import { useEffect, useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Calendar,
  ShoppingCart,
  Package,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Users,
  CreditCard,
  Target,
  Clock,
  ChevronRight,
  Plus
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

interface DashboardData {
  salesCount: number;
  salesToday: number;
  totalClients: number;
  agendamentosHoje: number;
  agendamentosPendentes: number;
  produtosEmFalta: { id: string; name: string; quantity: number }[];
  lastSales: any[];
  receitaMes: number;
  ticketMedio: number;
}

const Index = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const [vendasRes, agendRes, produtosRes, clientesRes, financeRes] = await Promise.all([
          api.get("/vendas?limit=10"),
          api.get("/agendamentos?limit=100"),
          api.get("/produtos?limit=100"),
          api.get("/clientes?limit=1"),
          api.get("/reports/financial")
        ]);

        const vendas = vendasRes?.data || [];
        const hoje = new Date().toISOString().split("T")[0];
        const fin = financeRes?.data || {};

        const agendamentos = agendRes?.data || [];
        const agendHoje = agendamentos.filter((a: any) => a.date === hoje);
        const agendPend = agendamentos.filter((a: any) => a.status === 'scheduled');

        const produtos = produtosRes.data || [];
        const emFalta = produtos.filter((p: any) => (p.quantity ?? 0) < (p.min_qty ?? 0));

        setData({
          salesCount: fin.vendasHoje || 0,
          salesToday: fin.receitaHoje || 0,
          totalClients: fin.totalClientes || 0,
          agendamentosHoje: agendHoje.length,
          agendamentosPendentes: agendPend.length,
          produtosEmFalta: emFalta.slice(0, 5),
          lastSales: vendas.slice(0, 5),
          receitaMes: fin.receitaMes || 0,
          ticketMedio: fin.ticketMedio || 0
        });
      } catch (err) {
        console.error("Dashboard error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in pb-10">
      {/* Header com Boas Vindas */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            Olá, administrador!
          </h1>
          <p className="text-muted-foreground mt-1">
            Aqui está o que está acontecendo no seu Pet Shop hoje.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => navigate("/servicos/novo-agendamento")}>
            <Calendar className="h-4 w-4 mr-2" /> Novo Agendamento
          </Button>
          <Button size="sm" onClick={() => navigate("/caixa")}>
            <ShoppingCart className="h-4 w-4 mr-2" /> Abrir Caixa
          </Button>
        </div>
      </div>

      {/* Grid Principal de KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          id="kpi-faturamento"
          title="Faturamento Hoje"
          value={loading ? "..." : `R$ ${(data?.salesToday || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`}
          sub="Vendas concluídas hoje"
          icon={CreditCard}
          color="text-emerald-500"
          bgColor="bg-emerald-500/20"
        />
        <KPICard
          id="kpi-agendamentos"
          title="Agendamentos"
          value={loading ? "..." : (data?.agendamentosHoje || 0)}
          sub={`${data?.agendamentosPendentes || 0} agendados no sistema`}
          icon={Clock}
          color="text-primary"
          bgColor="bg-primary/10"
        />
        <KPICard
          id="kpi-vendas"
          title="Vendas"
          value={loading ? "..." : (data?.salesCount || 0)}
          sub={`Média de R$ ${(data?.ticketMedio || 0).toFixed(2)}/venda`}
          icon={TrendingUp}
          color="text-blue-500"
          bgColor="bg-blue-500/20"
        />
        <KPICard
          id="kpi-clientes"
          title="Total Clientes"
          value={loading ? "..." : (data?.totalClients || 0)}
          sub="Clientes cadastrados"
          icon={Users}
          color="text-violet-500"
          bgColor="bg-violet-500/20"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ultimas Atividades */}
        <Card className="lg:col-span-2 glass-card border-none shadow-xl">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Visão Geral de Vendas</CardTitle>
              <CardDescription>Vendas e serviços realizados recentemente.</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={() => navigate("/relatorios")}>
              Relatório Completo
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {loading ? (
                [1, 2, 3].map(i => <Skeleton key={i} className="h-16 w-full" />)
              ) : data?.lastSales.length === 0 ? (
                <div className="text-center py-10 text-muted-foreground border-2 border-dashed rounded-xl">
                  Nenhuma venda registrada ainda.
                </div>
              ) : (
                data?.lastSales.map((sale: any) => (
                  <div key={sale.id} className="flex items-center justify-between p-4 rounded-xl bg-muted/20 hover:bg-muted/40 transition-colors group cursor-pointer">
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-full bg-background flex items-center justify-center shadow-sm">
                        <ShoppingCart className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">Venda #{sale.id.slice(0, 6).toUpperCase()}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(sale.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} •
                          {sale.payment_method === 'pix' ? ' Pix' : ' Dinheiro'}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-primary">R$ {Number(sale.total).toFixed(2).replace('.', ',')}</p>
                      <Badge variant="outline" className="text-[10px] uppercase">Concluída</Badge>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Alertas e Insights */}
        <div className="space-y-6">
          <Card id="alert-estoque" className="glass-card bg-amber-500/10 border-amber-500/20 overflow-hidden relative">
            <div className="absolute top-0 right-0 p-4 opacity-5">
              <Package className="h-20 w-20 rotate-12" />
            </div>
            <CardHeader>
              <CardTitle className="text-amber-500 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" /> Alerta de Estoque
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {data?.produtosEmFalta.map(p => (
                  <div key={p.id} className="flex justify-between items-center text-sm p-2 rounded-lg bg-background/40">
                    <span className="font-medium text-amber-500 truncate max-w-[140px]">{p.name}</span>
                    <Badge variant="destructive" className="bg-amber-600">{p.quantity} un</Badge>
                  </div>
                ))}
                {data?.produtosEmFalta.length === 0 && <p className="text-sm text-amber-500">Tudo em ordem no estoque! ✅</p>}
                <Button variant="link" className="w-full text-amber-500 font-bold" onClick={() => navigate("/estoque")}>
                  Solicitar Reposição <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-primary to-primary/80 text-white shadow-xl border-none">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Target className="h-5 w-5" /> Faturamento Mensal
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2 text-white/90">
                <div className="flex justify-between text-sm font-bold">
                  <span>Total arrecadado no mês</span>
                  <span>100%</span>
                </div>
                <p className="text-3xl font-black tracking-tighter">
                  R$ {(data?.receitaMes || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </p>
                <div className="h-2 bg-white/20 rounded-full overflow-hidden">
                  <div className="h-full bg-white rounded-full w-full" />
                </div>
              </div>
              <p className="text-xs text-white/70">Continue com o ótimo trabalho! Acompanhe o crescimento em tempo real.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

const KPICard = ({ id, title, value, sub, icon: Icon, color, bgColor }: any) => (
  <Card id={id} className="glass-card shadow-lg hover-lift border-none">
    <CardContent className="pt-6">
      <div className="flex items-center justify-between">
        <div className={`p-3 rounded-2xl ${bgColor}`}>
          <Icon className={`h-6 w-6 ${color}`} />
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <h3 className="text-2xl font-bold font-heading">{value}</h3>
          <p className="text-[10px] text-emerald-600 font-bold">{sub}</p>
        </div>
      </div>
    </CardContent>
  </Card>
);

export default Index;
