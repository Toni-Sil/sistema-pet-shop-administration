import { useState, useEffect, useRef } from "react";
import { Mic, MicOff, Search, Loader2, Sparkles, X, ChevronRight, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useNavigate } from "react-router-dom";

// Interface para a Web Speech API
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onresult: (event: any) => void;
  onerror: (event: any) => void;
  onend: () => void;
}

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export const VoiceCommander = () => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [showPanel, setShowPanel] = useState(false);
  const recognitionRef = useRef<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = "pt-BR";

      recognitionRef.current.onresult = (event: any) => {
        const current = event.results[event.results.length - 1][0].transcript;
        setTranscript(current);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error("Erro no reconhecimento de voz:", event.error);
        setIsListening(false);
        toast.error("Erro ao ouvir. Tente novamente.");
      };
    }
  }, []);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      setTranscript("");
      setShowPanel(true);
      recognitionRef.current?.start();
      setIsListening(true);
    }
  };

  const handleProcessIntent = async () => {
    if (!transcript.trim()) return;
    
    setIsProcessing(true);
    try {
      const { data } = await api.post("/ai/chat", { message: transcript });
      
      // Processa ações da IA (Navegação, Preenchimento de Form, etc)
      if (data.actions && data.actions.length > 0) {
        data.actions.forEach((action: any) => {
          if (action.type === "navigate") {
            navigate(action.payload);
            toast.success(`Navegando para: ${action.label}`);
          }
          if (action.type === "form_fill") {
             // Lógica para preencher formulários (emitir evento customizado)
             window.dispatchEvent(new CustomEvent("ai_form_fill", { detail: action.payload }));
             toast.success(`Preenchendo: ${action.label}`);
          }
        });
      }

      toast.info(data.response, { duration: 5000 });
      setShowPanel(false);
    } catch (error) {
      toast.error("Erro ao processar comando de voz.");
    } finally {
      setIsProcessing(false);
    }
  };

  useEffect(() => {
    if (!isListening && transcript && showPanel) {
      const timeout = setTimeout(handleProcessIntent, 1500);
      return () => clearTimeout(timeout);
    }
  }, [isListening, transcript]);

  if (!recognitionRef.current) return null;

  return (
    <>
      <div className="fixed bottom-6 right-24 z-[100] group flex flex-col items-end gap-3">
        {showPanel && (
          <div className="bg-background/95 backdrop-blur-md border border-primary/20 p-6 rounded-3xl shadow-2xl w-[320px] animate-in slide-in-from-bottom-5 duration-300 space-y-4">
             <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                   <div className="h-2 w-2 bg-primary rounded-full animate-pulse" />
                   <span className="text-xs font-bold uppercase tracking-widest text-primary">AIGuide Ativo</span>
                </div>
                <button onClick={() => setShowPanel(false)} className="text-muted-foreground hover:text-foreground">
                   <X className="h-4 w-4" />
                </button>
             </div>
             
             <div className="min-h-[60px] flex items-center justify-center text-center italic">
                {transcript ? (
                  <p className="text-sm font-medium leading-relaxed">"{transcript}"</p>
                ) : (
                  <p className="text-sm text-muted-foreground">Fale seu comando agora...</p>
                )}
             </div>

             {isProcessing && (
               <div className="flex items-center justify-center gap-2 text-xs text-primary font-bold">
                 <Loader2 className="h-3 w-3 animate-spin" /> Processando sua intenção...
               </div>
             )}

             {!isProcessing && !isListening && transcript && (
                <div className="grid grid-cols-2 gap-2">
                   <Button variant="outline" size="sm" onClick={() => { setTranscript(""); toggleListening(); }}>Repetir</Button>
                   <Button size="sm" onClick={handleProcessIntent}>Confirmar</Button>
                </div>
             )}
          </div>
        )}

        <button
          onClick={toggleListening}
          className={`h-14 w-14 rounded-2xl flex items-center justify-center transition-all shadow-xl hover:scale-110 active:scale-95 ${
            isListening 
            ? "bg-destructive text-destructive-foreground animate-pulse" 
            : "bg-primary text-primary-foreground shadow-primary/30"
          }`}
        >
          {isListening ? <MicOff className="h-6 w-6" /> : <Mic className="h-6 w-6" />}
        </button>
      </div>
    </>
  );
};
