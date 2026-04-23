import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Store, User, DollarSign, LogOut, Plus, CheckCircle, Trash2, MessageCircle, TrendingUp, CreditCard, QrCode, Lock, FileText, Building2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useNavigate } from "react-router-dom";
import { format } from "date-fns";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { CardDescription } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Brain, Package, Calendar, ShieldCheck, Cpu, Settings2, Sparkles, Key, Globe, Zap, Info } from "lucide-react";
import PackageManager from "@/components/PackageManager";

interface StoreData { id: string; name: string; slug: string; phone?: string; address?: string; plan: string; settings?: Record<string, any>; }
interface UserData { id: string; name: string; email: string; role: string; }
interface Despesa { id: string; description: string; amount: string; category: string; due_date: string; is_paid: boolean; }
interface WhatsAppLog { id: string; phone: string; message: string; status: string; created_at: string; }

interface AIProviderConfig {
  id: string;
  name: string;
  apiType: string;
  baseUrl?: string;
  apiKey?: string;
}

interface AIAgentConfig {
  providerId: string;
  model: string;
  temperature?: number;
}

const CATEGORIES_AI = ["Aluguel", "Fornecedor", "Salário", "Serviços", "Marketing", "Outros"];

const AGENTS = [
  { id: "orchestrator", name: "Orquestrador", description: "O cérebro principal que decide para qual agente rotear a pergunta.", icon: "Brain" },
  { id: "financial", name: "Agente Financeiro", description: "Responsável por analisar lucros, despesas e faturamento.", icon: "DollarSign" },
  { id: "inventory", name: "Agente de Estoque", description: "Analisa níveis de produtos e alertas de reposição.", icon: "Package" },
  { id: "scheduling", name: "Agente de Agendamento", description: "Organiza a agenda e evita conflitos de horários.", icon: "Calendar" },
  { id: "crm", name: "Agente de CRM / Saúde", description: "Especialista em histórico de pets e vacinas.", icon: "ShieldCheck" },
  { id: "fiscal", name: "Agente Fiscal AI", description: "Traduz erros da SEFAZ, sugere NCM/CFOP e monitora limites tributários.", icon: "FileText" },
];

const DEFAULT_AI_PROVIDERS: AIProviderConfig[] = [
  { id: "openai", name: "OpenAI", apiType: "openai", baseUrl: "https://api.openai.com/v1" },
  { id: "anthropic", name: "Anthropic", apiType: "anthropic", baseUrl: "https://api.anthropic.com" },
  { id: "google", name: "Google Gemini", apiType: "google", baseUrl: "https://generativelanguage.googleapis.com" },
  { id: "groq", name: "Groq", apiType: "openai", baseUrl: "https://api.groq.com/openai/v1" },
  { id: "openrouter", name: "OpenRouter", apiType: "openai", baseUrl: "https://openrouter.ai/api/v1" },
  { id: "together", name: "Together AI", apiType: "openai", baseUrl: "https://api.together.xyz/v1" },
  { id: "deepseek", name: "DeepSeek", apiType: "openai", baseUrl: "https://api.deepseek.com/v1" },
  { id: "xai", name: "xAI", apiType: "openai", baseUrl: "https://api.x.ai/v1" },
  { id: "ollama", name: "Ollama / Local", apiType: "openai", baseUrl: "http://localhost:11434/v1" },
];

const DEFAULT_AI_AGENT_SETTINGS: Record<string, AIAgentConfig> = {
  orchestrator: { providerId: "openai", model: "gpt-4o-mini", temperature: 0.2 },
  financial: { providerId: "openai", model: "gpt-4o-mini", temperature: 0.2 },
  inventory: { providerId: "openai", model: "gpt-4o-mini", temperature: 0.2 },
  scheduling: { providerId: "openai", model: "gpt-4o-mini", temperature: 0.2 },
  crm: { providerId: "openai", model: "gpt-4o-mini", temperature: 0.2 },
  fiscal: { providerId: "openai", model: "gpt-4o-mini", temperature: 0.1 },
};

const API_TYPES = [
  "openai",
  "anthropic",
  "google",
  "azure-openai",
  "bedrock",
  "cohere",
  "huggingface",
  "custom",
];

const MODEL_SUGGESTIONS = [
  "gpt-4o-mini",
  "gpt-4o",
  "gpt-4.1-mini",
  "claude-3-7-sonnet-latest",
  "claude-3-5-sonnet-latest",
  "gemini-1.5-flash",
  "gemini-1.5-pro",
  "deepseek-chat",
  "llama-3.3-70b-versatile",
  "mistral-large-latest",
  "qwen2.5-72b-instruct",
];

const PRESET_PROVIDERS = [
  { id: "openai", name: "OpenAI", apiType: "openai", baseUrl: "https://api.openai.com/v1", icon: "Zap" },
  { id: "anthropic", name: "Anthropic", apiType: "anthropic", baseUrl: "https://api.anthropic.com", icon: "Sparkles" },
  { id: "google", name: "Google Gemini", apiType: "google", baseUrl: "https://generativelanguage.googleapis.com", icon: "Cpu" },
  { id: "groq", name: "Groq", apiType: "openai", baseUrl: "https://api.groq.com/openai/v1", icon: "Zap" },
  { id: "deepseek", name: "DeepSeek", apiType: "openai", baseUrl: "https://api.deepseek.com/v1", icon: "Brain" },
  { id: "openrouter", name: "OpenRouter", apiType: "openai", baseUrl: "https://openrouter.ai/api/v1", icon: "Globe" },
];

const inferProviderFromModel = (model: string) => {
  const m = (model || "").toLowerCase();
  if (m.includes("claude")) return "anthropic";
  if (m.includes("gemini")) return "google";
  if (m.includes("llama") || m.includes("mixtral")) return "groq";
  if (m.includes("deepseek")) return "deepseek";
  if (m.includes("grok")) return "xai";
  if (m.includes("qwen")) return "together";
  return "openai";
};

const normalizeProviders = (rawProviders: any): AIProviderConfig[] => {
  if (!rawProviders) return DEFAULT_AI_PROVIDERS;
  const asArray = Array.isArray(rawProviders)
    ? rawProviders
    : Object.entries(rawProviders).map(([id, value]: any) => ({ id, ...(value || {}) }));

  const normalized = asArray
    .filter((provider: any) => provider && provider.id)
    .map((provider: any) => ({
      id: String(provider.id),
      name: String(provider.name || provider.id),
      apiType: String(provider.apiType || "openai"),
      baseUrl: provider.baseUrl ? String(provider.baseUrl) : "",
      apiKey: provider.apiKey ? String(provider.apiKey) : "",
    }));

  return normalized.length > 0 ? normalized : DEFAULT_AI_PROVIDERS;
};

const normalizeAgentSettings = (rawAgents: any): Record<string, AIAgentConfig> => {
  const next: Record<string, AIAgentConfig> = { ...DEFAULT_AI_AGENT_SETTINGS };

  AGENTS.forEach(({ id }) => {
    const current = rawAgents?.[id];
    if (!current) return;

    if (typeof current === "string") {
      next[id] = {
        providerId: inferProviderFromModel(current),
        model: current,
        temperature: 0.2,
      };
      return;
    }

    if (typeof current === "object") {
      next[id] = {
        providerId: String(current.providerId || inferProviderFromModel(String(current.model || ""))),
        model: String(current.model || next[id].model),
        temperature: Number.isFinite(current.temperature) ? Number(current.temperature) : 0.2,
      };
    }
  });

  return next;
};

const Settings = () => {
  const navigate = useNavigate();
  const [store, setStore] = useState<StoreData | null>(null);
  const [user, setUser] = useState<UserData | null>(null);
  const [waLogs, setWaLogs] = useState<WhatsAppLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // store form
  const [storeName, setStoreName] = useState("");
  const [storePhone, setStorePhone] = useState("");
  const [storeAddress, setStoreAddress] = useState("");
  const [storeWebsite, setStoreWebsite] = useState("");
  const [storeWhatsapp, setStoreWhatsapp] = useState("");
  const [storeCnpj, setStoreCnpj] = useState("");
  const [storeHours, setStoreHours] = useState("");
  const [storeSlogan, setStoreSlogan] = useState("");
  const [storeEmail, setStoreEmail] = useState("");

  // AI Agents settings
  const [aiProviders, setAiProviders] = useState<AIProviderConfig[]>(DEFAULT_AI_PROVIDERS);
  const [aiSettings, setAiSettings] = useState<Record<string, AIAgentConfig>>(DEFAULT_AI_AGENT_SETTINGS);

  const [asaasKey, setAsaasKey] = useState("");
  const [pixKey, setPixKey] = useState("");

  // Fiscal settings
  const [plugnotasKey, setPlugnotasKey] = useState("");
  const [fiscalCnpj, setFiscalCnpj] = useState("");
  const [fiscalIe, setFiscalIe] = useState("");
  const [fiscalIm, setFiscalIm] = useState("");
  const [fiscalRegime, setFiscalRegime] = useState("1");
  const [fiscalCep, setFiscalCep] = useState("");
  const [fiscalLogradouro, setFiscalLogradouro] = useState("");
  const [fiscalNumero, setFiscalNumero] = useState("");
  const [fiscalBairro, setFiscalBairro] = useState("");
  const [fiscalUf, setFiscalUf] = useState("SP");
  const [fiscalCodMunicipio, setFiscalCodMunicipio] = useState("");
  const [fiscalCfop, setFiscalCfop] = useState("5102");
  const [fiscalCst, setFiscalCst] = useState("500");
  const [fiscalNcm, setFiscalNcm] = useState("98010000");
  const [fiscalAliquotaIss, setFiscalAliquotaIss] = useState("0.05");
  const [fiscalCodServico, setFiscalCodServico] = useState("");
  const [fiscalNaturezaNfse, setFiscalNaturezaNfse] = useState("1");
  const [fiscalWebhookToken, setFiscalWebhookToken] = useState("");

  // Evolution API
  const [evoUrl, setEvoUrl] = useState("");
  const [evoKey, setEvoKey] = useState("");
  const [evoInstance, setEvoInstance] = useState("");

  const [quickKey, setQuickKey] = useState("");
  const [selectedPreset, setSelectedPreset] = useState<any>(null);
  const [isQuickOpen, setIsQuickOpen] = useState(false);

  const updateProvider = (providerId: string, updates: Partial<AIProviderConfig>) => {
    setAiProviders((prev) => prev.map((provider) => (
      provider.id === providerId ? { ...provider, ...updates } : provider
    )));
  };

  const addProvider = () => {
    const id = `provider-${Date.now()}`;
    setAiProviders((prev) => [
      ...prev,
      {
        id,
        name: "Novo provedor",
        apiType: "custom",
        baseUrl: "",
        apiKey: "",
      },
    ]);
  };

  const addPresetProvider = () => {
    if (!selectedPreset || !quickKey) return;
    
    // Check if provider already exists by name or base URL
    const existingIndex = aiProviders.findIndex(p => p.baseUrl === selectedPreset.baseUrl || p.id === selectedPreset.id);
    
    if (existingIndex > -1) {
      updateProvider(aiProviders[existingIndex].id, { apiKey: quickKey });
      toast.success(`${selectedPreset.name} atualizado com nova chave!`);
    } else {
      setAiProviders(prev => [
        ...prev,
        {
          id: selectedPreset.id,
          name: selectedPreset.name,
          apiType: selectedPreset.apiType,
          baseUrl: selectedPreset.baseUrl,
          apiKey: quickKey
        }
      ]);
      toast.success(`${selectedPreset.name} configurado com sucesso!`);
    }
    
    setIsQuickOpen(false);
    setQuickKey("");
    setSelectedPreset(null);
  };

  const removeProvider = (providerId: string) => {
    if (aiProviders.length <= 1) {
      toast.error("Mantenha ao menos um provedor configurado.");
      return;
    }

    const fallbackProvider = aiProviders.find((provider) => provider.id !== providerId);
    if (!fallbackProvider) return;

    setAiProviders((prev) => prev.filter((provider) => provider.id !== providerId));
    setAiSettings((prev) => {
      const next = { ...prev };
      AGENTS.forEach(({ id }) => {
        if (next[id]?.providerId === providerId) {
          next[id] = { ...next[id], providerId: fallbackProvider.id };
        }
      });
      return next;
    });
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [meRes, lojaRes, waRes] = await Promise.all([
        api.get("/settings/me"),
        api.get("/settings/loja"),
        api.get("/whatsapp/logs"),
      ]);
      
      if (meRes?.data) setUser(meRes.data);
      if (lojaRes?.data) {
        const d = lojaRes.data;
        setStore(d);
        setStoreName(d.name || "");
        setStorePhone(d.phone || "");
        setStoreAddress(d.address || "");
        
        const S = d.settings || {};
        setStoreWebsite(S.website || "");
        setStoreWhatsapp(S.whatsapp || "");
        setStoreCnpj(S.cnpj || "");
        setStoreHours(S.hours || "");
        setStoreSlogan(S.slogan || "");
        setStoreEmail(S.email || "");
        
        const normalizedProviders = normalizeProviders(S.ai_providers);
        setAiProviders(normalizedProviders);
        setAiSettings(normalizeAgentSettings(S.ai_agents));
        setAsaasKey(S.asaas_key || "");
        setPixKey(S.pix_key || "");
        
        // Fiscal
        setPlugnotasKey(S.plugnotas_api_key || "");
        setFiscalCnpj(S.cnpj || "");
        setFiscalIe(S.inscricao_estadual || "");
        setFiscalIm(S.inscricao_municipal || "");
        setFiscalRegime(S.regime_tributario || "1");
        setFiscalCep(S.cep || "");
        setFiscalLogradouro(S.logradouro || "");
        setFiscalNumero(S.numero || "");
        setFiscalBairro(S.bairro || "");
        setFiscalUf(S.uf || "SP");
        setFiscalCodMunicipio(S.codigo_municipio || "");
        setFiscalCfop(S.cfop_padrao || "5102");
        setFiscalCst(S.cst_padrao || "500");
        setFiscalNcm(S.ncm_padrao || "98010000");
        setFiscalAliquotaIss(String(S.aliquota_iss || "0.05"));
        setFiscalCodServico(S.codigo_servico_municipal || "");
        setFiscalNaturezaNfse(String(S.nfse_natureza || "1"));
        setFiscalWebhookToken(S.plugnotas_webhook_token || "");

        setEvoUrl(S.evolution_api_url || "");
        setEvoKey(S.evolution_api_key || "");
        setEvoInstance(S.evolution_instance || "");
      }
      if (waRes?.data) setWaLogs(waRes.data);
    } catch (e) { console.error(e); toast.error("Erro ao carregar configurações."); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, []);

  const saveLoja = async () => {
    setSaving(true);
    try {
      const newSettings = { 
        ...store?.settings, 
        website: storeWebsite, 
        whatsapp: storeWhatsapp,
        cnpj: storeCnpj,
        hours: storeHours,
        slogan: storeSlogan,
        email: storeEmail
      };
      await api.patch("/settings/loja", { 
        name: storeName, 
        phone: storePhone, 
        address: storeAddress || undefined,
        settings: newSettings
      });
      toast.success("Dados da loja atualizados!");
      if (store) setStore({ ...store, settings: newSettings } as any);
    } catch { toast.error("Erro ao salvar."); }
    finally { setSaving(false); }
  };

  const saveAiSettings = async () => {
    setSaving(true);
    try {
      const newSettings = {
        ...store?.settings,
        ai_agents: aiSettings,
        ai_providers: aiProviders,
      };
      await api.patch("/settings/loja", { settings: newSettings });
      toast.success("Configurações de IA salvas!");
      if (store) setStore({ ...store, settings: newSettings } as any);
    } catch { toast.error("Erro ao salvar configurações de IA."); }
    finally { setSaving(false); }
  };

  const savePaymentSettings = async () => {
    setSaving(true);
    try {
      const newSettings = { ...store?.settings, asaas_key: asaasKey, pix_key: pixKey };
      await api.patch("/settings/loja", { settings: newSettings });
      toast.success("Configurações de pagamento salvas!");
      if (store) setStore({ ...store, settings: newSettings } as any);
    } catch { toast.error("Erro ao salvar configurações de pagamento."); }
    finally { setSaving(false); }
  };

  const saveFiscalSettings = async () => {
    setSaving(true);
    try {
      const newSettings = {
        ...store?.settings,
        plugnotas_api_key: plugnotasKey,
        cnpj: fiscalCnpj,
        inscricao_estadual: fiscalIe,
        inscricao_municipal: fiscalIm,
        regime_tributario: fiscalRegime,
        cep: fiscalCep,
        logradouro: fiscalLogradouro,
        numero: fiscalNumero,
        bairro: fiscalBairro,
        uf: fiscalUf,
        codigo_municipio: fiscalCodMunicipio,
        cfop_padrao: fiscalCfop,
        cst_padrao: fiscalCst,
        ncm_padrao: fiscalNcm,
        aliquota_iss: fiscalAliquotaIss,
        codigo_servico_municipal: fiscalCodServico,
        nfse_natureza: fiscalNaturezaNfse,
        plugnotas_webhook_token: fiscalWebhookToken,
      };
      await api.patch("/settings/loja", { settings: newSettings });
      toast.success("Configurações fiscais salvas!");
      if (store) setStore({ ...store, settings: newSettings } as any);
    } catch { toast.error("Erro ao salvar configurações fiscais."); }
    finally { setSaving(false); }
  };

  const saveWhatsAppSettings = async () => {
    setSaving(true);
    try {
      const newSettings = {
        ...store?.settings,
        evolution_api_url: evoUrl,
        evolution_api_key: evoKey,
        evolution_instance: evoInstance,
      };
      await api.patch("/settings/loja", { settings: newSettings });
      toast.success("Configurações de WhatsApp atualizadas!");
      if (store) setStore({ ...store, settings: newSettings } as any);
    } catch { toast.error("Erro ao salvar configurações de WhatsApp."); }
    finally { setSaving(false); }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
    toast.info("Sessão encerrada.");
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold">Configurações</h1>
          <p className="text-muted-foreground mt-1">Personalize sua loja e preferências.</p>
        </div>
        <Button variant="outline" onClick={handleLogout} className="text-destructive hover:text-destructive">
          <LogOut className="h-4 w-4 mr-1.5" /> Sair
        </Button>
      </div>

      <Tabs defaultValue="loja" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 md:grid-cols-6">
          <TabsTrigger value="loja" className="flex items-center gap-1.5">
            <Store className="h-4 w-4" /> Perfil da loja
          </TabsTrigger>
          <TabsTrigger value="whatsapp" className="flex items-center gap-1.5">
            <MessageCircle className="h-4 w-4" /> WhatsApp
          </TabsTrigger>
          <TabsTrigger value="payments" className="flex items-center gap-1.5">
            <CreditCard className="h-4 w-4" /> Pagamentos
          </TabsTrigger>
          <TabsTrigger value="fiscal" className="flex items-center gap-1.5">
            <FileText className="h-4 w-4" /> Fiscal
          </TabsTrigger>
          <TabsTrigger value="ai" className="flex items-center gap-1.5">
            <TrendingUp className="h-4 w-4" /> IA Agentes
          </TabsTrigger>
          <TabsTrigger value="pacotes" className="flex items-center gap-1.5">
            <Package className="h-4 w-4" /> Pacotes
          </TabsTrigger>
        </TabsList>


        {/* Aba: Dados da Loja */}
        <TabsContent value="loja">
          <Card>
            <CardHeader><CardTitle className="text-base">Perfil da loja</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              {loading ? (
                <div className="space-y-3">{[1,2,3].map(i=><Skeleton key={i} className="h-10 w-full"/>)}</div>
              ) : (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Nome da loja</Label>
                      <Input value={storeName} onChange={e => setStoreName(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label>Slug (URL)</Label>
                      <Input value={store?.slug || ""} disabled className="bg-muted/50 text-muted-foreground" />
                    </div>
                    <div className="space-y-2">
                      <Label>Telefone</Label>
                      <Input value={storePhone} onChange={e => setStorePhone(e.target.value)} placeholder="(11) 99999-9999" />
                    </div>
                    <div className="space-y-2">
                       <Label>E-mail da Loja</Label>
                       <Input value={storeEmail} onChange={e => setStoreEmail(e.target.value)} placeholder="contato@empresa.com" />
                    </div>
                    <div className="space-y-2 sm:col-span-2">
                       <Label>Slogan / Subtítulo</Label>
                       <Input value={storeSlogan} onChange={e => setStoreSlogan(e.target.value)} placeholder="O melhor cuidado para o seu pet" />
                    </div>
                    <div className="space-y-2">
                       <Label>Website / Site</Label>
                       <Input value={storeWebsite} onChange={e => setStoreWebsite(e.target.value)} placeholder="https://www.meupetshop.com.br" />
                    </div>
                    <div className="space-y-2">
                       <Label>WhatsApp</Label>
                       <Input value={storeWhatsapp} onChange={e => setStoreWhatsapp(e.target.value)} placeholder="(11) 99999-9999" />
                    </div>
                    <div className="space-y-2">
                       <Label>CNPJ</Label>
                       <Input value={storeCnpj} onChange={e => setStoreCnpj(e.target.value)} placeholder="00.000.000/0001-00" />
                    </div>
                    <div className="space-y-2">
                       <Label>Horário de Funcionamento</Label>
                       <Input value={storeHours} onChange={e => setStoreHours(e.target.value)} placeholder="Seg a Sex: 08h às 18h" />
                    </div>
                    <div className="space-y-2 sm:col-span-2">
                      <Label>Endereço Completo</Label>
                      <Input value={storeAddress} onChange={e => setStoreAddress(e.target.value)} placeholder="Rua, número - Cidade/UF" />
                    </div>
                  </div>
                  <Button onClick={saveLoja} disabled={saving}>
                    {saving ? "Salvando..." : "Salvar alterações"}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>




        {/* Aba: WhatsApp */}
        <TabsContent value="whatsapp" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Zap className="h-5 w-5 text-primary" /> Integração Evolution API
              </CardTitle>
              <CardDescription>Configure sua instância do WhatsApp para envios reais.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2 md:col-span-2">
                  <Label>URL da API (Evolution)</Label>
                  <Input 
                    value={evoUrl} 
                    onChange={e => setEvoUrl(e.target.value)} 
                    placeholder="https://sua-instancia.com" 
                  />
                </div>
                <div className="space-y-2">
                  <Label>API Key</Label>
                  <Input 
                    type="password"
                    value={evoKey} 
                    onChange={e => setEvoKey(e.target.value)} 
                    placeholder="Sua chave secreta" 
                  />
                </div>
                <div className="space-y-2">
                  <Label>Nome da Instância</Label>
                  <Input 
                    value={evoInstance} 
                    onChange={e => setEvoInstance(e.target.value)} 
                    placeholder="Ex: PetShop01" 
                  />
                </div>
              </div>
              <Button onClick={saveWhatsAppSettings} disabled={saving}>
                {saving ? "Salvando..." : "Salvar Configuração WhatsApp"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <MessageCircle className="h-5 w-5 text-emerald-500" /> Log de Mensagens Recentes
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-2">{[1,2,3].map(i=><Skeleton key={i} className="h-14 w-full"/>)}</div>
              ) : waLogs.length === 0 ? (
                <p className="text-center text-sm text-muted-foreground py-8 border rounded border-dashed">Nenhuma mensagem enviada ainda.</p>
              ) : (
                <div className="space-y-3">
                  {waLogs.map(log => (
                    <div key={log.id} className="p-3 rounded-lg bg-muted/20 border space-y-2">
                      <div className="flex justify-between items-start">
                        <span className="text-sm font-semibold">{log.phone}</span>
                        <span className="text-[10px] text-muted-foreground">
                          {format(new Date(log.created_at), "dd/MM HH:mm")}
                        </span>
                      </div>
                      <p className="text-xs text-foreground whitespace-pre-wrap">{log.message}</p>
                      <div className="flex justify-end">
                        <span className="text-[10px] bg-emerald-500/20 text-emerald-500 px-1.5 py-0.5 rounded uppercase font-bold">
                          {log.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        {/* Aba: Pagamentos */}
        <TabsContent value="payments">
          <Card className="glass-card shadow-xl border-none">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-primary" /> Configurações de Pagamento
              </CardTitle>
              <CardDescription>Configure suas chaves para receber via Pix e Cartão.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
               <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                     <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                           <QrCode className="h-4 w-4 text-emerald-500" /> Chave PIX (Manual)
                        </Label>
                        <Input 
                          placeholder="CNPJ, E-mail ou Telefone" 
                          value={pixKey}
                          onChange={e => setPixKey(e.target.value)}
                        />
                        <p className="text-[10px] text-muted-foreground">Esta chave será exibida caso o Pix automático falhe.</p>
                     </div>

                     <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                           <Lock className="h-4 w-4 text-primary" /> ASAAS API KEY
                        </Label>
                        <Input 
                          type="password"
                          placeholder="$a.abc..." 
                          value={asaasKey}
                          onChange={e => setAsaasKey(e.target.value)}
                        />
                        <p className="text-[10px] text-muted-foreground italic">Necessário para automação de Pix e cobrança via Cartão.</p>
                     </div>
                  </div>

                  <div className="bg-primary/10 rounded-2xl p-6 flex flex-col items-center justify-center text-center space-y-3 border border-primary/20">
                     <div className="h-12 w-12 rounded-full bg-background flex items-center justify-center shadow-sm">
                        <DollarSign className="h-6 w-6 text-primary" />
                     </div>
                     <h4 className="font-bold text-sm">Integração Asaas</h4>
                     <p className="text-xs text-muted-foreground">
                        Ao configurar sua API KEY do Asaas, o sistema poderá gerar QR Codes dinâmicos 
                        e processar cartões de crédito automaticamente.
                     </p>
                     <a href="https://www.asaas.com" target="_blank" rel="noreferrer" className="text-[10px] text-primary underline">Obter minha chave API</a>
                  </div>
               </div>

               <div className="pt-4 border-t">
                  <Button onClick={savePaymentSettings} disabled={saving} className="w-full sm:w-auto px-10">
                    {saving ? "Salvando..." : "Salvar Configurações de Pagamento"}
                  </Button>
               </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai">
          <div className="space-y-6">
            <div className="flex flex-col gap-1">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary animate-pulse" /> Inteligência Artificial
              </h2>
              <p className="text-muted-foreground text-sm">
                Gerencie os motores de IA que alimentam seu Pet Shop.
              </p>
            </div>

            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="providers" className="border rounded-xl bg-card px-4 shadow-sm overflow-hidden">
                <AccordionTrigger className="hover:no-underline py-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Key className="h-4 w-4 text-primary" />
                    </div>
                    <div className="text-left">
                      <p className="text-sm font-semibold">Provedores e Chaves de API</p>
                      <p className="text-xs text-muted-foreground font-normal">Conecte rapidamente seus serviços de IA favoritos.</p>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-6 pt-2">
                  <div className="space-y-6">
                    {/* Quick Connect Session */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Conexão Rápida</span>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
                        {PRESET_PROVIDERS.map(preset => {
                          const isConfigured = aiProviders.some(p => p.baseUrl === preset.baseUrl && p.apiKey);
                          const IconComp = { Zap, Sparkles, Cpu, Brain, Globe }[preset.icon] || Zap;
                          
                          return (
                            <button
                              key={preset.id}
                              onClick={() => { setSelectedPreset(preset); setIsQuickOpen(true); }}
                              className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all gap-1.5 hover:border-primary/50 group ${isConfigured ? 'bg-primary/5 border-primary/20' : 'bg-background hover:bg-muted/30'}`}
                            >
                              <div className={`p-2 rounded-lg transition-colors ${isConfigured ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary'}`}>
                                <IconComp className="h-4 w-4" />
                              </div>
                              <span className="text-[10px] font-bold">{preset.name}</span>
                              {isConfigured && <div className="h-1 w-1 bg-primary rounded-full" />}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-center justify-between pt-4 border-t">
                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Provedores Configurados ({aiProviders.length})</span>
                        <Button variant="outline" size="sm" onClick={addProvider} className="h-8 border-dashed">
                          <Plus className="h-3 w-3 mr-1" /> Configuração Personalizada
                        </Button>
                      </div>

                      <div className="grid grid-cols-1 gap-3">
                        {aiProviders.map((provider) => (
                          <div key={provider.id} className="rounded-lg border bg-muted/5 p-4 relative group transition-all hover:bg-muted/10">
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="absolute top-2 right-2 h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                              onClick={() => removeProvider(provider.id)}
                            >
                              <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive" />
                            </Button>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="space-y-1.5">
                                <Label className="text-[11px] font-bold uppercase text-muted-foreground">Nome do provedor</Label>
                                <Input
                                  className="h-9 text-sm"
                                  value={provider.name}
                                  onChange={(e) => updateProvider(provider.id, { name: e.target.value })}
                                  placeholder="Ex: OpenRouter, OpenAI..."
                                />
                              </div>
                              <div className="space-y-1.5">
                                <Label className="text-[11px] font-bold uppercase text-muted-foreground">Tipo de API</Label>
                                <select
                                  value={provider.apiType}
                                  onChange={(e) => updateProvider(provider.id, { apiType: e.target.value })}
                                  className="w-full text-sm h-9 rounded-md border border-input bg-background px-2 outline-none focus:ring-1 focus:ring-primary"
                                >
                                  {API_TYPES.map((apiType) => (
                                    <option key={apiType} value={apiType}>{apiType}</option>
                                  ))}
                                </select>
                              </div>
                              <div className="space-y-1.5 md:col-span-2">
                                <Label className="text-[11px] font-bold uppercase text-muted-foreground flex items-center gap-1">
                                  <Globe className="h-3 w-3" /> Base URL
                                </Label>
                                <Input
                                  className="h-9 text-sm font-mono"
                                  value={provider.baseUrl || ""}
                                  onChange={(e) => updateProvider(provider.id, { baseUrl: e.target.value })}
                                  placeholder="https://api.openai.com/v1"
                                />
                              </div>
                              <div className="space-y-1.5 md:col-span-2">
                                <Label className="text-[11px] font-bold uppercase text-muted-foreground flex items-center gap-1">
                                  <Key className="h-3 w-3" /> API Key
                                </Label>
                                <div className="relative">
                                  <Input
                                    type="password"
                                    className="h-9 text-sm pr-10"
                                    value={provider.apiKey || ""}
                                    onChange={(e) => updateProvider(provider.id, { apiKey: e.target.value })}
                                    placeholder="••••••••••••••••"
                                  />
                                  <Lock className="absolute right-3 top-2.5 h-4 w-4 text-muted-foreground/50" />
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>

            <Card className="border-none shadow-none bg-transparent">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-primary/10">
                  <Settings2 className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold">Configuração dos Agentes Específicos</h3>
                  <p className="text-xs text-muted-foreground">Escolha qual cérebro cuida de cada parte do seu negócio.</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {AGENTS.map(agent => (
                  <AgentModelSelector 
                    key={agent.id}
                    agent={agent}
                    currentConfig={aiSettings[agent.id] || DEFAULT_AI_AGENT_SETTINGS[agent.id]}
                    providers={aiProviders}
                    onChange={(nextConfig: AIAgentConfig) => setAiSettings(prev => ({ ...prev, [agent.id]: nextConfig }))}
                  />
                ))}
              </div>
            </Card>

            <div className="flex gap-4 p-4 rounded-xl bg-primary/5 border border-primary/10 items-start">
              <div className="p-2 rounded-full bg-primary/10 mt-0.5">
                <Info className="h-4 w-4 text-primary" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-semibold">Dica de Performance</p>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Para o <span className="font-bold">Orquestrador</span>, recomendamos modelos mais inteligentes como <span className="font-mono text-[10px] bg-primary/10 px-1 rounded">GPT-4o</span> ou <span className="font-mono text-[10px] bg-primary/10 px-1 rounded">Claude 3.5 Sonnet</span>. 
                  Para tarefas de rotina, modelos "Mini" ou "Flash" são mais rápidos e econômicos.
                </p>
              </div>
            </div>

            <Button 
              onClick={saveAiSettings} 
              disabled={saving} 
              className="w-full h-12 text-base font-semibold shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all active:scale-[0.98]"
            >
              {saving ? (
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Salvando Configurações...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 fill-current" /> Salvar Configurações de IA
                </div>
              )}
            </Button>
          </div>
        </TabsContent>

        {/* Aba: Configurações Fiscais */}
        <TabsContent value="fiscal">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" /> Integração PlugNotas
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="flex items-center gap-2"><Lock className="h-4 w-4" /> API Key PlugNotas</Label>
                  <Input type="password" value={plugnotasKey} onChange={e => setPlugnotasKey(e.target.value)} placeholder="xxxxxxxxxxxxxxxxxxx" />
                  <p className="text-[10px] text-muted-foreground">Obtenha em <a href="https://plugnotas.com.br" target="_blank" rel="noreferrer" className="underline text-primary">plugnotas.com.br</a>. Sem esta chave, a emissão automática não funcionará.</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-primary" /> Dados do Emitente
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2"><Label>CNPJ</Label><Input value={fiscalCnpj} onChange={e => setFiscalCnpj(e.target.value)} placeholder="00.000.000/0001-00" /></div>
                  <div className="space-y-2"><Label>Inscrição Estadual</Label><Input value={fiscalIe} onChange={e => setFiscalIe(e.target.value)} placeholder="ISENTO ou número" /></div>
                  <div className="space-y-2"><Label>Inscrição Municipal</Label><Input value={fiscalIm} onChange={e => setFiscalIm(e.target.value)} placeholder="Número IM" /></div>
                  <div className="space-y-2">
                    <Label>Regime Tributário</Label>
                    <select value={fiscalRegime} onChange={e => setFiscalRegime(e.target.value)} className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-1 focus:ring-primary">
                      <option value="1">1 — Simples Nacional</option>
                      <option value="2">2 — Simples Nacional — excesso</option>
                      <option value="3">3 — Regime Normal</option>
                    </select>
                  </div>
                  <div className="space-y-2"><Label>CEP</Label><Input value={fiscalCep} onChange={e => setFiscalCep(e.target.value)} placeholder="00000-000" /></div>
                  <div className="space-y-2"><Label>Logradouro</Label><Input value={fiscalLogradouro} onChange={e => setFiscalLogradouro(e.target.value)} placeholder="Rua Exemplo" /></div>
                  <div className="space-y-2"><Label>Número</Label><Input value={fiscalNumero} onChange={e => setFiscalNumero(e.target.value)} placeholder="123" /></div>
                  <div className="space-y-2"><Label>Bairro</Label><Input value={fiscalBairro} onChange={e => setFiscalBairro(e.target.value)} placeholder="Centro" /></div>
                  <div className="space-y-2"><Label>UF</Label><Input value={fiscalUf} onChange={e => setFiscalUf(e.target.value)} placeholder="SP" maxLength={2} /></div>
                  <div className="space-y-2"><Label>Cód. Município IBGE</Label><Input value={fiscalCodMunicipio} onChange={e => setFiscalCodMunicipio(e.target.value)} placeholder="3550308" /></div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Parâmetros Fiscais (NF-e)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="space-y-2"><Label>CFOP Padrão</Label><Input value={fiscalCfop} onChange={e => setFiscalCfop(e.target.value)} placeholder="5102" /></div>
                  <div className="space-y-2"><Label>CST/CSOSN Padrão</Label><Input value={fiscalCst} onChange={e => setFiscalCst(e.target.value)} placeholder="500" /></div>
                  <div className="space-y-2"><Label>NCM Padrão</Label><Input value={fiscalNcm} onChange={e => setFiscalNcm(e.target.value)} placeholder="98010000" /></div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Parâmetros Fiscais (NFS-e)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="space-y-2"><Label>Alíquota ISS (%)</Label><Input type="number" step="0.01" value={fiscalAliquotaIss} onChange={e => setFiscalAliquotaIss(e.target.value)} placeholder="0.05" /></div>
                  <div className="space-y-2"><Label>Código Serviço Municipal</Label><Input value={fiscalCodServico} onChange={e => setFiscalCodServico(e.target.value)} placeholder="04847" /></div>
                  <div className="space-y-2"><Label>Natureza Operação NFS-e</Label><Input value={fiscalNaturezaNfse} onChange={e => setFiscalNaturezaNfse(e.target.value)} placeholder="1" /></div>
                </div>
                <p className="text-[10px] text-muted-foreground mt-3">⚠️ Consulte seu contador para o código correto de serviço e alíquota ISS do seu município.</p>
              </CardContent>
            </Card>

            {/* Webhook e avisos técnicos */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Lock className="h-5 w-5 text-primary" /> Webhook PlugNotas
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>URL do Webhook (configure no painel PlugNotas)</Label>
                  <div className="flex items-center gap-2 p-2 bg-muted/50 rounded-md border text-xs font-mono break-all">
                    {window.location.origin}/api/v1/fiscal/webhook/plugnotas
                  </div>
                  <p className="text-[10px] text-muted-foreground">Configure esta URL em Integrações &gt; Webhook no painel PlugNotas para receber o status final automaticamente.</p>
                </div>
                <div className="space-y-2">
                  <Label className="flex items-center gap-2"><Lock className="h-4 w-4" /> Token de Segurança do Webhook</Label>
                  <Input type="password" value={fiscalWebhookToken} onChange={e => setFiscalWebhookToken(e.target.value)} placeholder="token-secreto-webhook" />
                  <p className="text-[10px] text-muted-foreground">Enviado no header X-Plugnotas-Token. Gere um token aleatório e configure o mesmo no painel PlugNotas.</p>
                </div>
              </CardContent>
            </Card>

            {/* Aviso técnico importante */}
            <div className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/5 space-y-2">
              <p className="text-sm font-bold text-amber-400">⚠️ Avisos técnicos importantes</p>
              <ul className="text-xs text-muted-foreground space-y-1.5 list-disc list-inside">
                <li><strong>Certificado A1:</strong> deve ser cadastrado diretamente no painel PlugNotas, não aqui.</li>
                <li><strong>NF-e:</strong> o status final (autorizado/rejeitado) chega via webhook ou polling — não é imediato.</li>
                <li><strong>NFS-e:</strong> regras de alíquota ISS e código de serviço variam por município. Valide com seu contador.</li>
                <li><strong>Rejeições SEFAZ:</strong> são registradas com o motivo exato. Use o botão "Reenviar" após corrigir os dados.</li>
                <li><strong>Cancelamento NF-e:</strong> prazo máximo de 168h após autorização conforme legislação.</li>
              </ul>
            </div>

            <Button onClick={saveFiscalSettings} disabled={saving} className="w-full sm:w-auto">
              {saving ? "Salvando..." : "Salvar Configurações Fiscais"}
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="pacotes">
          <PackageManager />
        </TabsContent>

      </Tabs>

      {/* Quick Connect Dialog */}
      <Dialog open={isQuickOpen} onOpenChange={setIsQuickOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              Conectar ao {selectedPreset?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="p-3 rounded-lg bg-primary/5 border border-primary/10 space-y-2">
              <p className="text-xs text-muted-foreground">
                Configuraremos automaticamente o endpoint base e o tipo de API. Você só precisa colar sua chave abaixo.
              </p>
              <div className="text-[10px] font-mono opacity-60">
                URL: {selectedPreset?.baseUrl}
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-xs font-bold uppercase">API Key do {selectedPreset?.name}</Label>
              <Input
                type="password"
                placeholder="sk-..."
                value={quickKey}
                onChange={(e) => setQuickKey(e.target.value)}
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && addPresetProvider()}
              />
            </div>
            <Button className="w-full" onClick={addPresetProvider} disabled={!quickKey}>
              Confirmar Conexão
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const AgentModelSelector = ({ agent, currentConfig, providers, onChange }: any) => {
  const currentProvider = providers.find((provider: AIProviderConfig) => provider.id === currentConfig?.providerId);
  
  const IconComponent = {
    Brain: Brain,
    DollarSign: DollarSign,
    Package: Package,
    Calendar: Calendar,
    ShieldCheck: ShieldCheck,
  }[agent.icon as string] || Sparkles;

  return (
     <div className="flex flex-col h-full bg-card rounded-xl border border-border/50 p-5 gap-4 hover:border-primary/40 hover:shadow-md transition-all group relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 rounded-full -mr-12 -mt-12 transition-all group-hover:scale-110" />
        
        <div className="flex items-start gap-4 z-10">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary group-hover:scale-110 transition-transform">
             <IconComponent className="h-5 w-5" />
          </div>
          <div className="space-y-1 pr-6">
            <h4 className="text-sm font-bold leading-none">{agent.name}</h4>
            <p className="text-xs text-muted-foreground leading-tight">{agent.description}</p>
          </div>
        </div>

        <div className="space-y-4 pt-2 mt-auto z-10">
          <div className="grid grid-cols-1 gap-3">
            <div className="space-y-1.5">
              <Label className="text-[10px] font-bold uppercase text-muted-foreground px-1">Provedor</Label>
              <select
                value={currentConfig?.providerId}
                onChange={(e) => onChange({ ...currentConfig, providerId: e.target.value })}
                className="w-full text-xs h-9 rounded-lg border border-input bg-background/50 px-2 focus:ring-1 focus:ring-primary outline-none"
              >
                {providers.map((provider: AIProviderConfig) => (
                  <option key={provider.id} value={provider.id}>
                    {provider.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="space-y-1.5 col-span-2">
                <Label className="text-[10px] font-bold uppercase text-muted-foreground px-1">Modelo</Label>
                <Input
                  className="h-9 text-xs"
                  value={currentConfig?.model || ""}
                  list="llm-model-suggestions"
                  onChange={(e) => onChange({ ...currentConfig, model: e.target.value })}
                  placeholder="Modelo"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] font-bold uppercase text-muted-foreground px-1">Temp</Label>
                <div className="relative">
                  <Input
                    type="number"
                    min={0}
                    max={2}
                    step={0.1}
                    className="h-9 text-xs pr-2"
                    value={String(currentConfig?.temperature ?? 0.2)}
                    onChange={(e) => onChange({ ...currentConfig, temperature: Number(e.target.value || 0.2) })}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 mt-2 opacity-50 text-[9px] font-mono italic">
          <div className="h-1 w-1 bg-primary rounded-full animate-pulse" />
          {currentProvider?.name || "Desconhecido"} · {currentConfig?.model || "padrão"}
        </div>
     </div>
  );
};

export default Settings;
