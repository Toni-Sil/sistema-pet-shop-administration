import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Calendar, Clock, PawPrint, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

const PublicBooking = () => {
  const { slug } = useParams();
  const [services, setServices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(1);
  const [success, setSuccess] = useState(false);

  // Selection state
  const [selectedService, setSelectedService] = useState<any>(null);
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [petName, setPetName] = useState("");
  const [phone, setPhone] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await api.get(`/public/${slug}/services`);
        setServices(data);
      } catch {
        toast.error("Loja não encontrada ou erro ao carregar.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [slug]);

  const handleSubmit = async () => {
    try {
      await api.post(`/public/${slug}/book`, {
        service: selectedService.name,
        service_id: selectedService.id,
        date,
        time,
        notes: `Pet: ${petName} | Tel: ${phone}`,
        pet_id: null
      });
      setSuccess(true);
    } catch {
      toast.error("Erro ao solicitar agendamento.");
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="max-w-md w-full text-center p-8 space-y-4">
          <CheckCircle2 className="h-16 w-16 text-emerald-500 mx-auto" />
          <h2 className="text-2xl font-bold">Solicitação Enviada!</h2>
          <p className="text-muted-foreground">O pet shop recebeu seu pedido e entrará em contato em breve para confirmar.</p>
          <Button onClick={() => window.location.reload()} variant="outline" className="w-full">Agendar outro pet</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen animated-gradient py-12 px-4 transition-all">
      <div className="max-w-xl mx-auto space-y-8">
        <div className="text-center space-y-3 glass-panel p-6 rounded-3xl border-none shadow-2xl">
           <div className="h-16 w-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-2 border border-primary/20">
              <PawPrint className="h-8 w-8 text-primary" />
           </div>
          <h1 className="text-3xl font-heading font-black tracking-tight text-foreground capitalize">{slug?.replace("-", " ")}</h1>
          <p className="text-muted-foreground font-medium">Agendamento Online de Serviços</p>
        </div>

        <Card className="shadow-2xl border-none rounded-3xl overflow-hidden glass-card">
          <div className="h-2 bg-muted w-full">
             <div 
               className="h-full bg-primary transition-all duration-500" 
               style={{ width: `${(step / 3) * 100}%` }}
             />
          </div>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {step === 1 && "1. Escolha o serviço"}
              {step === 2 && "2. Data e Horário"}
              {step === 3 && "3. Seus Dados"}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {step === 1 && (
              <div className="grid gap-3">
                {loading ? <p>Carregando...</p> : services.map(s => (
                  <button
                    key={s.id}
                    onClick={() => { setSelectedService(s); setStep(2); }}
                    className={`flex items-center justify-between p-5 rounded-2xl border-2 text-left transition-all ${
                      selectedService?.id === s.id ? "border-primary bg-primary/15 shadow-lg shadow-primary/10" : "bg-card/50 hover:border-primary/40 hover:bg-card/80"
                    }`}
                  >
                    <div>
                      <p className="font-bold text-lg">{s.name}</p>
                      <p className="text-sm text-muted-foreground">{s.duration} min • R$ {Number(s.price).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                    </div>
                    <div className={`h-10 w-10 rounded-full flex items-center justify-center transition-colors ${
                      selectedService?.id === s.id ? "bg-primary text-white" : "bg-primary/10 text-primary"
                    }`}>
                      →
                    </div>
                  </button>
                ))}
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="flex items-center gap-2"><Calendar className="h-4 w-4" /> Data</Label>
                  <Input type="date" value={date} onChange={e => setDate(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label className="flex items-center gap-2"><Clock className="h-4 w-4" /> Horário</Label>
                  <Input type="time" value={time} onChange={e => setTime(e.target.value)} />
                </div>
                <div className="flex gap-3 pt-4">
                  <Button variant="outline" className="flex-1" onClick={() => setStep(1)}>Voltar</Button>
                  <Button className="flex-1" disabled={!date || !time} onClick={() => setStep(3)}>Próximo</Button>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="flex items-center gap-2"><PawPrint className="h-4 w-4" /> Nome do Pet</Label>
                  <Input placeholder="Como chama seu pet?" value={petName} onChange={e => setPetName(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label>Seu Telefone (WhatsApp)</Label>
                  <Input placeholder="(00) 00000-0000" value={phone} onChange={e => setPhone(e.target.value)} />
                </div>
                <div className="flex gap-3 pt-4">
                  <Button variant="outline" className="flex-1" onClick={() => setStep(2)}>Voltar</Button>
                  <Button className="flex-1" disabled={!petName || !phone} onClick={handleSubmit}>Solicitar Agendamento</Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PublicBooking;
