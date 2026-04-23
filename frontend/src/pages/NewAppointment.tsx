import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, ArrowRight, Check, Search } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { PawPrint, Truck, Package, Calendar } from "lucide-react";

// Dynamic steps logic is implemented inside the component

const APPOINTMENT_TYPES = [
  { id: "servico", name: "Serviço Pet", description: "Banho, tosa, consulta, etc.", icon: "PawPrint" },
  { id: "entrega", name: "Entrega de Material", description: "Recebimento de fornecedores.", icon: "Truck" },
  { id: "recebimento", name: "Recebimento de Mercadoria", description: "Entrada de estoque.", icon: "Package" },
  { id: "outros", name: "Outro Agendamento", description: "Reuniões, manutenção, etc.", icon: "Calendar" },
];

const SERVICES = [
  { key: "banho", label: "Banho" },
  { key: "tosa", label: "Tosa" },
  { key: "banho_tosa", label: "Banho + Tosa" },
  { key: "higienica", label: "Tosa higiênica" },
  { key: "consulta", label: "Consulta veterinária" },
  { key: "hotel", label: "Hotel" },
];

const PROFESSIONALS = ["Ana (Groomer)", "Carlos (Groomer)", "Dra. Joana (Vet)"];

const TIMES = [
  "08:00","08:30","09:00","09:30","10:00","10:30",
  "11:00","13:00","13:30","14:00","14:30","15:00","15:30","16:00",
];

interface Pet { id: string; name: string; species: string; breed?: string; }
interface Client { id: string; name: string; phone: string; pets: Pet[]; }

const NewAppointment = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);

  // Step 0: Type
  const [appointmentType, setAppointmentType] = useState(searchParams.get("type") || "servico");

  // Dynamic Stepper Configuration
  const getSteps = () => {
    switch (appointmentType) {
      case "servico":
        return ["Pedido", "Tutor e Pet", "Serviço", "Data e Horário"];
      case "entrega":
        return ["Pedido", "Material", "Detalhes da Entrega", "Data e Horário"];
      case "recebimento":
        return ["Pedido", "Mercadoria", "Detalhes do Recebimento", "Data e Horário"];
      default:
        return ["Pedido", "Motivo / Razão", "Observações", "Data e Horário"];
    }
  };
  const steps = getSteps();

  // Step 1: Pet/Tutor (only for servico)
  const [clientSearch, setClientSearch] = useState("");
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [selectedPet, setSelectedPet] = useState<Pet | null>(null);
  
  // Step 1 variation: Delivery/Other Details
  const [productSearch, setProductSearch] = useState("");
  const [products, setProducts] = useState<any[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [otherDescription, setOtherDescription] = useState("");

  // Step 2: Service
  const [dbServices, setDbServices] = useState<any[]>([]);
  const [selectedServiceId, setSelectedServiceId] = useState("");
  const [selectedServiceLabel, setSelectedServiceLabel] = useState("");
  const [selectedProf, setSelectedProf] = useState("");
  const [notes, setNotes] = useState("");

  // Step 3: Date/Time
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [selectedTime, setSelectedTime] = useState("");
  const [estimatedDuration, setEstimatedDuration] = useState<number | null>(null);

  // Search clientes with debounce
  useEffect(() => {
    const delay = setTimeout(async () => {
      if (clientSearch.length < 1) { setClients([]); return; }
      try {
        const { data } = await api.get(`/clientes?search=${clientSearch}&limit=10`);
        setClients(data);
      } catch { /* silently */ }
    }, 300);
    return () => clearTimeout(delay);
  }, [clientSearch]);

  // Search produtos with debounce (or load initial list)
  useEffect(() => {
    const delay = setTimeout(async () => {
      if (step !== 1 || appointmentType === "servico") return;
      try {
        const url = productSearch.length >= 1 ? `/produtos?search=${productSearch}&limit=10` : `/produtos?limit=10`;
        const { data } = await api.get(url);
        setProducts(data);
      } catch { /* silently */ }
    }, 300);
    return () => clearTimeout(delay);
  }, [productSearch, step, appointmentType]);

  // Load services once
  useEffect(() => {
    const loadServices = async () => {
      try {
        const { data } = await api.get("/services");
        setDbServices(data);
      } catch { /* silently */ }
    };
    loadServices();
  }, []);

  // Handle initial pet search from params
  useEffect(() => {
    const petParam = searchParams.get("pet");
    if (petParam && appointmentType === "servico") {
      setClientSearch(petParam);
      setStep(1);
    }
    const typeParam = searchParams.get("type");
    if (typeParam) {
      setStep(1);
    }
  }, [searchParams, appointmentType]);

  // Fetch duration estimate when pet and service are selected
  useEffect(() => {
    const getEstimate = async () => {
      if (appointmentType === "servico" && selectedPet && selectedServiceLabel) {
        try {
          const { data } = await api.get("/agendamentos/estimate-duration", {
            params: { pet_id: selectedPet.id, service_type: selectedServiceLabel }
          });
          setEstimatedDuration(data.minutes);
        } catch { /* ignore */ }
      } else {
        setEstimatedDuration(null);
      }
    };
    getEstimate();
  }, [selectedPet, selectedServiceLabel, appointmentType]);

  const canAdvance = () => {
    if (step === 0) return !!appointmentType;
    if (step === 1) {
      if (appointmentType === "servico") return !!selectedPet;
      if (["entrega", "recebimento"].includes(appointmentType)) return !!selectedProduct || otherDescription.length > 2;
      return otherDescription.length > 2;
    }
    if (step === 2) {
      if (appointmentType === "servico") return !!selectedServiceId;
      return true; // Step 2 is notes for non-servico
    }
    if (step === 3) return !!date && !!selectedTime;
    return false;
  };

  const handleConfirm = async () => {
    if (appointmentType === "servico" && !selectedPet) return;
    setSaving(true);
    try {
      const payload = {
        pet_id: appointmentType === "servico" ? selectedPet?.id : undefined,
        service_id: appointmentType === "servico" ? selectedServiceId : undefined,
        service: appointmentType === "servico" ? selectedServiceLabel : APPOINTMENT_TYPES.find(t => t.id === appointmentType)?.name,
        date,
        time: selectedTime,
        professional: selectedProf || undefined,
        notes: appointmentType !== "servico" 
          ? `${selectedProduct ? `Objeto: ${selectedProduct.name}\n` : ""}${otherDescription}\n${notes}` 
          : notes || undefined,
      };
      await api.post("/agendamentos", payload);
      toast.success(`Agendamento confirmado!`);
      navigate("/servicos");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erro ao criar agendamento.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div>
        <Button variant="ghost" size="sm" className="-ml-2 mb-2" onClick={() => navigate("/servicos")}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Voltar para Agenda
        </Button>
        <h1 className="text-2xl font-heading font-bold">Novo agendamento</h1>
        <p className="text-muted-foreground mt-1">Preencha em 3 passos simples.</p>
      </div>

      {/* Stepper */}
      <div className="flex items-center gap-2 mb-8 bg-card/40 p-4 rounded-2xl border">
        {steps.map((s, i) => (
          <div key={s} className="flex items-center gap-2 flex-1">
            <div className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 transition-all ${
              i < step ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20" : i === step ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-110" : "bg-muted text-muted-foreground"
            }`}>
              {i < step ? <Check className="h-4 w-4" /> : i + 1}
            </div>
            <span className={`text-sm hidden sm:block transition-colors ${i === step ? "font-bold text-primary" : "text-muted-foreground font-medium"}`}>{s}</span>
            {i < steps.length - 1 && <div className={`flex-1 h-1 rounded-full transition-colors ${i < step ? "bg-emerald-500/50" : "bg-border"}`} />}
          </div>
        ))}
      </div>

      <Card>
        <CardContent className="pt-6">

          {/* ── Step 0: Tipo de Pedido ─────────────────────── */}
          {step === 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {APPOINTMENT_TYPES.map(type => {
                const icons = { PawPrint, Truck, Package, Calendar };
                const Icon = icons[type.icon as keyof typeof icons] || Calendar;
                return (
                  <button
                    key={type.id}
                    onClick={() => { setAppointmentType(type.id); setStep(1); }}
                    className={`flex items-start gap-4 p-4 rounded-xl border text-left transition-all hover:bg-muted/30 ${
                      appointmentType === type.id ? "border-primary bg-primary/5" : ""
                    }`}
                  >
                    <div className="p-2 rounded-lg bg-primary/10 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="font-bold text-sm">{type.name}</p>
                      <p className="text-xs text-muted-foreground">{type.description}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* ── Step 1: Razão / Objeto / Pet ───────────────── */}
          {step === 1 && (
            <div className="space-y-4">
              {appointmentType === "servico" ? (
                <>
                  <div className="space-y-2">
                    <Label>Buscar cliente</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Nome ou telefone do tutor..."
                        className="pl-9"
                        value={clientSearch}
                        onChange={e => { setClientSearch(e.target.value); setSelectedClient(null); setSelectedPet(null); }}
                      />
                    </div>
                  </div>

                  {clients.length > 0 && !selectedClient && (
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {clients.map(c => (
                        <button
                          key={c.id}
                          onClick={() => { setSelectedClient(c); setClientSearch(c.name); }}
                          className="w-full text-left p-3 rounded-lg border hover:bg-muted/30 transition-colors"
                        >
                          <p className="font-medium">{c.name}</p>
                          <p className="text-sm text-muted-foreground">{c.phone} · {c.pets.length} pet(s)</p>
                        </button>
                      ))}
                    </div>
                  )}

                  {selectedClient && (
                    <div className="space-y-2">
                      <Label>Selecione o pet</Label>
                      {selectedClient.pets.length === 0 ? (
                        <p className="text-sm text-muted-foreground p-3 rounded border border-dashed">
                          Este cliente não tem pets cadastrados.
                        </p>
                      ) : (
                        <div className="grid grid-cols-2 gap-2">
                          {selectedClient.pets.map(p => (
                            <button
                              key={p.id}
                              onClick={() => setSelectedPet(p)}
                              className={`p-3 rounded-lg border text-left text-sm transition-colors ${
                                selectedPet?.id === p.id ? "border-primary bg-primary/5 font-medium" : "hover:bg-muted/30"
                              }`}
                            >
                              <p className="font-medium">{p.name}</p>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {selectedPet && (
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-sm">
                      <Check className="h-4 w-4 text-emerald-600 flex-shrink-0" />
                      <span><strong>{selectedPet.name}</strong> de <strong>{selectedClient?.name}</strong> selecionado.</span>
                    </div>
                  )}
                </>
              ) : (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>{appointmentType === "entrega" ? "Buscar Material" : appointmentType === "recebimento" ? "Buscar Mercadoria" : "Razão do Agendamento (ou Buscar Fornecedor)"}</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder={appointmentType === "entrega" ? "Nome do material..." : appointmentType === "recebimento" ? "Nome do produto/mercadoria..." : "Digite o motivo ou busque... "}
                        className="pl-9"
                        value={productSearch}
                        onChange={e => { setProductSearch(e.target.value); setSelectedProduct(null); }}
                      />
                    </div>
                  </div>

                  {products.length > 0 && !selectedProduct && (
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {products.map(p => (
                        <button
                          key={p.id}
                          onClick={() => { setSelectedProduct(p); setProductSearch(p.name); }}
                          className="w-full text-left p-3 rounded-lg border hover:bg-muted/30 transition-colors"
                        >
                          <div className="flex justify-between items-center">
                            <div>
                              <p className="font-medium">{p.name}</p>
                              <p className="text-xs text-muted-foreground">{p.category} · Estoque: {p.quantity || p.weight_in_stock || 0}</p>
                            </div>
                            <Badge variant="outline" className="text-[10px]">{p.sku || "S/ SKU"}</Badge>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}

                  {selectedProduct && (
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-primary/5 border border-primary/20 text-sm">
                      <Check className="h-4 w-4 text-primary flex-shrink-0" />
                      <span><strong>{selectedProduct.name}</strong> selecionado.</span>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label>Detalhes Adicionais *</Label>
                    <Input 
                      placeholder="Ex: Entrega prevista para o período da tarde"
                      value={otherDescription}
                      onChange={e => setOtherDescription(e.target.value)}
                    />
                    <p className="text-[10px] text-muted-foreground">Informe os detalhes completos deste pedido.</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Step 2: Detalhes / Serviço ──────────────────────── */}
          {step === 2 && (
            <div className="space-y-5">
              {appointmentType === "servico" ? (
                <>
                  <div className="space-y-2">
                    <Label>Serviço *</Label>
                    <div className="grid grid-cols-2 gap-2">
                      {dbServices.length === 0 ? (
                        <p className="text-sm text-muted-foreground col-span-2 py-4">Nenhum serviço cadastrado ainda.</p>
                      ) : dbServices.map(s => (
                        <button
                          key={s.id}
                          onClick={() => { setSelectedServiceId(s.id); setSelectedServiceLabel(s.name); }}
                          className={`p-3 rounded-lg border text-sm text-left transition-colors ${
                            selectedServiceId === s.id ? "border-primary bg-primary/5 font-medium" : "hover:bg-muted/30"
                          }`}
                        >
                          <p>{s.name}</p>
                          <p className="text-xs text-muted-foreground">R$ {Number(s.price).toFixed(2)}</p>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Profissional (opcional)</Label>
                    <div className="flex flex-wrap gap-2">
                      {PROFESSIONALS.map(p => (
                        <button
                          key={p}
                          onClick={() => setSelectedProf(selectedProf === p ? "" : p)}
                          className={`px-3 py-2 rounded-lg border text-sm transition-colors ${
                            selectedProf === p ? "border-primary bg-primary/5 font-medium" : "hover:bg-muted/30"
                          }`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>
                  </div>

                  {estimatedDuration && (
                    <div className="flex items-center gap-2 p-3 bg-primary/5 rounded-xl border border-primary/10 animate-in fade-in slide-in-from-top-2">
                      <div className="p-1.5 rounded-full bg-primary/20">
                        <Calendar className="h-3.5 w-3.5 text-primary" />
                      </div>
                      <p className="text-xs font-bold text-primary">
                        Sugestão da IA: Tempo estimado de {estimatedDuration} minutos para o(a) {selectedPet?.name}.
                      </p>
                    </div>
                  )}
                </>
              ) : null}

              <div className="space-y-2">
                <Label>Observações Adicionais</Label>
                <Textarea
                  placeholder="Instruções específicas..."
                  rows={4}
                  value={notes}
                  onChange={e => setNotes(e.target.value)}
                />
              </div>
            </div>
          )}

          {/* ── Step 3: Data + Horário ──────────────────────────── */}
          {step === 3 && (
            <div className="space-y-5">
              <div className="space-y-2">
                <Label>Data *</Label>
                <Input
                  type="date"
                  value={date}
                  min={new Date().toISOString().split("T")[0]}
                  onChange={e => setDate(e.target.value)}
                  className="max-w-xs"
                />
              </div>

              <div className="space-y-2">
                <Label>Horário *</Label>
                <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
                  {TIMES.map(t => (
                    <button
                      key={t}
                      onClick={() => setSelectedTime(t)}
                      className={`py-2 rounded-lg border text-sm font-medium transition-colors ${
                        selectedTime === t ? "border-primary bg-primary text-primary-foreground" : "hover:bg-muted/30"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {/* Resumo */}
              {date && selectedTime && (
                <div className="p-4 rounded-lg bg-muted/40 space-y-1 text-sm">
                  <p className="font-semibold mb-2">Resumo do agendamento</p>
                  <p><span className="text-muted-foreground">Tipo:</span> {APPOINTMENT_TYPES.find(t => t.id === appointmentType)?.name}</p>
                  {appointmentType === "servico" ? (
                    <>
                      <p><span className="text-muted-foreground">Pet:</span> {selectedPet?.name}</p>
                      <p><span className="text-muted-foreground">Serviço:</span> {selectedServiceLabel}</p>
                    </>
                  ) : (
                    <p><span className="text-muted-foreground">Desc:</span> {otherDescription}</p>
                  )}
                  <p><span className="text-muted-foreground">Data/hora:</span> {date} às {selectedTime}</p>
                  {estimatedDuration && (
                    <p><span className="text-muted-foreground">Duração prevista:</span> ~{estimatedDuration} min</p>
                  )}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => setStep(Math.max(0, step - 1))}
          disabled={step === 0}
        >
          <ArrowLeft className="h-4 w-4 mr-1.5" /> Voltar
        </Button>

        {step < 3 ? (
          <Button onClick={() => setStep(step + 1)} disabled={!canAdvance()}>
            Avançar <ArrowRight className="h-4 w-4 ml-1.5" />
          </Button>
        ) : (
          <Button onClick={handleConfirm} disabled={!canAdvance() || saving}>
            <Check className="h-4 w-4 mr-1.5" />
            {saving ? "Salvando..." : "Confirmar agendamento"}
          </Button>
        )}
      </div>
    </div>
  );
};

export default NewAppointment;
