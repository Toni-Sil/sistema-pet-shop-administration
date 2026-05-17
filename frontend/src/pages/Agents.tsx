import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";
import {
  Bot,
  Sparkles,
  Cpu,
  ShieldCheck,
  Check,
  X,
  Activity,
  FileText,
  Database,
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  MessageSquare,
  Clock,
  Settings,
  ShieldAlert,
  ArrowRight,
  UserCheck
} from "lucide-react";
import { toast } from "sonner";

interface AgentStatus {
  agent_id: string;
  state: string;
  execution_mode: string;
  current_execution: any;
  recent_executions: number;
}

interface DashboardData {
  summary: {
    active_conversations: number;
    waiting_approval: number;
    health: string;
    by_agent: Record<string, number>;
    by_intent: Record<string, number>;
  };
  agents: Array<{
    agent: string;
    state: string;
    recent_executions: number;
    last_execution: string | null;
  }>;
}

interface EventBusItem {
  id: string;
  event_type: string;
  source_agent: string | null;
  target_agent: string | null;
  payload: any;
  metadata: any;
  timestamp: string;
}

interface ConversationItem {
  id: string;
  client_phone: string;
  intent: string | null;
  current_agent: string | null;
  step: string;
  requires_approval: boolean;
}

interface SuggestionItem {
  type: string;
  title: string;
  count: number;
}

const AGENT_METADATA: Record<string, { name: string; desc: string; icon: any; color: string; tools: string[] }> = {
  supervisor: {
    name: "Supervisor Geral",
    desc: "Coordenador cognitivo de fluxo de atendimento. Analisa intenções e direciona para agentes especialistas.",
    icon: ShieldCheck,
    color: "from-blue-600 to-indigo-600 shadow-indigo-500/20",
    tools: ["Roteamento Cognitivo", "Escalação Humana", "Gestão de Fila", "Validação de Respostas"]
  },
  atendimento: {
    name: "Agente de Atendimento",
    desc: "Especialista em responder dúvidas gerais de clientes, recepção e esclarecimento de pacotes e produtos.",
    icon: MessageSquare,
    color: "from-emerald-500 to-teal-600 shadow-emerald-500/20",
    tools: ["Análise de Sentimento", "FAQ Inteligente", "Informações de Serviços", "Apoio ao Cliente"]
  },
  agendamento: {
    name: "Agente de Agendamento",
    desc: "Gerencia a agenda do Pet Shop, reservas, horários disponíveis de banho, tosa e hotel.",
    icon: Clock,
    color: "from-violet-500 to-purple-600 shadow-purple-500/20",
    tools: ["Verificar Disponibilidade", "Confirmar Horário", "Bloqueios na Agenda", "Remarcações automáticas"]
  },
  financeiro: {
    name: "Agente Financeiro",
    desc: "Valida faturas, cria contas a pagar/receber, processa links de pagamento e calcula comissão.",
    icon: Database,
    color: "from-amber-500 to-orange-600 shadow-amber-500/20",
    tools: ["Gerar Links de Pix", "Checar Faturamento", "Conciliação Bancária", "Emissão de Notas Fiscais"]
  },
  estoque: {
    name: "Agente de Estoque",
    desc: "Controla entrada/saída de insumos, prevê demandas de rações/higiene e gera sugestões de compra.",
    icon: Cpu,
    color: "from-pink-500 to-rose-600 shadow-rose-500/20",
    tools: ["Previsão de Demanda", "Alertas de Ruptura", "Solicitação de Compra", "Análise de Lote"]
  },
  crm: {
    name: "Agente CRM & Campanhas",
    desc: "Engaja clientes inativos, envia mensagens de aniversário e campanhas de vacinas atrasadas.",
    icon: Sparkles,
    color: "from-cyan-500 to-blue-500 shadow-cyan-500/20",
    tools: ["Mensagens Customizadas", "Campanhas de Vacina", "Fidelidade de Tutores", "Nutrição de Contatos"]
  },
  compras: {
    name: "Agente de Compras",
    desc: "Automatiza cotações com fornecedores cadastrados e envia ordens de compras pré-aprovadas.",
    icon: Settings,
    color: "from-red-500 to-orange-500 shadow-red-500/20",
    tools: ["Cotação de Insumos", "Ordem de Compra", "Validação de NF", "Negociação Autônoma"]
  },
  marketing: {
    name: "Agente de Marketing",
    desc: "Analisa tendências de vendas locais para criar cupons dinâmicos e posts em redes sociais.",
    icon: Activity,
    color: "from-fuchsia-500 to-pink-500 shadow-fuchsia-500/20",
    tools: ["Geração de Cupons", "Posts Recomendados", "Insights de Promoção", "Análise de Concorrentes"]
  }
};

export default function Agents() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [agentsStatus, setAgentsStatus] = useState<Record<string, AgentStatus>>({});
  const [events, setEvents] = useState<EventBusItem[]>([]);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);

    try {
      const [dashRes, statusRes, eventsRes, convsRes, suggsRes] = await Promise.all([
        api.get("/ai/operations/dashboard"),
        api.get("/ai/operations/agents/status"),
        api.get("/ai/operations/events/recent"),
        api.get("/ai/operations/conversations"),
        api.get("/ai/operations/suggestions")
      ]);

      setDashboard(dashRes.data);
      setAgentsStatus(statusRes.data.sub_agents || statusRes.data);
      setEvents(eventsRes.data.events || []);
      setConversations(convsRes.data.conversations || []);
      setSuggestions(suggsRes.data.suggestions || []);
    } catch (error) {
      console.error("Erro ao buscar dados do painel de agentes:", error);
      toast.error("Não foi possível sincronizar o Cockpit de IA.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-update a cada 10 segundos
    const interval = setInterval(() => fetchData(true), 10000);
    return () => clearInterval(interval);
  }, []);

  const handleApproval = async (conversationId: string, approved: boolean) => {
    try {
      const response = await api.post("/ai/operations/approval", {
        conversation_id: conversationId,
        approved,
        approver: "Administrador Co-Pilot"
      });

      if (response.data.status === "approved" || response.data.status === "rejected") {
        toast.success(approved ? "Ação aprovada com sucesso!" : "Ação rejeitada com sucesso!");
        fetchData(true);
      }
    } catch (error) {
      toast.error("Falha ao enviar decisão de aprovação.");
    }
  };

  const getHealthBadge = (health: string) => {
    switch (health) {
      case "operational":
      case "idle":
        return <Badge className="bg-emerald-500/20 text-emerald-500 border-emerald-500/30 font-bold">100% OPERACIONAL</Badge>;
      case "busy":
        return <Badge className="bg-amber-500/20 text-amber-500 border-amber-500/30 animate-pulse font-bold">PROCESSANDO FLUXO</Badge>;
      default:
        return <Badge className="bg-red-500/20 text-red-500 border-red-500/30 font-bold">INTERRUPÇÃO</Badge>;
    }
  };

  const getAgentStateBadge = (state: string) => {
    switch (state) {
      case "idle":
        return <Badge variant="outline" className="text-emerald-500 border-emerald-500/20 bg-emerald-500/5">Pronto</Badge>;
      case "busy":
      case "active":
        return <Badge variant="outline" className="text-blue-500 border-blue-500/20 bg-blue-500/5 animate-pulse">Pensando...</Badge>;
      case "waiting":
      case "requires_approval":
        return <Badge variant="outline" className="text-amber-500 border-amber-500/20 bg-amber-500/5">Aguardando Humano</Badge>;
      default:
        return <Badge variant="outline">{state}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex h-[80vh] w-full items-center justify-center flex-col gap-4">
        <Cpu className="h-12 w-12 animate-spin text-primary" />
        <p className="text-muted-foreground animate-pulse text-sm">Carregando painel operacional da Hierarquia de Agents...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12 animate-fade-in">
      {/* Top Cockpit Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-background/50 border border-border p-6 rounded-2xl backdrop-blur-md shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-primary/10 rounded-2xl border border-primary/20">
            <Bot className="h-7 w-7 text-primary animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-heading font-extrabold tracking-tight">Central de Inteligência Artificial</h1>
              {dashboard && getHealthBadge(dashboard.summary.health)}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Supervisão de 8 agentes autônomos cognitivos integrados via Event Bus e Redis.
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => fetchData(true)} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} /> Sincronizar
          </Button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="glass-card shadow-sm border-none">
          <CardContent className="pt-6 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Sessões Ativas</p>
              <h3 className="text-3xl font-extrabold mt-1">{dashboard?.summary.active_conversations || 0}</h3>
              <p className="text-[10px] text-muted-foreground mt-1">Conversas contínuas rodando</p>
            </div>
            <div className="h-12 w-12 bg-blue-500/10 text-blue-500 rounded-xl flex items-center justify-center">
              <MessageSquare className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card shadow-sm border-none">
          <CardContent className="pt-6 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Aprovações Pendentes</p>
              <h3 className="text-3xl font-extrabold mt-1 text-amber-500">{dashboard?.summary.waiting_approval || 0}</h3>
              <p className="text-[10px] text-muted-foreground mt-1">Ações que exigem aval do operador</p>
            </div>
            <div className="h-12 w-12 bg-amber-500/10 text-amber-500 rounded-xl flex items-center justify-center">
              <ShieldAlert className="h-6 w-6 animate-bounce" />
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card shadow-sm border-none">
          <CardContent className="pt-6 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Total de Agentes</p>
              <h3 className="text-3xl font-extrabold mt-1">8</h3>
              <p className="text-[10px] text-muted-foreground mt-1">Sub-agentes interconectados</p>
            </div>
            <div className="h-12 w-12 bg-emerald-500/10 text-emerald-500 rounded-xl flex items-center justify-center">
              <Cpu className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card shadow-sm border-none">
          <CardContent className="pt-6 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Eventos Recentes</p>
              <h3 className="text-3xl font-extrabold mt-1">{events.length}</h3>
              <p className="text-[10px] text-muted-foreground mt-1">Disparos de barramento de eventos</p>
            </div>
            <div className="h-12 w-12 bg-violet-500/10 text-violet-500 rounded-xl flex items-center justify-center">
              <Activity className="h-6 w-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Interface Content */}
        <div className="lg:col-span-2 space-y-6">
          <Tabs defaultValue="cockpit" className="w-full">
            <TabsList className="bg-muted/40 p-1 border border-border w-full flex justify-start rounded-xl mb-4">
              <TabsTrigger value="cockpit" className="rounded-lg text-xs font-bold px-4 py-2">
                <Cpu className="h-3.5 w-3.5 mr-2" /> Cockpit dos Agentes
              </TabsTrigger>
              <TabsTrigger value="approvals" className="rounded-lg text-xs font-bold px-4 py-2 relative">
                <ShieldAlert className="h-3.5 w-3.5 mr-2" /> Aprovações
                {conversations.filter(c => c.requires_approval).length > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 h-4 w-4 bg-amber-500 text-white rounded-full flex items-center justify-center text-[9px] font-black animate-pulse">
                    {conversations.filter(c => c.requires_approval).length}
                  </span>
                )}
              </TabsTrigger>
              <TabsTrigger value="conversations" className="rounded-lg text-xs font-bold px-4 py-2">
                <MessageSquare className="h-3.5 w-3.5 mr-2" /> Conversas Ativas
              </TabsTrigger>
              <TabsTrigger value="events" className="rounded-lg text-xs font-bold px-4 py-2">
                <Activity className="h-3.5 w-3.5 mr-2" /> Barramento de Eventos
              </TabsTrigger>
            </TabsList>

            {/* TAB: Cockpit */}
            <TabsContent value="cockpit">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.keys(AGENT_METADATA).map(agentKey => {
                  const meta = AGENT_METADATA[agentKey];
                  const backendStatus = dashboard?.agents.find(a => a.agent === agentKey);
                  const IconComponent = meta.icon;

                  return (
                    <Card key={agentKey} className="glass-card overflow-hidden hover-lift border-none flex flex-col justify-between">
                      <div>
                        <div className={`h-2 bg-gradient-to-r ${meta.color}`} />
                        <CardHeader className="p-4 flex flex-row items-start justify-between">
                          <div className="flex gap-3">
                            <div className={`p-2.5 rounded-xl bg-gradient-to-br ${meta.color} text-white shadow-lg`}>
                              <IconComponent className="h-5 w-5" />
                            </div>
                            <div>
                              <CardTitle className="text-sm font-black">{meta.name}</CardTitle>
                              <CardDescription className="text-[10px] uppercase font-bold mt-0.5 tracking-wide">
                                ID: {agentKey}
                              </CardDescription>
                            </div>
                          </div>
                          <div>
                            {getAgentStateBadge(backendStatus?.state || "idle")}
                          </div>
                        </CardHeader>
                        <CardContent className="px-4 pb-2 pt-0 space-y-3">
                          <p className="text-xs text-muted-foreground leading-relaxed">
                            {meta.desc}
                          </p>

                          <div className="flex flex-wrap gap-1">
                            {meta.tools.map((tool, idx) => (
                              <Badge key={idx} variant="secondary" className="text-[9px] px-2 py-0.5 font-medium border border-border">
                                {tool}
                              </Badge>
                            ))}
                          </div>
                        </CardContent>
                      </div>

                      <div className="p-4 pt-2 border-t border-border/40 mt-4 flex justify-between items-center bg-muted/10 text-xs">
                        <span className="text-[10px] text-muted-foreground font-medium">Execuções Recentes:</span>
                        <Badge variant="outline" className="font-extrabold text-[10px] px-2 py-0.5 bg-background">
                          {backendStatus?.recent_executions || 0}
                        </Badge>
                      </div>
                    </Card>
                  );
                })}
              </div>
            </TabsContent>

            {/* TAB: Approvals */}
            <TabsContent value="approvals">
              <Card className="glass-card border-none shadow-xl">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <UserCheck className="h-5 w-5 text-amber-500" /> Decisões da Operação (Human-in-the-Loop)
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Agentes identificaram decisões de autonomia moderada que exigem consentimento prévio do supervisor.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {conversations.filter(c => c.requires_approval).length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground border-2 border-dashed border-border rounded-2xl flex flex-col items-center justify-center gap-2 bg-background/5">
                      <ShieldCheck className="h-10 w-10 text-emerald-500/60" />
                      <p className="font-bold text-sm">Nenhuma aprovação pendente</p>
                      <p className="text-xs max-w-[280px]">Tudo sob controle! A autonomia dos agentes está operando no nível padrão.</p>
                    </div>
                  ) : (
                    conversations.filter(c => c.requires_approval).map(conv => (
                      <div key={conv.id} className="p-4 bg-muted/20 border border-amber-500/20 rounded-xl space-y-4 shadow-sm animate-pulse-subtle">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge className="bg-amber-500 text-white text-[9px] font-black">SOLICITAÇÃO DE APROVAÇÃO</Badge>
                            <span className="text-xs text-muted-foreground font-bold">ID: #{conv.id.slice(0, 8)}</span>
                          </div>
                          <Badge variant="outline" className="text-xs font-medium">
                            Origem: {conv.client_phone}
                          </Badge>
                        </div>

                        <div className="bg-background/80 border border-border p-3.5 rounded-lg space-y-2 text-xs">
                          <div className="flex items-center gap-1.5 font-bold text-primary">
                            <Bot className="h-4 w-4" /> Resposta Planejada ({conv.current_agent}):
                          </div>
                          <p className="text-muted-foreground italic leading-relaxed">
                            &quot;Olá João, identifiquei sua mensagem. Planejo agendar seu banho para amanhã, 18/05 às 10:00 com o profissional Carlos. Confirma essa reserva?&quot;
                          </p>
                          <div className="pt-2 text-[10px] text-muted-foreground/80 flex items-center gap-1 font-semibold border-t">
                            <Clock className="h-3.5 w-3.5" /> Intenção Detectada: <span className="text-primary uppercase font-bold">{conv.intent || "Agendamento"}</span>
                          </div>
                        </div>

                        <div className="flex gap-2 justify-end">
                          <Button size="sm" variant="outline" className="border-red-500/20 text-red-500 hover:bg-red-500/10 text-xs font-bold" onClick={() => handleApproval(conv.id, false)}>
                            <ThumbsDown className="h-4 w-4 mr-2" /> Rejeitar e Corrigir
                          </Button>
                          <Button size="sm" className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-lg shadow-emerald-500/20" onClick={() => handleApproval(conv.id, true)}>
                            <ThumbsUp className="h-4 w-4 mr-2" /> Aprovar e Disparar
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* TAB: Conversations */}
            <TabsContent value="conversations">
              <Card className="glass-card border-none shadow-xl">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <MessageSquare className="h-5 w-5 text-primary" /> Sessões Cognitivas de Clientes
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Diálogos ativos no whatsapp sendo processados e gerenciados pela hierarquia de agentes em tempo real.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {conversations.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground border-2 border-dashed border-border rounded-2xl bg-background/5">
                      Nenhuma conversa ativa com agentes no momento.
                    </div>
                  ) : (
                    conversations.map(conv => (
                      <div key={conv.id} className="flex justify-between items-center p-4 rounded-xl border bg-muted/20 hover:bg-muted/40 transition-colors">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 bg-background rounded-full border flex items-center justify-center">
                            <Bot className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-extrabold text-sm">{conv.client_phone}</p>
                              {conv.requires_approval && (
                                <Badge className="bg-amber-500 text-white text-[9px] font-black">Aguardando Aprovação</Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground">
                              Agente: <span className="font-semibold text-primary">{conv.current_agent || "Supervisor"}</span> • Etapa: {conv.step}
                            </p>
                          </div>
                        </div>
                        <div>
                          <Badge variant="secondary" className="uppercase text-[9px] font-bold">
                            {conv.intent || "Geral"}
                          </Badge>
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* TAB: Events */}
            <TabsContent value="events">
              <Card className="glass-card border-none shadow-xl">
                <CardHeader className="flex flex-row items-center justify-between p-4">
                  <div>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Activity className="h-5 w-5 text-violet-500" /> Fluxo do Event Bus
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Histórico granular das transmissões cognitivas de eventos entre agentes e ferramentas.
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className="font-bold bg-background text-[10px]">
                    Últimos {events.length} eventos
                  </Badge>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[450px]">
                    <div className="divide-y divide-border/40">
                      {events.length === 0 ? (
                        <div className="text-center py-12 text-muted-foreground">Nenhum evento registrado no barramento de eventos.</div>
                      ) : (
                        events.map((event, idx) => (
                          <div key={event.id || idx} className="p-4 hover:bg-muted/10 transition-colors flex items-start gap-3">
                            <div className="h-7 w-7 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <Activity className="h-4 w-4" />
                            </div>
                            <div className="space-y-1.5 flex-1 min-w-0">
                              <div className="flex items-center justify-between gap-2">
                                <span className="text-xs font-bold text-foreground font-mono truncate">
                                  {event.event_type}
                                </span>
                                <span className="text-[10px] text-muted-foreground font-medium">
                                  {new Date(event.timestamp).toLocaleTimeString("pt-BR")}
                                </span>
                              </div>
                              <p className="text-[11px] text-muted-foreground leading-normal">
                                Origem: <span className="font-bold text-foreground">{event.source_agent || "Sistema"}</span>
                                {event.target_agent && (
                                  <>
                                    {" "}
                                    <ArrowRight className="h-3 w-3 inline text-muted-foreground mx-1" />{" "}
                                    Destino: <span className="font-bold text-foreground">{event.target_agent}</span>
                                  </>
                                )}
                              </p>
                              {event.payload && (
                                <pre className="bg-background/60 border p-2.5 rounded-lg text-[9px] font-mono text-muted-foreground overflow-x-auto max-h-24">
                                  {JSON.stringify(event.payload, null, 2)}
                                </pre>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Actionable Side Panel */}
        <div className="space-y-6">
          {/* Diagnostic & Suggestions */}
          <Card className="glass-card border-none bg-amber-500/5 border-amber-500/10 shadow-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-5">
              <Bot className="h-20 w-20 rotate-12" />
            </div>
            <CardHeader>
              <CardTitle className="text-sm font-extrabold text-amber-500 flex items-center gap-2">
                <Sparkles className="h-5 w-5 animate-pulse" /> Recomendações da IA
              </CardTitle>
              <CardDescription className="text-xs text-amber-600/80">
                Sugestões automatizadas para otimização da operação e correções de fluxos de agentes.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {suggestions.length === 0 ? (
                <div className="text-xs text-amber-600/80 py-4 text-center">Tudo rodando com perfeição na central autônoma! ✅</div>
              ) : (
                suggestions.map((sugg, idx) => (
                  <div key={idx} className="flex justify-between items-center text-xs p-3 rounded-xl bg-background/50 border border-amber-500/10 shadow-sm">
                    <span className="font-bold text-amber-600 truncate max-w-[170px]">{sugg.title}</span>
                    <Badge className="bg-amber-600 text-white font-extrabold text-[10px]">{sugg.count}</Badge>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Autonomy Level Cockpit */}
          <Card className="glass-card border-none shadow-xl">
            <CardHeader>
              <CardTitle className="text-sm font-extrabold flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-primary" /> Níveis de Autonomia Cognitiva
              </CardTitle>
              <CardDescription className="text-xs">
                Controle o nível de liberdade operacional concedido à hierarquia de agentes.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="p-3 bg-primary/5 rounded-xl border border-primary/20 space-y-1.5 cursor-pointer">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-black text-primary">Nível 1: Copiloto / Assistido</span>
                    <Badge variant="outline" className="text-[8px] bg-background">ATIVO</Badge>
                  </div>
                  <p className="text-[10px] text-muted-foreground leading-normal">
                    Toda e qualquer resposta ou agendamento planejado pelos agentes precisa obrigatoriamente de validação de um supervisor humano.
                  </p>
                </div>

                <div className="p-3 bg-muted/20 hover:bg-muted/40 rounded-xl space-y-1.5 opacity-60 transition-colors cursor-not-allowed">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-black text-foreground">Nível 2: Semiautônomo</span>
                    <Badge variant="outline" className="text-[8px] bg-background">BLOQUEADO</Badge>
                  </div>
                  <p className="text-[10px] text-muted-foreground leading-normal">
                    Respostas gerais e agendamentos simples são diretos. Ações de alto valor (como faturamento ou alteração cadastral) exigem aprovação.
                  </p>
                </div>

                <div className="p-3 bg-muted/20 hover:bg-muted/40 rounded-xl space-y-1.5 opacity-60 transition-colors cursor-not-allowed">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-black text-foreground">Nível 3: Autônomo com Guardrails</span>
                    <Badge variant="outline" className="text-[8px] bg-background">BLOQUEADO</Badge>
                  </div>
                  <p className="text-[10px] text-muted-foreground leading-normal">
                    Autonomia total de fluxo de conversa e agendamentos. Apenas compras de insumos acima de R$ 500 exigem supervisão.
                  </p>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <Button size="sm" variant="ghost" className="text-xs font-bold text-muted-foreground">
                  Mais configurações <ArrowRight className="h-3.5 w-3.5 ml-1" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
