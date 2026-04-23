import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { 
  PawPrint, 
  Calendar, 
  Syringe, 
  ClipboardList, 
  ArrowLeft, 
  Plus, 
  History, 
  CheckCircle2,
  Clock,
  ExternalLink,
  ChevronRight,
  Stethoscope,
  Mic,
  Loader2,
  Sparkles
} from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";

interface Vaccine {
  id: string;
  vaccine: string;
  applied_at: string;
  next_dose?: string;
  notes?: string;
}

interface PetNote {
  id: string;
  note: string;
  created_at: string;
}

interface Appointment {
  id: string;
  date: string;
  service: string;
  status: string;
}

interface HistoryData {
  agendamentos: Appointment[];
  notes: PetNote[];
  prontuarios: any[];
}

const PetProfile = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [pet, setPet] = useState<any>(null);
  const [vaccines, setVaccines] = useState<Vaccine[]>([]);
  const [history, setHistory] = useState<HistoryData>({ agendamentos: [], notes: [], prontuarios: [] });
  const [loading, setLoading] = useState(true);

  // Form states
  const [vaxName, setVaxName] = useState("");
  const [vaxDate, setVaxDate] = useState(new Date().toISOString().split("T")[0]);
  const [vaxNext, setVaxNext] = useState("");
  const [vaxNotes, setVaxNotes] = useState("");
  const [isVaxModalOpen, setIsVaxModalOpen] = useState(false);

  const [noteContent, setNoteContent] = useState("");
  const [isNoteModalOpen, setIsNoteModalOpen] = useState(false);

  const [isConsultModalOpen, setIsConsultModalOpen] = useState(false);
  const [newConsult, setNewConsult] = useState({
    anamnese: "",
    exame_fisico: "",
    suspeita_diagnostica: "",
    prescricao: "",
  });
  const [isScribing, setIsScribing] = useState(false);

  const handleAIScribe = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsScribing(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const { data } = await api.post("/ai/scribe", formData);
      setNewConsult({
        anamnese: data.anamnese,
        exame_fisico: data.exame_fisico,
        suspeita_diagnostica: data.suspeita_diagnostica,
        prescricao: data.prescricao,
      });
      toast.success("Consulta estruturada com sucesso pela IA!");
    } catch {
      toast.error("Erro ao processar áudio com IA.");
    } finally {
      setIsScribing(false);
    }
  };

  const loadAll = useCallback(async () => {
    try {
      const [pRes, vRes, hRes] = await Promise.all([
        api.get(`/pets/${id}`),
        api.get(`/pets/${id}/vaccines`),
        api.get(`/pets/${id}/history`)
      ]);
      setPet(pRes.data);
      setVaccines(vRes.data);
      setHistory(hRes.data);
    } catch (err) {
      toast.error("Erro ao carregar dados do pet.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleAddVaccine = async () => {
    if (!vaxName || !vaxDate) return;
    try {
      await api.post(`/pets/${id}/vaccines`, {
        vaccine: vaxName,
        applied_at: vaxDate,
        next_dose: vaxNext || null,
        notes: vaxNotes || null
      });
      toast.success("Vacina registrada!");
      setIsVaxModalOpen(false);
      loadAll();
      setVaxName("");
      setVaxNext("");
      setVaxNotes("");
    } catch {
      toast.error("Erro ao registrar vacina.");
    }
  };

  const handleAddNote = async () => {
    if (!noteContent) return;
    try {
      await api.post(`/pets/${id}/notes`, { note: noteContent });
      toast.success("Nota salva no histórico!");
      setIsNoteModalOpen(false);
      loadAll();
      setNoteContent("");
    } catch {
      toast.error("Erro ao salvar nota.");
    }
  };

  const handleAddConsultation = async () => {
    try {
      await api.post(`/pets/${id}/prontuarios`, newConsult);
      toast.success("Prontuário salvo!");
      setIsConsultModalOpen(false);
      setNewConsult({ anamnese: "", exame_fisico: "", suspeita_diagnostica: "", prescricao: "" });
      loadAll();
    } catch {
      toast.error("Erro ao salvar prontuário.");
    }
  };

  // Combine and sort total history
  const combinedHistory = useMemo(() => {
    const list = [
      ...history.agendamentos.map(a => ({ 
        type: "appointment", 
        date: a.date, 
        title: a.service?.replace("_", " ") || "Serviço",
        id: a.id,
        status: a.status
      })),
      ...history.notes.map(n => ({ 
        type: "note", 
        date: n.created_at, 
        title: "Nota Clínica",
        content: n.note,
        id: n.id
      })),
      ...history.prontuarios.map(p => ({
        type: "prontuario",
        date: p.created_at,
        title: "Consulta Clínica",
        content: p.prescricao,
        details: p,
        id: p.id
      }))
    ];
    return list.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [history]);

  if (loading) return (
    <div className="max-w-5xl mx-auto space-y-6 pt-10">
      <Skeleton className="h-40 w-full rounded-2xl" />
      <div className="grid grid-cols-3 gap-6">
        <Skeleton className="h-80 w-full rounded-2xl" />
        <Skeleton className="h-80 col-span-2 w-full rounded-2xl" />
      </div>
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" className="rounded-full h-10 w-10 bg-muted/50" onClick={() => navigate("/pets")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-3">
             <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
                <PawPrint className="h-8 w-8" />
             </div>
             <div>
                <h1 className="text-3xl font-heading font-black tracking-tight">{pet?.name}</h1>
                <div className="flex items-center gap-2 mt-0.5">
                  <Badge variant="secondary" className="font-bold">{pet?.species}</Badge>
                  <span className="text-sm text-muted-foreground">• {pet?.breed || "SRD"}</span>
                </div>
             </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
           <Dialog open={isVaxModalOpen} onOpenChange={setIsVaxModalOpen}>
            <DialogTrigger asChild>
              <Button className="rounded-full shadow-lg gap-2">
                <Syringe className="h-4 w-4" /> Registrar Vacina
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Syringe className="h-5 w-5 text-primary" /> Nova Vacina
                </DialogTitle>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Nome da Vacina</Label>
                  <Input id="name" value={vaxName} onChange={e => setVaxName(e.target.value)} placeholder="Ex: V10, Antirrábica..." />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="date">Aplicada em</Label>
                    <Input id="date" type="date" value={vaxDate} onChange={e => setVaxDate(e.target.value)} />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="next">Próxima Dose</Label>
                    <Input id="next" type="date" value={vaxNext} onChange={e => setVaxNext(e.target.value)} />
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="vax-notes">Observações</Label>
                  <Textarea id="vax-notes" value={vaxNotes} onChange={e => setVaxNotes(e.target.value)} placeholder="Lote, fabricante..." />
                </div>
              </div>
              <DialogFooter>
                <Button onClick={handleAddVaccine} className="w-full">Registrar Agora</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={isNoteModalOpen} onOpenChange={setIsNoteModalOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="rounded-full gap-2">
                <Plus className="h-4 w-4" /> Nota ao Histórico
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <ClipboardList className="h-5 w-5 text-primary" /> Novo Registro Clinico
                </DialogTitle>
              </DialogHeader>
              <div className="py-4 space-y-4">
                 <Textarea 
                    className="min-h-[150px] rounded-xl border-dashed"
                    placeholder="O que aconteceu no atendimento? Quais sintomas ou prescrições?"
                    value={noteContent}
                    onChange={e => setNoteContent(e.target.value)}
                 />
              </div>
              <DialogFooter>
                <Button onClick={handleAddNote} className="w-full">Salvar Histórico</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Left Column: Basic Info & Static stats */}
        <div className="md:col-span-4 space-y-6">
          <Card className="border-none shadow-xl rounded-3xl bg-gradient-to-b from-card to-muted/20">
            <CardHeader>
              <CardTitle className="text-lg font-bold">Resumo Geral</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="space-y-1">
                  <p className="text-[10px] text-muted-foreground uppercase font-black">Tutor / Responsável</p>
                  <p className="font-bold flex items-center justify-between">
                    {pet?.client_name || "Não informado"}
                    <ExternalLink className="h-3 w-3 text-muted-foreground mr-1" />
                  </p>
                </div>
                
                <div className="p-4 rounded-2xl bg-primary/5 border border-primary/10">
                   <p className="text-[10px] text-primary uppercase font-black mb-2">Próximas Vacinas</p>
                   {vaccines.filter(v => v.next_dose && new Date(v.next_dose) > new Date()).length === 0 ? (
                     <p className="text-sm text-muted-foreground">Tudo em dia!</p>
                   ) : (
                     <div className="space-y-2">
                        {vaccines.filter(v => v.next_dose && new Date(v.next_dose) > new Date()).map(v => (
                          <div key={v.id} className="flex justify-between items-center text-sm">
                            <span className="font-medium">{v.vaccine}</span>
                            <span className="text-xs font-bold bg-white px-2 py-0.5 rounded shadow-sm">
                              {format(new Date(v.next_dose!), "dd MMM", { locale: ptBR })}
                            </span>
                          </div>
                        ))}
                     </div>
                   )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                   <div className="p-4 rounded-2xl bg-secondary/30">
                      <p className="text-[10px] text-muted-foreground uppercase font-black mb-1">Visitas</p>
                      <p className="text-xl font-black">{history.agendamentos.length}</p>
                   </div>
                   <div className="p-4 rounded-2xl bg-secondary/30">
                      <p className="text-[10px] text-muted-foreground uppercase font-black mb-1">Vacinas</p>
                      <p className="text-xl font-black">{vaccines.length}</p>
                   </div>
                </div>

                <div className="space-y-1">
                  <p className="text-[10px] text-muted-foreground uppercase font-black">Alergias / Restrições</p>
                  <p className={`text-sm font-bold ${pet?.allergies ? 'text-destructive' : 'text-muted-foreground'}`}>
                    {pet?.allergies || "Nenhuma registrada."}
                  </p>
                </div>

                <div className="space-y-1">
                  <p className="text-[10px] text-muted-foreground uppercase font-black">Observações Médicas</p>
                  <p className="text-sm italic text-muted-foreground leading-relaxed">
                    {pet?.notes || "Nenhuma contraindicação ou observação especial registrada."}
                  </p>
                </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Detailed Cards */}
        <div className="md:col-span-8 space-y-6">
          {/* Vaccination Card - Aesthetic horizontal layout */}
          <Card className="border-none shadow-xl rounded-3xl overflow-hidden">
             <CardHeader className="bg-primary/5 pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Syringe className="h-5 w-5 text-primary" /> Carteirinha Digital de Vacinação
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              {vaccines.length === 0 ? (
                <div className="text-center py-12 border-2 border-dashed rounded-3xl border-muted">
                   <Syringe className="h-10 w-10 text-muted-foreground mx-auto mb-3 opacity-20" />
                   <p className="text-muted-foreground text-sm font-medium">Parece que ainda não há vacinas registradas.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {vaccines.map((v, idx) => (
                    <div key={v.id} className="p-4 rounded-2xl bg-card border hover:shadow-md transition-all group">
                       <div className="flex justify-between items-start mb-2">
                          <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                            <CheckCircle2 className="h-5 w-5" />
                          </div>
                          <Badge variant="outline" className="text-[10px] uppercase font-black">
                            {format(new Date(v.applied_at), "dd/MM/yyyy")}
                          </Badge>
                       </div>
                       <p className="font-bold text-lg leading-tight uppercase tracking-tight">{v.vaccine}</p>
                       <div className="mt-4 flex flex-col gap-1">
                          {v.next_dose && (
                            <div className="flex items-center gap-2 text-xs font-bold text-amber-600 bg-amber-50 p-2 rounded-xl">
                               <Clock className="h-3.5 w-3.5" />
                               Próximo Reforço: {format(new Date(v.next_dose), "dd/MM/yy")}
                            </div>
                          )}
                          {v.notes && (
                             <p className="text-[10px] text-muted-foreground mt-2 line-clamp-2">{v.notes}</p>
                          )}
                       </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Timeline of everything */}
          <Card className="border-none shadow-xl rounded-3xl">
             <CardHeader>
              <CardTitle className="text-lg flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                  <History className="h-5 w-5 text-primary" /> Jornada de Atendimentos
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => setIsNoteModalOpen(true)} className="rounded-xl h-8 text-[10px] uppercase font-black">
                     + Nota
                  </Button>
                  <Button size="sm" onClick={() => setIsConsultModalOpen(true)} className="rounded-xl h-8 text-[10px] uppercase font-black bg-primary">
                     + Consulta
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
               {combinedHistory.length === 0 ? (
                 <div className="text-center py-10 opacity-40">
                    <ClipboardList className="h-10 w-10 mx-auto mb-2" />
                    <p className="text-sm font-medium">Nenhum evento registrado no histórico.</p>
                 </div>
               ) : (
                 <div className="relative pl-6 space-y-8 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-[2px] before:bg-muted">
                    {combinedHistory.map((evt, idx) => (
                      <div key={evt.id} className="relative group animate-slide-up" style={{ animationDelay: `${idx * 0.1}s` }}>
                        {/* Dot */}
                        <div className={`absolute -left-[19px] top-1.5 h-4 w-4 rounded-full border-2 bg-background z-10 ${
                          evt.type === "note" ? "border-emerald-500" : "border-primary"
                        }`} />
                        
                        <div className="space-y-1">
                           <div className="flex items-center justify-between">
                              <span className="text-[10px] font-black text-muted-foreground uppercase opacity-70">
                                {format(new Date(evt.date), "dd MMMM, yyyy", { locale: ptBR })}
                              </span>
                              {evt.type === "appointment" && (
                                <Badge variant="outline" className="text-[9px] uppercase font-black py-0 px-1 border-primary/30 text-primary">
                                  {evt.status === "done" ? "Concluído" : evt.status}
                                </Badge>
                              )}
                           </div>
                           <h4 className="font-bold flex items-center gap-2">
                             {evt.type === "note" ? <ClipboardList className="h-3.5 w-3.5 text-emerald-500" /> : <Calendar className="h-3.5 w-3.5 text-primary" />}
                             {evt.title}
                           </h4>
                           {evt.type === "note" && (
                             <div className="mt-2 p-3 rounded-2xl bg-muted/30 border border-muted/50 text-sm leading-relaxed text-muted-foreground">
                               {evt.content}
                             </div>
                           )}
                           {evt.type === "appointment" && (
                             <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                                <span className="hover:text-primary cursor-pointer flex items-center gap-1 group/btn">
                                  Ver Detalhes do Agendamento <ChevronRight className="h-3 w-3 transition-transform group-hover/btn:translate-x-0.5" />
                                </span>
                             </div>
                           )}
                        </div>
                      </div>
                    ))}
                 </div>
               )}
            </CardContent>
          </Card>
        </div>
      </div>
      {/* Nova Consulta Modal */}
      <Dialog open={isConsultModalOpen} onOpenChange={setIsConsultModalOpen}>
        <DialogContent className="sm:max-w-[600px] rounded-[2rem]">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <DialogTitle className="flex items-center gap-2">
                <Stethoscope className="h-5 w-5 text-primary" /> Novo Registro Clínico
              </DialogTitle>
              
              <div className="relative">
                <Input 
                  type="file" 
                  accept="audio/*" 
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
                  onChange={handleAIScribe}
                  disabled={isScribing}
                />
                <Button variant="outline" size="sm" className="rounded-full gap-2 border-primary/30 hover:bg-primary/5">
                  {isScribing ? <Loader2 className="h-3 w-3 animate-spin" /> : <Mic className="h-3 w-3 text-primary" />}
                  <span className="text-[10px] font-bold uppercase">{isScribing ? 'Processando...' : 'AI Scribe'}</span>
                </Button>
              </div>
            </div>
          </DialogHeader>
          
          {isScribing && (
            <div className="flex flex-col items-center justify-center py-8 space-y-3 animate-pulse">
               <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <Sparkles className="h-6 w-6 text-primary animate-bounce" />
               </div>
               <p className="text-xs font-medium text-muted-foreground">A IA está ouvindo e estruturando sua consulta...</p>
            </div>
          )}

          <div className={`grid gap-4 py-4 transition-all ${isScribing ? 'opacity-20 pointer-events-none' : 'opacity-100'}`}>
            <div className="space-y-2">
              <Label>Anamnese / Histórico</Label>
              <Textarea 
                value={newConsult.anamnese} 
                onChange={e => setNewConsult({...newConsult, anamnese: e.target.value})} 
                placeholder="Motivo da consulta, sintomas, duração..."
              />
            </div>
            <div className="space-y-2">
              <Label>Exame Físico</Label>
              <Textarea 
                value={newConsult.exame_fisico} 
                onChange={e => setNewConsult({...newConsult, exame_fisico: e.target.value})} 
                placeholder="Temperatura, frequência cardíaca, observações físicas..."
              />
            </div>
            <div className="space-y-2">
              <Label>Suspeita Diagnóstica</Label>
              <Input 
                value={newConsult.suspeita_diagnostica} 
                onChange={e => setNewConsult({...newConsult, suspeita_diagnostica: e.target.value})} 
              />
            </div>
            <div className="space-y-2">
              <Label>Prescrição / Tratamento</Label>
              <Textarea 
                value={newConsult.prescricao} 
                onChange={e => setNewConsult({...newConsult, prescricao: e.target.value})} 
                placeholder="Medicamentos, dosagens, recomendações..."
              />
            </div>
          </div>
          <Button onClick={handleAddConsultation} className="w-full">Salvar Prontuário</Button>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PetProfile;
