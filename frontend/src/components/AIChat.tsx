import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sparkles, X, Send, Bot, User as UserIcon, Loader2, Volume2, Paperclip } from "lucide-react";
import { api } from "@/lib/api";
import { ScrollArea } from "@/components/ui/scroll-area";

interface AIAction {
  label: string;
  type: 'navigate' | 'whatsapp' | 'modal';
  payload: any;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  actions?: AIAction[];
  suggestions?: string[];
}

import { useNavigate } from "react-router-dom";

export const AIChat = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [history, setHistory] = useState<Message[]>([
    { role: "assistant", content: "Olá! Como posso ajudar você a gerir seu Pet Shop hoje?" }
  ]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [history]);

  const handleSend = async () => {
    if (!message.trim() || loading) return;

    const userMsg = message;
    setMessage("");
    setHistory(prev => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const { data } = await api.post("/ai/chat", { message: userMsg });
      
      // Se houver uma ação com target_selector, dispara o guia
      const guideAction = data.actions?.find((a: any) => a.target_selector);
      if (guideAction) {
        window.dispatchEvent(new CustomEvent("ai-guide-target", { 
          detail: { 
            selector: guideAction.target_selector,
            message: data.response,
            label: guideAction.label
          } 
        }));
      }

      setHistory(prev => [...prev, { 
        role: "assistant", 
        content: data.response,
        actions: data.actions || [],
        suggestions: data.suggestions || []
      }]);
    } catch {
      setHistory(prev => [...prev, { role: "assistant", content: "Ops, tive um problema ao processar seu pedido. Tente novamente mais tarde." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Simula o envio do arquivo informando ao chat
    setMessage(`[Arquivo Anexado: ${file.name}] Por favor, analise este arquivo para mim.`);
    toast.info("Arquivo anexado! Clique em enviar para processar.");
  };

  const handleAction = (action: AIAction) => {
    if (action.type === 'navigate') {
      navigate(action.payload);
      setIsOpen(false);
    } else if (action.type === 'whatsapp') {
      const { phone, message } = action.payload;
      window.open(`https://wa.me/${phone}?text=${encodeURIComponent(message)}`, "_blank");
    }
  };

  const speak = (text: string) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'pt-BR';
    window.speechSynthesis.speak(utterance);
  };

  const lastAssistantMessage = [...history].reverse().find(m => m.role === 'assistant');

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {isOpen && (
        <Card className="w-[380px] h-[500px] shadow-2xl mb-4 flex flex-col glass-card border-primary/20 animate-in slide-in-from-bottom-5 duration-300">
          <CardHeader className="bg-primary text-primary-foreground p-4 rounded-t-xl flex flex-row items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Sparkles className="h-4 w-4" /> Assistente IA Especialista
            </CardTitle>
            <Button variant="ghost" size="icon" className="h-8 w-8 text-primary-foreground hover:bg-primary-foreground/10" onClick={() => setIsOpen(false)}>
              <X className="h-4 w-4" />
            </Button>
          </CardHeader>
          
          <CardContent className="flex-1 p-3 overflow-hidden">
            <ScrollArea className="h-full pr-3">
              <div className="space-y-4">
                {history.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div className={`flex gap-2 max-w-[85%] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                      <div className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === "user" ? "bg-primary" : "bg-secondary"}`}>
                        {msg.role === "user" ? <UserIcon className="h-4 w-4 text-white" /> : <Bot className="h-4 w-4 text-primary" />}
                      </div>
                      <div className={`p-3 rounded-2xl text-sm relative ${
                        msg.role === "user" 
                        ? "bg-primary text-primary-foreground rounded-tr-none" 
                        : "bg-secondary text-foreground rounded-tl-none border shadow-sm"
                      }`}>
                        {msg.content}
                        
                        {msg.role === 'assistant' && (
                          <button 
                            className="absolute -right-7 top-0 p-1 text-muted-foreground hover:text-primary transition-colors"
                            onClick={() => speak(msg.content)}
                          >
                            <Volume2 className="h-4 w-4" />
                          </button>
                        )}

                        {msg.actions && msg.actions.length > 0 && (
                          <div className="mt-4 flex flex-wrap gap-2">
                            {msg.actions.map((action, idx) => (
                              <Button 
                                key={idx} 
                                size="sm" 
                                className="h-8 text-[11px] bg-primary hover:bg-primary/90 text-primary-foreground font-black shadow-lg shadow-primary/20 transition-all rounded-full px-4"
                                onClick={() => handleAction(action)}
                              >
                                {action.label}
                              </Button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="flex gap-2 items-center text-muted-foreground">
                      <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center">
                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
                      </div>
                      <span className="text-xs italic">AI está pensando...</span>
                    </div>
                  </div>
                )}
                <div ref={scrollRef} />
              </div>
            </ScrollArea>
          </CardContent>

          <CardFooter className="p-3 border-t bg-secondary/30 rounded-b-xl flex flex-col gap-3">
            {lastAssistantMessage?.suggestions && lastAssistantMessage.suggestions.length > 0 && (
              <div className="flex gap-2 overflow-x-auto pb-1 custom-scrollbar w-full">
                {lastAssistantMessage.suggestions.map((s, idx) => (
                  <button 
                    key={idx} 
                    className="whitespace-nowrap px-3 py-1 rounded-full bg-background border border-primary/20 text-[10px] text-primary hover:bg-primary/10 transition-colors font-medium"
                    onClick={() => {
                      setMessage(s);
                      // Auto-send can be added here if desired
                    }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
            <div className="flex w-full gap-2 items-center">
              <input 
                type="file" 
                id="ai-chat-file" 
                className="hidden" 
                onChange={handleFileSelect}
                accept=".csv,.txt,.pdf,.png,.jpg,.jpeg"
              />
              <Button 
                variant="ghost" 
                size="icon" 
                className="h-9 w-9 text-muted-foreground hover:text-primary transition-colors"
                onClick={() => document.getElementById('ai-chat-file')?.click()}
              >
                <Paperclip className="h-4 w-4" />
              </Button>
              <Input 
                placeholder="Pergunte ou anexe um arquivo..." 
                value={message}
                onChange={e => setMessage(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleSend()}
              />
              <Button size="icon" onClick={handleSend} disabled={loading || !message.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </CardFooter>
        </Card>
      )}

      <Button
        size="lg"
        className={`rounded-full h-14 w-14 shadow-2xl transition-all duration-300 ${isOpen ? "rotate-90 scale-0" : "hover:scale-110"}`}
        onClick={() => setIsOpen(true)}
      >
        <Sparkles className="h-6 w-6" />
      </Button>
    </div>
  );
};
