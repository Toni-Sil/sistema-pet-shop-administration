import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Hotel as HotelIcon, 
  Moon, 
  Sun, 
  PawPrint, 
  Clock, 
  CheckCircle2, 
  Plus, 
  LogIn, 
  LogOut,
  ChevronRight,
  AlertCircle,
  Edit2
} from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface Quarto {
  id: string;
  name: string;
  tipo: string;
  status: "available" | "occupied" | "cleaning" | "maintenance";
  preco_diaria: number;
  capacidade: number;
}

interface Hospedagem {
  id: string;
  pet_id: string;
  quarto_id: string;
  status: "planned" | "checked_in" | "checked_out" | "cancelled";
  check_in_previsto: string;
  check_out_previsto: string;
  check_in_real?: string;
  check_out_real?: string;
  valor_total: number;
  pet?: any;
}

const statusColors = {
  available: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  occupied: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  cleaning: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  maintenance: "bg-destructive/10 text-destructive border-destructive/20",
};

const statusLabels = {
  available: "Disponível",
  occupied: "Ocupado",
  cleaning: "Em Limpeza",
  maintenance: "Manutenção",
};

const Hotel = () => {
  const [quartos, setQuartos] = useState<Quarto[]>([]);
  const [hospedagens, setHospedagens] = useState<Hospedagem[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Modals
  const [isNewHospOpen, setIsNewHospOpen] = useState(false);
  const [isNewQuartoOpen, setIsNewQuartoOpen] = useState(false);
  const [editHospId, setEditHospId] = useState<string | null>(null);
  
  // Forms
  const [newQuarto, setNewQuarto] = useState({ name: "", tipo: "Padrão", preco_diaria: 60, capacidade: 1 });
  const [newHosp, setNewHosp] = useState({ 
    pet_id: "", 
    quarto_id: "", 
    check_in_previsto: "", 
    check_out_previsto: "",
    alimentacao: "",
    medicamentos: "",
    observacoes: "" 
  });

  const loadData = async () => {
    try {
      const [qRes, hRes] = await Promise.all([
        api.get("/hotel/quartos"),
        api.get("/hotel/hospedagens")
      ]);
      setQuartos(qRes.data);
      setHospedagens(hRes.data);
    } catch {
      toast.error("Erro ao carregar dados do hotel.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleCreateQuarto = async () => {
    try {
      await api.post("/hotel/quartos", newQuarto);
      toast.success("Vaga/Quarto criado!");
      setIsNewQuartoOpen(false);
      loadData();
    } catch {
      toast.error("Erro ao criar quarto.");
    }
  };

  const handleCheckIn = async (id: string) => {
    try {
      await api.post(`/hotel/hospedagens/${id}/check-in`);
      toast.success("Check-in realizado!");
      loadData();
    } catch {
      toast.error("Erro no check-in.");
    }
  };

  const handleCheckOut = async (id: string) => {
    try {
      await api.post(`/hotel/hospedagens/${id}/check-out`);
      toast.success("Check-out realizado!");
      loadData();
    } catch {
      toast.error("Erro no check-out.");
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in pb-16">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 px-2">
        <div className="space-y-1">
          <Badge className="bg-primary/10 text-primary border-none px-3 mb-2 font-black uppercase tracking-[0.2em] text-[10px]">Módulo de Hospedagem</Badge>
          <h1 className="text-4xl font-black tracking-tighter">Hotel & Creche</h1>
          <p className="text-muted-foreground font-medium italic">Gestão de estadias, ocupação e bem-estar animal.</p>
        </div>
        <div className="flex gap-4">
          <Button variant="outline" onClick={() => setIsNewQuartoOpen(true)} className="rounded-2xl h-11 font-black border-2 border-primary/20 hover:bg-primary/5 transition-all">
             CONFIGURAR VAGAS
          </Button>
          <Button onClick={() => {
             setEditHospId(null);
             setNewHosp({ pet_id: "", quarto_id: "", check_in_previsto: "", check_out_previsto: "", alimentacao: "", medicamentos: "", observacoes: "" });
             setIsNewHospOpen(true);
          }} className="h-11 px-6 rounded-2xl font-black shadow-xl shadow-primary/20 hover:scale-[1.02] transition-all bg-primary text-white">
            <Plus className="h-5 w-5 mr-2" /> NOVA HOSPEDAGEM
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Room Grid (65%) */}
        <div className="lg:col-span-8 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-48 rounded-[2rem]" />)
            ) : quartos.length === 0 ? (
              <Card className="col-span-full py-20 bg-muted/10 border-dashed rounded-[2.5rem] flex flex-col items-center justify-center">
                 <HotelIcon className="h-16 w-16 text-muted-foreground/20 mb-4" />
                 <p className="text-muted-foreground font-bold">Nenhum quarto ou canil configurado.</p>
                 <Button variant="link" onClick={() => setIsNewQuartoOpen(true)}>Comece configurando suas vagas aqui.</Button>
              </Card>
            ) : (
              quartos.map(quarto => (
                <Card key={quarto.id} className={`group border-none shadow-xl rounded-[2rem] overflow-hidden transition-all hover:translate-y-[-4px] ${quarto.status === 'occupied' ? 'bg-amber-500/5 ring-1 ring-amber-500/20' : 'bg-card/40 backdrop-blur-xl ring-1 ring-white/10'}`}>
                   <CardHeader className="pb-2">
                     <div className="flex justify-between items-start">
                        <div className={`p-2 rounded-xl ${statusColors[quarto.status]} border transition-colors`}>
                           <HotelIcon className="h-5 w-5" />
                        </div>
                        <Badge variant="outline" className={`font-black uppercase text-[9px] tracking-tighter ${statusColors[quarto.status]}`}>
                           {statusLabels[quarto.status]}
                        </Badge>
                     </div>
                     <CardTitle className="text-xl font-black tracking-tight mt-3">{quarto.name}</CardTitle>
                     <CardDescription className="text-[10px] uppercase font-black tracking-widest">{quarto.tipo}</CardDescription>
                   </CardHeader>
                   <CardContent className="pt-4 space-y-4">
                      <div className="flex justify-between items-center bg-white/5 p-3 rounded-2xl">
                         <div className="flex flex-col">
                            <span className="text-[10px] text-muted-foreground font-black uppercase">Diária</span>
                            <span className="text-lg font-black text-primary">R$ {Number(quarto.preco_diaria).toFixed(2)}</span>
                         </div>
                         <div className="h-10 w-10 rounded-full border border-primary/20 flex items-center justify-center bg-primary/5">
                            <span className="text-xs font-black text-primary">{quarto.capacidade}</span>
                         </div>
                      </div>
                   </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Active Stays (35%) */}
        <div className="lg:col-span-4 space-y-6">
          <Card className="glass-card shadow-2xl border-none rounded-[2.5rem] bg-card/60 backdrop-blur-xl overflow-hidden ring-1 ring-white/10 h-full">
            <CardHeader className="bg-primary/5 border-b border-white/5 py-8">
              <CardTitle className="text-xl font-black flex items-center gap-3">
                 <div className="p-2.5 rounded-2xl bg-primary shadow-lg shadow-primary/20 text-white">
                    <Clock className="h-5 w-5" />
                 </div>
                 Fluxo de Hospedagem
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
               <div className="space-y-4">
                  {hospedagens.filter(h => h.status !== 'checked_out' && h.status !== 'cancelled').length === 0 ? (
                    <div className="text-center py-20 opacity-30">
                       <AlertCircle className="h-12 w-12 mx-auto mb-3" />
                       <p className="text-sm font-bold uppercase tracking-widest">Nenhuma estadia ativa</p>
                    </div>
                  ) : (
                    hospedagens.filter(h => h.status !== 'checked_out' && h.status !== 'cancelled').map(h => (
                      <div key={h.id} className="p-5 rounded-3xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all group relative overflow-hidden">
                         <div className="absolute top-2 right-2 p-1 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-20">
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-primary/70 hover:text-primary hover:bg-primary/10" onClick={(e) => { 
                               e.stopPropagation();
                               setEditHospId(h.id);
                               setNewHosp({
                                  pet_id: h.pet_id,
                                  quarto_id: h.quarto_id,
                                  check_in_previsto: h.check_in_previsto ? new Date(h.check_in_previsto).toISOString().slice(0, 16) : "",
                                  check_out_previsto: h.check_out_previsto ? new Date(h.check_out_previsto).toISOString().slice(0, 16) : "",
                                  alimentacao: (h as any).alimentacao || "",
                                  medicamentos: (h as any).medicamentos || "",
                                  observacoes: (h as any).observacoes || ""
                               });
                               setIsNewHospOpen(true);
                            }}>
                              <Edit2 className="h-4 w-4" />
                            </Button>
                         </div>
                         <div className="flex items-center gap-4 relative z-10">
                            <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center text-primary font-black text-xl">
                               <PawPrint className="h-8 w-8" />
                            </div>
                            <div className="flex-1">
                               <h4 className="font-black text-lg tracking-tight truncate leading-none mb-1">{h.pet?.name || `Hospedagem #${h.id.slice(0,4)}`}</h4>
                               <p className="text-[10px] font-black uppercase text-muted-foreground flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {format(new Date(h.check_in_previsto), "dd MMM")} → {format(new Date(h.check_out_previsto), "dd MMM")}
                               </p>
                            </div>
                         </div>
                         
                         {(h.alimentacao || h.medicamentos || h.observacoes) && (
                            <div className="mt-4 p-3 bg-white/5 rounded-xl border border-white/5 space-y-1">
                               <p className="text-[9px] font-black uppercase tracking-widest text-primary mb-1">Cuidados Especiais</p>
                               {h.alimentacao && <p className="text-xs text-muted-foreground"><strong className="text-foreground font-bold">Alimentação:</strong> {h.alimentacao}</p>}
                               {h.medicamentos && <p className="text-xs text-muted-foreground"><strong className="text-foreground font-bold">Medicamentos:</strong> {h.medicamentos}</p>}
                               {h.observacoes && <p className="text-xs text-muted-foreground"><strong className="text-foreground font-bold">Obs:</strong> {h.observacoes}</p>}
                            </div>
                          )}

                         <div className="mt-4 flex items-center justify-between pt-4 border-t border-white/5">
                            {h.status === 'planned' ? (
                              <Button size="sm" onClick={() => handleCheckIn(h.id)} className="w-full rounded-xl h-10 font-black bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-500/20">
                                 REALIZAR CHECK-IN
                              </Button>
                            ) : (
                              <Button size="sm" onClick={() => handleCheckOut(h.id)} className="w-full rounded-xl h-10 font-black bg-amber-500 hover:bg-amber-600 text-white shadow-lg shadow-amber-500/20">
                                 REALIZAR CHECK-OUT
                              </Button>
                            )}
                         </div>
                      </div>
                    ))
                  )}
               </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Modal: Novo Quarto */}
      <Dialog open={isNewQuartoOpen} onOpenChange={setIsNewQuartoOpen}>
        <DialogContent className="sm:max-w-[450px] rounded-[2.5rem]">
          <DialogHeader>
            <DialogTitle className="text-2xl font-black tracking-tight flex items-center gap-2">
               <HotelIcon className="h-6 w-6 text-primary" /> Configurar Nova Vaga
            </DialogTitle>
          </DialogHeader>
          <div className="grid gap-6 py-6">
            <div className="space-y-2">
              <Label className="font-bold">Nome da Vaga / Quarto</Label>
              <Input value={newQuarto.name} onChange={e => setNewQuarto({...newQuarto, name: e.target.value})} placeholder="Ex: Suíte Pet 01" className="rounded-xl" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="font-bold">Preço Diária (R$)</Label>
                <Input type="number" value={newQuarto.preco_diaria} onChange={e => setNewQuarto({...newQuarto, preco_diaria: parseFloat(e.target.value)})} className="rounded-xl" />
              </div>
              <div className="space-y-2">
                <Label className="font-bold">Capacidade (Pets)</Label>
                <Input type="number" value={newQuarto.capacidade} onChange={e => setNewQuarto({...newQuarto, capacidade: parseInt(e.target.value)})} className="rounded-xl" />
              </div>
            </div>
          </div>
          <Button onClick={handleCreateQuarto} className="w-full h-12 rounded-xl font-black text-lg shadow-xl shadow-primary/20">SALVAR CONFIGURAÇÃO</Button>
        </DialogContent>
      </Dialog>

      {/* Modal: Nova/Editar Hospedagem */}
      <Dialog open={isNewHospOpen} onOpenChange={setIsNewHospOpen}>
        <DialogContent className="sm:max-w-[500px] rounded-[2.5rem] max-h-[90vh] overflow-y-auto custom-scrollbar">
          <DialogHeader>
            <DialogTitle className="text-2xl font-black tracking-tight">{editHospId ? "Editar Hospedagem" : "Agendar Estadia"}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-6 py-6">
            {!editHospId && (
              <>
                <div className="space-y-2">
                  <Label className="font-bold">ID do Quarto (Manual por enquanto)</Label>
                  <Input value={newHosp.quarto_id} onChange={e => setNewHosp({...newHosp, quarto_id: e.target.value})} placeholder="UUID do quarto" />
                </div>
                <div className="space-y-2">
                  <Label className="font-bold">ID do Pet (Manual por enquanto)</Label>
                  <Input value={newHosp.pet_id} onChange={e => setNewHosp({...newHosp, pet_id: e.target.value})} placeholder="UUID do pet" />
                </div>
              </>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="font-bold">Check-in Previsto</Label>
                <Input type="datetime-local" value={newHosp.check_in_previsto} onChange={e => setNewHosp({...newHosp, check_in_previsto: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label className="font-bold">Check-out Previsto</Label>
                <Input type="datetime-local" value={newHosp.check_out_previsto} onChange={e => setNewHosp({...newHosp, check_out_previsto: e.target.value})} />
              </div>
            </div>
            <div className="space-y-2">
              <Label className="font-bold">Alimentação</Label>
              <Input placeholder="Ex: Ração Premier 2x ao dia" value={newHosp.alimentacao} onChange={e => setNewHosp({...newHosp, alimentacao: e.target.value})} />
            </div>
            <div className="space-y-2">
              <Label className="font-bold">Medicamentos</Label>
              <Input placeholder="Ex: Nexgard dia 10" value={newHosp.medicamentos} onChange={e => setNewHosp({...newHosp, medicamentos: e.target.value})} />
            </div>
            <div className="space-y-2">
              <Label className="font-bold">Observações</Label>
              <Textarea rows={2} placeholder="Ex: Não gosta de outros cães, medroso com barulho..." value={newHosp.observacoes} onChange={e => setNewHosp({...newHosp, observacoes: e.target.value})} />
            </div>
          </div>
          <Button onClick={async () => {
             try {
               const payload = { ...newHosp };
               if (editHospId) {
                  delete (payload as any).pet_id; // pet can't be changed usually, but just in case
                  await api.patch(`/hotel/hospedagens/${editHospId}`, payload);
                  toast.success("Hospedagem atualizada!");
               } else {
                  await api.post("/hotel/hospedagens", payload);
                  toast.success("Hospedagem agendada!");
               }
               setIsNewHospOpen(false);
               loadData();
             } catch (err: any) { 
               toast.error(err.response?.data?.detail || "Erro ao salvar."); 
             }
          }} className="w-full h-12 rounded-xl font-black text-lg">{editHospId ? "SALVAR ALTERAÇÕES" : "CONFIRMAR RESERVA"}</Button>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Hotel;
