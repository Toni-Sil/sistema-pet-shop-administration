import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  CalendarPlus, 
  ClipboardCheck, 
  Clock, 
  Settings2, 
  Droplets, 
  Scissors, 
  Truck, 
  Package, 
  Calendar as CalendarIcon, 
  ChevronLeft, 
  ChevronRight,
  List as ListIcon,
  Hotel,
  Stethoscope,
  MessageCircle,
  Droplets as WavesIcon,
  Sparkles as SparklesIcon,
  CheckCircle,
  Coffee,
  Gamepad2
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { 
  format, 
  startOfMonth, 
  endOfMonth, 
  eachDayOfInterval, 
  isSameDay, 
  addMonths, 
  subMonths,
  startOfWeek,
  endOfWeek,
  isToday,
  parseISO
} from "date-fns";
import { ptBR } from "date-fns/locale";
import { POSModal } from "@/components/POSModal";

interface Appointment {
  id: string;
  pet_id?: string;
  pet_name?: string;
  service: string;
  professional?: string;
  date: string;
  time: string;
  status: string;
  notes?: string;
  price?: string;
  type?: 'service' | 'hotel';
}

const statusColors: Record<string, string> = {
  scheduled: "bg-primary/10 text-primary",
  in_progress: "bg-amber-100 text-amber-600",
  done: "bg-emerald-100 text-emerald-600",
  absent: "bg-destructive/10 text-destructive",
  cancelled: "bg-muted text-muted-foreground",
};

const statusLabels: Record<string, string> = {
  scheduled: "Agendado",
  in_progress: "Em atendimento",
  done: "Concluído",
  absent: "Faltou",
  cancelled: "Cancelado",
};

const SERVICE_SECTIONS = [
  { key: "all", label: "Todos", icon: ClipboardCheck },
  { key: "banho", label: "Banho", icon: Droplets },
  { key: "tosa", label: "Tosa", icon: Scissors },
  { key: "clinica", label: "Clínica", icon: Stethoscope },
  { key: "hotel", label: "Hotel", icon: Hotel },
  { key: "entrega", label: "Entrega", icon: Truck },
  { key: "encomenda", label: "Encomenda", icon: Package },
  { key: "recebimento", label: "Recebimento", icon: Package },
] as const;

type ServiceSectionKey = typeof SERVICE_SECTIONS[number]["key"];

const matchServiceSection = (serviceName: string | undefined, section: ServiceSectionKey) => {
  if (section === "all") return true;
  const normalized = (serviceName || "").toLowerCase();
  if (section === "recebimento") {
    return normalized.includes("recebimento") || normalized.includes("mercadoria");
  }
  if (section === "hotel") {
    return normalized.includes("hotel") || normalized.includes("hospedagem") || normalized.includes("pernoite");
  }
  if (section === "clinica") {
    return normalized.includes("clinica") || normalized.includes("consulta") || normalized.includes("vacina") || normalized.includes("vet");
  }
  return normalized.includes(section);
};
const Services = () => {
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"list" | "calendar">("calendar");
  const [currentDate, setCurrentDate] = useState(new Date());
  const [serviceSection, setServiceSection] = useState<ServiceSectionKey>("all");
  
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);
  const [isDayModalOpen, setIsDayModalOpen] = useState(false);

  const [isPOSOpen, setIsPOSOpen] = useState(false);
  const [posInitialData, setPosInitialData] = useState<any>(null);

  const [estimatedDuration, setEstimatedDuration] = useState<number | null>(null);

  const loadAppointments = async () => {
    setLoading(true);
    try {
      let endpoint = "/agendamentos";
      let params = "";
      
      if (viewMode === "calendar") {
        const start = format(startOfMonth(currentDate), "yyyy-MM-dd");
        const end = format(endOfMonth(currentDate), "yyyy-MM-dd");
        endpoint = "/agendamentos/unified";
        params = `?start_date=${start}&end_date=${end}`;
      } else {
        // List mode: today
        params = `?data=${format(new Date(), "yyyy-MM-dd")}`;
      }
      
      const { data } = await api.get(`${endpoint}${params}`);
      setAppointments(data);
    } catch {
      toast.error("Erro ao carregar agendamentos.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAppointments(); }, [viewMode, currentDate]);

  const displayedAppointments = useMemo(
    () => appointments.filter((a) => matchServiceSection(a.service, serviceSection)),
    [appointments, serviceSection]
  );

  const updateStatus = async (id: string, status: string) => {
    try {
      await api.patch(`/agendamentos/${id}`, { status });
      setAppointments(prev => prev.map(a => a.id === id ? { ...a, status } : a));
      toast.success("Status atualizado!");
    } catch {
      toast.error("Erro ao atualizar status.");
    }
  };

  const handleFinishWithSale = (app: Appointment) => {
    setPosInitialData({
      client_id: app.pet_id,
      appointment_id: app.id,
      items: [{
        id: 'service-' + app.id,
        name: app.service.replace('_', ' '),
        price: Number(app.price || 0),
        qty: 1
      }]
    });
    setIsPOSOpen(true);
  };

  const sendWhatsAppStatus = async (petId: string, type: string) => {
    try {
      await api.post("/whatsapp/status-update", null, { params: { pet_id: petId, status_type: type } });
      toast.success("Status enviado ao tutor!");
    } catch {
      toast.error("Erro ao enviar status.");
    }
  };

  const calendarDays = useMemo(() => {
    const start = startOfWeek(startOfMonth(currentDate));
    const end = endOfWeek(endOfMonth(currentDate));
    return eachDayOfInterval({ start, end });
  }, [currentDate]);

  const getAppointmentsForDay = (day: Date) => {
    return displayedAppointments.filter(a => isSameDay(parseISO(a.date), day));
  };

  const renderCalendar = () => {
    return (
      <div className="grid grid-cols-7 gap-px bg-white/5 border border-white/10 rounded-[2rem] overflow-hidden shadow-2xl backdrop-blur-md">
        {["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"].map(d => (
          <div key={d} className="bg-white/10 py-5 text-center text-[10px] sm:text-xs font-black text-primary border-b border-white/10 uppercase tracking-[0.2em]">
            {d}
          </div>
        ))}
        {calendarDays.map((day) => {
          const dayApps = getAppointmentsForDay(day);
          const isSelectedMonth = day.getMonth() === currentDate.getMonth();
          
          return (
            <div 
              key={day.toISOString()} 
              onClick={() => { setSelectedDay(day); setIsDayModalOpen(true); }}
              className={`min-h-[120px] sm:min-h-[150px] bg-transparent p-3 flex flex-col gap-2 transition-all cursor-pointer hover:bg-white/[0.05] group relative border-[0.5px] border-white/5 ${
                !isSelectedMonth ? "opacity-20 grayscale" : ""
              }`}
            >
              <div className="flex justify-between items-start">
                <span className={`text-[11px] sm:text-xs font-black w-9 h-9 flex items-center justify-center rounded-2xl transition-all duration-300 group-hover:scale-110 group-hover:shadow-lg group-hover:shadow-primary/20 ${
                  isToday(day) 
                    ? "bg-primary text-white shadow-xl shadow-primary/30" 
                    : "text-white/60 group-hover:text-primary group-hover:bg-primary/10"
                }`}>
                  {format(day, "d")}
                </span>
                {dayApps.length > 0 && (
                  <div className="text-[10px] sm:text-xs font-black text-primary px-2 py-1 rounded-full bg-primary/10 border border-primary/20">
                    {dayApps.length}
                  </div>
                )}
              </div>
              <div className="flex-1 overflow-hidden space-y-1.5 pt-1">
                {dayApps.slice(0, 3).map(app => (
                  <div 
                    key={app.id}
                    className={`text-[9px] sm:text-[10px] p-2 rounded-xl truncate border border-white/5 shadow-sm font-bold backdrop-blur-md transition-all group-hover:translate-x-1 ${
                      app.type === 'hotel' ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30' : statusColors[app.status]
                    } border-l-4 border-l-current/10`}
                  >
                    <span className="opacity-70 mr-1.5">{app.time}</span>
                    <span className="capitalize">{app.pet_name ? `${app.pet_name}: ` : ""}{app.service.split('_').join(' + ')}</span>
                  </div>
                ))}
                {dayApps.length > 3 && (
                  <div className="text-[10px] text-primary/80 font-black pl-1 uppercase tracking-tighter animate-pulse">
                    + {dayApps.length - 3} mais
                  </div>
                )}
              </div>
              <div className="absolute inset-0 border-t border-l border-white/5 pointer-events-none" />
            </div>
          );
        })}
      </div>
    );
  };

  const renderList = () => {
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b-2 text-left text-[10px] uppercase tracking-widest font-black text-muted-foreground">
              <th className="pb-3 pr-4">Data</th>
              <th className="pb-3 pr-4">Horário</th>
              <th className="pb-3 pr-4">Serviço</th>
              <th className="pb-3 pr-4">Profissional</th>
              <th className="pb-3 pr-4">Status</th>
              <th className="pb-3 text-right">Ação</th>
            </tr>
          </thead>
          <tbody>
            {displayedAppointments.map((a) => (
              <tr key={a.id} className="border-b border-border/40 last:border-0 hover:bg-primary/[0.02] transition-colors group">
                <td className="py-4 pr-4 font-medium text-muted-foreground">{format(parseISO(a.date), "dd/MM/yy")}</td>
                <td className="py-4 pr-4 font-black text-primary">{a.time}</td>
                <td className="py-4 pr-4">
                  <div className="flex flex-col">
                    <span className="capitalize font-black text-foreground/90">{a.service?.replace("_", " + ") || "Serviço"}</span>
                    {a.notes && (
                      <span className="text-[11px] text-muted-foreground truncate max-w-[200px] italic">"{a.notes.split('\n')[0]}"</span>
                    )}
                  </div>
                </td>
                <td className="py-4 pr-4 text-muted-foreground font-medium">{a.professional || "Não atribuído"}</td>
                <td className="py-4 pr-4">
                  <Badge variant="outline" className={`font-black uppercase text-[10px] tracking-tighter ${statusColors[a.status]} border-none shadow-sm`}>
                    {statusLabels[a.status] || a.status}
                  </Badge>
                </td>
                <td className="py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Button 
                      size="sm" 
                      variant="ghost" 
                      onClick={() => { setSelectedAppointment(a); setIsDetailsOpen(true); }}
                      className="h-9 w-9 p-0 rounded-xl hover:bg-primary/10 hover:text-primary transition-all"
                    >
                      <Settings2 className="h-4 w-4" />
                    </Button>

                    {a.status === "scheduled" && (
                      <Button size="sm" variant="secondary" onClick={() => updateStatus(a.id, "in_progress")} className="h-9 font-bold px-4 rounded-xl shadow-sm hover:translate-y-[-1px] transition-all">
                         Atender
                      </Button>
                    )}
                    {a.status === "in_progress" && (
                      <Button size="sm" onClick={() => handleFinishWithSale(a)} className="h-9 bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-4 rounded-xl shadow-lg shadow-emerald-200/50 hover:translate-y-[-1px] transition-all">
                        Concluir
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {displayedAppointments.length === 0 && (
          <div className="text-center py-16 space-y-4">
              <div className="mx-auto w-20 h-20 rounded-full bg-muted/20 flex items-center justify-center">
                <ClipboardCheck className="h-10 w-10 text-muted-foreground/30" />
              </div>
              <p className="text-muted-foreground font-bold italic">Nenhum compromisso encontrado para este filtro.</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in pb-16">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6 px-2">
        <div className="space-y-1">
          <Badge className="bg-primary/10 text-primary hover:bg-primary/20 border-none px-3 mb-2 font-black uppercase tracking-[0.2em] text-[10px]">Agenda Profissional</Badge>
          <h1 className="text-4xl font-black tracking-tighter bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">Fluxo de Atendimento</h1>
          <p className="text-muted-foreground font-medium max-w-lg italic">Visualize e gerencie a rotina da sua loja com elegância e precisão.</p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex bg-white/5 p-2 rounded-3xl border border-white/10 backdrop-blur-xl shadow-2xl overflow-hidden">
            <Button 
              size="sm" 
              variant="ghost" 
              className={`h-11 px-6 rounded-2xl font-black transition-all uppercase tracking-tighter text-xs ${viewMode === "calendar" ? "bg-primary text-white shadow-xl shadow-primary/30" : "text-white/40 hover:text-white"}`}
              onClick={() => setViewMode("calendar")}
            >
              <CalendarIcon className="h-4 w-4 mr-2" /> Visual
            </Button>
            <Button 
              size="sm" 
              variant="ghost" 
              className={`h-11 px-6 rounded-2xl font-black transition-all uppercase tracking-tighter text-xs ${viewMode === "list" ? "bg-primary text-white shadow-xl shadow-primary/30" : "text-white/40 hover:text-white"}`}
              onClick={() => setViewMode("list")}
            >
              <ListIcon className="h-4 w-4 mr-2" /> Tabela
            </Button>
          </div>
          <Button onClick={() => navigate("/servicos/novo-agendamento")} className="h-11 px-6 rounded-2xl font-black shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all bg-primary text-white border-none">
            <CalendarPlus className="h-5 w-5 mr-2" /> NOVO SERVIÇO
          </Button>
        </div>
      </div>

      {/* Navigation Header for Calendar */}
      {viewMode === "calendar" && (
        <Card className="bg-white/5 border border-white/10 shadow-2xl overflow-hidden rounded-3xl backdrop-blur-md">
          <CardContent className="p-0 flex flex-col sm:flex-row items-center justify-between">
            <div className="flex items-center gap-6 p-4 sm:p-6 w-full sm:w-auto bg-white/5">
              <Button variant="ghost" size="icon" onClick={() => setCurrentDate(subMonths(currentDate, 1))} className="h-10 w-10 rounded-xl hover:bg-white/10 text-white">
                <ChevronLeft className="h-6 w-6" />
              </Button>
              <h2 className="text-2xl font-black capitalize min-w-[200px] text-center tracking-tighter text-white">
                {format(currentDate, "MMMM yyyy", { locale: ptBR })}
              </h2>
              <Button variant="ghost" size="icon" onClick={() => setCurrentDate(addMonths(currentDate, 1))} className="h-10 w-10 rounded-xl hover:bg-white/10 text-white">
                <ChevronRight className="h-6 w-6" />
              </Button>
            </div>
            
            <div className="flex items-center gap-6 p-4 sm:p-6">
               <button onClick={() => setCurrentDate(new Date())} className="text-sm font-black uppercase tracking-widest text-primary hover:underline underline-offset-4">Ir para Hoje</button>
               <div className="h-8 w-px bg-white/10 hidden sm:block" />
               <Badge variant="outline" className="text-[11px] font-black px-4 py-1.5 rounded-full border-primary/20 bg-primary/5 text-primary">
                 {displayedAppointments.length} AGENDAMENTOS
               </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="glass-card border-none shadow-xl rounded-3xl bg-card/60 backdrop-blur-md">
            <CardHeader className="pb-4 border-b border-border/40 px-6">
              <CardTitle className="text-[10px] font-black uppercase tracking-[0.3em] text-muted-foreground">Especialidades</CardTitle>
            </CardHeader>
            <CardContent className="pt-6 px-4 flex sm:flex-col overflow-x-auto gap-2 sm:space-y-1.5 sm:overflow-x-visible pb-6 sm:pb-8">
              {SERVICE_SECTIONS.map((section) => {
                const Icon = section.icon;
                const active = serviceSection === section.key;
                return (
                  <button
                    key={section.key}
                    onClick={() => setServiceSection(section.key)}
                    className={`whitespace-nowrap px-4 py-3.5 rounded-2xl text-sm font-black transition-all flex items-center gap-3 relative overflow-hidden group ${
                      active 
                        ? "bg-primary text-primary-foreground shadow-lg shadow-primary/30 scale-[1.05] z-10" 
                        : "hover:bg-primary/5 text-muted-foreground/80 hover:text-foreground"
                    }`}
                  >
                    <Icon className={`h-4 w-4 shrink-0 transition-transform group-hover:scale-110 ${active ? "text-white" : "text-primary/60"}`} />
                    {section.label}
                    {active && <div className="absolute right-3 w-1.5 h-1.5 rounded-full bg-white animate-pulse" />}
                  </button>
                );
              })}
            </CardContent>
          </Card>
          
          {/* Quick stats or Legend */}
          <Card className="glass-card border-none shadow-lg rounded-3xl p-6 bg-primary/5 hidden lg:block">
            <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-4">Legenda de Status</p>
            <div className="space-y-3">
              {Object.entries(statusLabels).map(([key, label]) => (
                <div key={key} className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${statusColors[key]} border-[1.5px] border-current/20 shadow-sm`} />
                  <span className="text-xs font-bold text-foreground/70">{label}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Main Content Area */}
        <div className="lg:col-span-3">
          <Card className="glass-card shadow-2xl border-none overflow-hidden rounded-[2.5rem] bg-card/40 backdrop-blur-xl ring-1 ring-white/10">
            <CardHeader className="bg-gradient-to-b from-primary/[0.03] to-transparent border-b border-border/30 py-6 px-8">
              <CardTitle className="text-xl font-black flex items-center gap-3 tracking-tighter">
                <div className="p-2 rounded-2xl bg-primary shadow-lg shadow-primary/20">
                  <Clock className="h-5 w-5 text-primary-foreground" />
                </div>
                {viewMode === "calendar" ? "Calendário de Operações" : "Cronograma do Dia"}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 sm:p-8 overflow-hidden">
              {loading ? (
                <div className="grid grid-cols-7 gap-4">
                  {Array.from({ length: 28 }).map((_, i) => (
                    <Skeleton key={i} className="h-32 w-full rounded-2xl bg-primary/5 animate-pulse" />
                  ))}
                </div>
              ) : (
                viewMode === "calendar" ? renderCalendar() : renderList()
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Day View Modal */}
      <Dialog open={isDayModalOpen} onOpenChange={setIsDayModalOpen}>
        <DialogContent className="sm:max-w-[580px] overflow-hidden rounded-[2.5rem] p-0 gap-0 border border-white/10 shadow-2xl bg-[#0a0a0b]/98 backdrop-blur-3xl ring-1 ring-white/10">
          <DialogHeader className="p-8 bg-white/[0.03] border-b border-white/10 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/20 rounded-full -mr-32 -mt-32 blur-[80px]" />
            <DialogTitle className="flex flex-col gap-4 relative z-10">
              <div className="flex items-center gap-4">
                <div className="p-3.5 rounded-[1.5rem] bg-primary shadow-xl shadow-primary/30">
                  <CalendarIcon className="h-6 w-6 text-white" />
                </div>
                <div className="space-y-0.5">
                  <Badge variant="outline" className="border-primary/50 text-primary text-[9px] font-black tracking-[0.3em] uppercase px-3 h-6">Agenda Diária</Badge>
                  <h3 className="text-2xl font-black tracking-tight text-white">Cronograma do Dia</h3>
                </div>
              </div>
              <p className="text-base font-black text-white/50 ml-[3.5rem] flex items-center gap-2">
                <ChevronRight className="h-5 w-5 text-primary" />
                {selectedDay && format(selectedDay, "EEEE, d 'de' MMMM", { locale: ptBR })}
              </p>
            </DialogTitle>
          </DialogHeader>
          
          <div className="p-6 max-h-[60vh] overflow-y-auto custom-scrollbar space-y-4 bg-transparent">
            {selectedDay && (
              getAppointmentsForDay(selectedDay).length === 0 ? (
                <div className="text-center py-16 px-10 space-y-6">
                   <div className="mx-auto w-20 h-20 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                     <Clock className="h-8 w-8 text-white/10" />
                   </div>
                   <div className="space-y-1">
                    <p className="text-xl font-black text-white/60 tracking-tight">Sem atividades registradas</p>
                    <p className="text-white/20 font-bold italic text-xs">Este dia está livre no cronograma.</p>
                   </div>
                   <Button onClick={() => navigate("/servicos/novo-agendamento")} className="rounded-xl h-11 font-black px-8 shadow-xl shadow-primary/20 border-none bg-primary text-white uppercase tracking-widest text-[10px]">Agendar Serviço</Button>
                </div>
              ) : (
                <div className="space-y-3 relative before:absolute before:left-[2.5rem] before:top-2 before:bottom-2 before:w-px before:bg-white/5">
                  {getAppointmentsForDay(selectedDay).sort((a,b) => a.time.localeCompare(b.time)).map(app => (
                    <div 
                      key={app.id}
                      onClick={() => { setSelectedAppointment(app); setIsDetailsOpen(true); }}
                      className="group bg-white/[0.03] p-4 rounded-[1.5rem] border border-white/5 shadow-lg hover:shadow-2xl hover:border-primary/40 hover:bg-white/5 transition-all duration-300 cursor-pointer flex items-center justify-between overflow-hidden relative"
                    >
                      <div className="flex items-center gap-5 relative z-10">
                        <div className={`w-14 h-14 rounded-2xl flex flex-col items-center justify-center shrink-0 shadow-lg border border-white/10 font-bold ${statusColors[app.status]}`}>
                          <span className="text-[14px] leading-none tracking-tighter">{app.time}</span>
                        </div>
                        <div className="space-y-1">
                          <p className="font-black text-lg tracking-tight text-white group-hover:text-primary transition-colors capitalize leading-none">{app.service.replace("_", "+")}</p>
                          <div className="flex items-center gap-3 text-[10px] font-black text-white/40">
                            <span className="uppercase tracking-widest">{app.professional || "Padrão"}</span>
                            {app.price && (
                              <span className="text-emerald-400">R$ {Number(app.price).toFixed(2)}</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="shrink-0 flex items-center gap-4 relative z-10">
                        <Badge variant="outline" className={`font-black uppercase text-[9px] tracking-widest border-none px-3 py-1 ${statusColors[app.status]} shadow-lg`}>
                          {statusLabels[app.status]}
                        </Badge>
                        <ChevronRight className="h-5 w-5 text-white/10 group-hover:text-primary transition-colors" />
                      </div>
                    </div>
                  ))}
                </div>
              )
            )}
          </div>
          <div className="p-6 bg-white/[0.02] border-t border-white/10 flex justify-center">
             <Button variant="ghost" className="font-black text-[10px] uppercase tracking-[0.3em] text-white/30 hover:bg-white/5 hover:text-white rounded-xl h-10 px-8" onClick={() => setIsDayModalOpen(false)}>Fechar Registro</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Appointment Details Dialog */}
      <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
        <DialogContent className="sm:max-w-[480px] overflow-hidden rounded-[3.5rem] p-0 gap-0 border border-white/10 shadow-2xl z-[60] bg-[#0a0a0b]/98 backdrop-blur-3xl ring-1 ring-white/10">
          <DialogHeader className="p-10 bg-gradient-to-b from-primary/10 to-transparent relative">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full blur-[50px]" />
            <DialogTitle className="flex items-center gap-4 relative z-10">
              <div className="p-3 rounded-[1.25rem] bg-primary text-primary-foreground shadow-2xl shadow-primary/40 scale-110">
                <Settings2 className="h-6 w-6" />
              </div>
              <div className="space-y-0.5">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Gestão de Serviço</p>
                <h2 className="text-2xl font-black tracking-tighter text-white">Painel Técnico</h2>
              </div>
            </DialogTitle>
          </DialogHeader>
          
          {selectedAppointment && (
            <div className="p-10 pt-4 space-y-8">
              <div className="flex justify-between items-end">
                <div className="space-y-1">
                  <p className="text-[10px] uppercase font-black text-muted-foreground tracking-[0.4em] mb-1">Especialidade</p>
                  <p className="text-4xl font-black tracking-tight text-foreground/90 capitalize leading-[0.8]">{selectedAppointment.service.replace("_", " ")}</p>
                </div>
                <Badge variant="outline" className={`${statusColors[selectedAppointment.status]} border-2 border-current shadow-2xl shadow-current/10 font-black px-6 py-2 rounded-2xl text-xs uppercase tracking-tighter`}>
                  {statusLabels[selectedAppointment.status]}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-4 bg-white/5 p-6 rounded-[2.5rem] border border-white/5 backdrop-blur-sm relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-tr from-primary/[0.05] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="space-y-1 relative z-10">
                  <p className="text-[10px] uppercase font-black text-white/20 tracking-widest opacity-60">Data Agendada</p>
                  <p className="text-base font-black flex items-center gap-2 pr-4 text-white/80">{format(parseISO(selectedAppointment.date), "dd · MM · yyyy")}</p>
                </div>
                <div className="space-y-1 relative z-10 border-l border-white/5 pl-4">
                  <p className="text-[10px] uppercase font-black text-white/20 tracking-widest opacity-60">Início</p>
                  <p className="text-base font-black flex items-center gap-2 tracking-widest text-primary">{selectedAppointment.time}</p>
                </div>
                <div className="space-y-1 relative z-10 mt-4">
                  <p className="text-[10px] uppercase font-black text-white/20 tracking-widest opacity-60">Responsável</p>
                  <p className="text-base font-black truncate text-white/80">{selectedAppointment.professional || "Time Master"}</p>
                </div>
                <div className="space-y-1 relative z-10 mt-4 border-l border-white/5 pl-4">
                  <p className="text-[10px] uppercase font-black text-white/20 tracking-widest opacity-60">Custo Total</p>
                  <p className="text-xl font-black text-emerald-400 tracking-tighter">R$ {Number(selectedAppointment.price || 0).toFixed(2)}</p>
                </div>
              </div>

              {selectedAppointment.notes && (
                <div className="p-4 rounded-2xl bg-muted/30 border border-muted/50">
                  <p className="text-[10px] text-muted-foreground uppercase font-black mb-1">Observações</p>
                  <p className="text-sm">{selectedAppointment.notes}</p>
                </div>
              )}

              {/* Live Status Section */}
              <div className="p-4 rounded-[2rem] bg-emerald-500/5 border border-emerald-500/10 space-y-3">
                 <div className="flex items-center gap-2 mb-1">
                    <MessageCircle className="h-4 w-4 text-emerald-500" />
                    <span className="text-[10px] font-black uppercase text-emerald-600">Live Status (WhatsApp)</span>
                 </div>
                 <div className="grid grid-cols-5 gap-2">
                    <Button variant="outline" size="icon" className="rounded-2xl h-12 w-full hover:bg-emerald-500 hover:text-white" onClick={() => sendWhatsAppStatus(selectedAppointment.pet_id!, "bath_start")} title="Iniciou Banho">
                      <WavesIcon className="h-5 w-5" />
                    </Button>
                    <Button variant="outline" size="icon" className="rounded-2xl h-12 w-full hover:bg-emerald-500 hover:text-white" onClick={() => sendWhatsAppStatus(selectedAppointment.pet_id!, "bath_end")} title="Terminou Banho">
                      <SparklesIcon className="h-5 w-5" />
                    </Button>
                    <Button variant="outline" size="icon" className="rounded-2xl h-12 w-full hover:bg-emerald-500 hover:text-white" onClick={() => sendWhatsAppStatus(selectedAppointment.pet_id!, "meal")} title="Alimentação">
                      <Coffee className="h-5 w-5" />
                    </Button>
                    <Button variant="outline" size="icon" className="rounded-2xl h-12 w-full hover:bg-emerald-500 hover:text-white" onClick={() => sendWhatsAppStatus(selectedAppointment.pet_id!, "play")} title="Diversão">
                      <Gamepad2 className="h-5 w-5" />
                    </Button>
                    <Button variant="outline" size="icon" className="rounded-2xl h-12 w-full hover:bg-emerald-500 hover:text-white" onClick={() => sendWhatsAppStatus(selectedAppointment.pet_id!, "sleep")} title="Descanso">
                      <CheckCircle className="h-5 w-5" />
                    </Button>
                 </div>
              </div>

              <div className="space-y-4">
                  <div className="flex items-center gap-2 ml-1">
                    <div className="h-4 w-1 bg-primary rounded-full" />
                    <p className="text-[11px] uppercase font-black text-muted-foreground tracking-[0.2em]">Memorial Descritivo</p>
                  </div>
                  <div className="text-sm bg-primary/[0.03] p-6 rounded-[2rem] border border-border/60 leading-relaxed font-medium text-foreground/80 italic shadow-inner">
                    "{selectedAppointment.notes}"
                  </div>
              </div>

              <div className="pt-6 flex flex-col gap-4">
                {selectedAppointment.status === "scheduled" && (
                  <Button className="w-full rounded-[1.5rem] h-14 font-black text-lg shadow-2xl shadow-primary/40 bg-primary hover:scale-[1.01] transition-transform active:scale-[0.98]" onClick={() => { updateStatus(selectedAppointment.id, "in_progress"); setIsDetailsOpen(false); }}>
                    INICIAR SERVIÇO AGORA
                  </Button>
                )}
                {selectedAppointment.status === "in_progress" && (
                  <Button className="w-full bg-emerald-500 hover:bg-emerald-600 text-white rounded-[1.5rem] h-14 font-black text-lg shadow-2xl shadow-emerald-400/20 hover:scale-[1.01] transition-transform active:scale-[0.98]" onClick={() => { handleFinishWithSale(selectedAppointment); setIsDetailsOpen(false); }}>
                    FINALIZAR ATENDIMENTO
                  </Button>
                )}
                
                {["scheduled", "in_progress"].includes(selectedAppointment.status) ? (
                  <div className="grid grid-cols-2 gap-4">
                    <Button variant="ghost" className="text-destructive font-black uppercase text-[10px] tracking-widest hover:bg-destructive/10 rounded-[1.25rem] h-12" onClick={() => { updateStatus(selectedAppointment.id, "cancelled"); setIsDetailsOpen(false); }}>
                      CANCELAR
                    </Button>
                    <Button variant="outline" className="rounded-[1.25rem] h-12 font-black uppercase text-[10px] tracking-widest border-2" onClick={() => setIsDetailsOpen(false)}>
                      RETORNAR
                    </Button>
                  </div>
                ) : (
                   <Button variant="outline" className="w-full rounded-[1.5rem] h-14 font-black uppercase text-xs tracking-widest border-2" onClick={() => setIsDetailsOpen(false)}>
                     FECHAR PAINEL
                   </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      <POSModal 
        open={isPOSOpen} 
        onOpenChange={(open) => {
          setIsPOSOpen(open);
          if (!open) loadAppointments(); // Recarrega agenda ao fechar PDV
        }} 
        initialData={posInitialData}
      />
    </div>
  );
};

export default Services;
