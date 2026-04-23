import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  FileText,
  RefreshCw,
  CheckCircle2,
  Clock,
  XCircle,
  Download,
  ExternalLink,
  AlertTriangle,
  Receipt,
  Wrench,
  Filter,
  Send,
  Ban,
  Loader2,
  Info,
  RotateCcw,
  Hourglass,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface NotaFiscal {
  id: string;
  tipo: "nfe" | "nfse";
  /** Lifecycle:
   *  pending    = criada localmente, aguardando envio ao PlugNotas
   *  processing = enviada; aguardando resposta da SEFAZ/Prefeitura
   *  authorized = autorizada com chave de acesso e DANFE disponíveis
   *  rejected   = rejeitada pela SEFAZ/Prefeitura (com motivo)
   *  error      = falha de rede/servidor; pode ser reenviada
   *  cancelled  = cancelada após autorização
   */
  status: "pending" | "processing" | "authorized" | "rejected" | "cancelled" | "error";
  sale_id: string | null;
  appointment_id: string | null;
  destinatario_nome: string | null;
  destinatario_cpf_cnpj: string | null;
  valor_total: string;
  numero_nota: string | null;
  serie: string | null;
  chave_acesso: string | null;
  danfe_url: string | null;
  xml_url: string | null;
  descricao: string | null;
  motivo_rejeicao: string | null;
  ultimo_erro: string | null;
  tentativas: number | null;
  max_tentativas: number | null;
  created_at: string;
  authorized_at: string | null;
  webhook_recebido_em: string | null;
  last_sync_at: string | null;
}

interface Resumo {
  [key: string]: { tipo: string; status: string; quantidade: number; valor_total: number };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  authorized: {
    label: "Autorizada",
    color: "bg-emerald-500/15 text-emerald-500 border-emerald-500/30",
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
  },
  processing: {
    label: "Em processamento",
    color: "bg-blue-500/15 text-blue-400 border-blue-500/30",
    icon: <Hourglass className="h-3.5 w-3.5" />,
  },
  pending: {
    label: "Aguardando envio",
    color: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    icon: <Clock className="h-3.5 w-3.5" />,
  },
  rejected: {
    label: "Rejeitada",
    color: "bg-red-500/15 text-red-400 border-red-500/30",
    icon: <XCircle className="h-3.5 w-3.5" />,
  },
  error: {
    label: "Erro (reemissível)",
    color: "bg-orange-500/15 text-orange-400 border-orange-500/30",
    icon: <AlertTriangle className="h-3.5 w-3.5" />,
  },
  cancelled: {
    label: "Cancelada",
    color: "bg-gray-500/15 text-gray-400 border-gray-500/30",
    icon: <Ban className="h-3.5 w-3.5" />,
  },
};

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? {
    label: status,
    color: "bg-muted text-muted-foreground",
    icon: null,
  };
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border ${cfg.color}`}
    >
      {cfg.icon} {cfg.label}
    </span>
  );
}

function TipoBadge({ tipo }: { tipo: string }) {
  return tipo === "nfe" ? (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-500/15 text-blue-400 border border-blue-500/30">
      <Receipt className="h-3 w-3" /> NF-e
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-violet-500/15 text-violet-400 border border-violet-500/30">
      <Wrench className="h-3 w-3" /> NFS-e
    </span>
  );
}

function moeda(v: string | number) {
  return Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
const Fiscal = () => {
  const [notas, setNotas] = useState<NotaFiscal[]>([]);
  const [resumo, setResumo] = useState<Resumo>({});
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const [filtroTipo, setFiltroTipo] = useState<string>("all");
  const [filtroStatus, setFiltroStatus] = useState<string>("all");

  const [emitModal, setEmitModal] = useState<{ open: boolean; tipo: "nfe" | "nfse" }>({ open: false, tipo: "nfe" });
  const [emitId, setEmitId] = useState("");
  const [emitting, setEmitting] = useState(false);

  const [cancelModal, setCancelModal] = useState<{ open: boolean; nota: NotaFiscal | null }>({ open: false, nota: null });
  const [cancelMotivo, setCancelMotivo] = useState("");
  const [cancelling, setCancelling] = useState(false);

  const [detailNota, setDetailNota] = useState<NotaFiscal | null>(null);

  const carregarNotas = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filtroTipo !== "all") params.tipo = filtroTipo;
      if (filtroStatus !== "all") params.status = filtroStatus;
      const [notasRes, resumoRes] = await Promise.all([
        api.get("/fiscal", { params }),
        api.get("/fiscal/stats/resumo"),
      ]);
      setNotas(notasRes.data);
      setResumo(resumoRes.data);
    } catch {
      toast.error("Erro ao carregar notas fiscais.");
    } finally {
      setLoading(false);
    }
  }, [filtroTipo, filtroStatus]);

  useEffect(() => {
    carregarNotas();
  }, [carregarNotas]);

  const sincronizar = async () => {
    setSyncing(true);
    try {
      await api.post("/fiscal/sincronizar");
      toast.info("Sincronização iniciada (verifica notas 'Em processamento'). Aguarde e recarregue.");
      setTimeout(() => carregarNotas(), 4000);
    } catch {
      toast.error("Erro ao sincronizar.");
    } finally {
      setSyncing(false);
    }
  };

  const emitirNota = async () => {
    if (!emitId.trim()) return toast.error("Informe o ID.");
    setEmitting(true);
    try {
      const body = emitModal.tipo === "nfe" ? { sale_id: emitId.trim() } : { appointment_id: emitId.trim() };
      await api.post(`/fiscal/emitir/${emitModal.tipo}`, body);
      toast.success(`${emitModal.tipo.toUpperCase()} enviada! Status inicial: Em processamento.`);
      setEmitModal({ open: false, tipo: "nfe" });
      setEmitId("");
      carregarNotas();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Erro ao emitir nota.");
    } finally {
      setEmitting(false);
    }
  };

  const cancelarNota = async () => {
    if (!cancelModal.nota || cancelMotivo.length < 15) return toast.error("Justificativa mínima de 15 caracteres.");
    setCancelling(true);
    try {
      await api.post(`/fiscal/${cancelModal.nota.id}/cancelar`, { motivo: cancelMotivo });
      toast.success("Nota cancelada com sucesso.");
      setCancelModal({ open: false, nota: null });
      setCancelMotivo("");
      carregarNotas();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Erro ao cancelar nota.");
    } finally {
      setCancelling(false);
    }
  };

  // Computed stats
  const totalAutorizadas = Object.values(resumo).filter((r) => r.status === "authorized").reduce((s, r) => s + r.valor_total, 0);
  const totalProcessando = Object.values(resumo).filter((r) => r.status === "processing").reduce((s, r) => s + r.quantidade, 0);
  const totalRejeitadas = Object.values(resumo).filter((r) => r.status === "rejected").reduce((s, r) => s + r.quantidade, 0);
  const totalErros = Object.values(resumo).filter((r) => r.status === "error").reduce((s, r) => s + r.quantidade, 0);
  const countAutorizadas = Object.values(resumo).filter((r) => r.status === "authorized").reduce((s, r) => s + r.quantidade, 0);

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold flex items-center gap-2">
            <FileText className="h-6 w-6 text-primary" />
            Notas Fiscais
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">NF-e e NFS-e via PlugNotas</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={sincronizar} disabled={syncing} id="btn-sincronizar-fiscal">
            {syncing ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <RefreshCw className="h-4 w-4 mr-1.5" />}
            Sincronizar status
          </Button>
          <Button size="sm" onClick={() => setEmitModal({ open: true, tipo: "nfe" })} id="btn-emitir-nfe">
            <Send className="h-4 w-4 mr-1.5" /> Emitir NF-e
          </Button>
          <Button size="sm" variant="secondary" onClick={() => setEmitModal({ open: true, tipo: "nfse" })} id="btn-emitir-nfse">
            <Send className="h-4 w-4 mr-1.5" /> Emitir NFS-e
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Valor Autorizado" value={moeda(totalAutorizadas)} icon={<CheckCircle2 className="h-5 w-5 text-emerald-500" />} color="emerald" />
        <KpiCard label="Notas Emitidas" value={String(countAutorizadas)} icon={<FileText className="h-5 w-5 text-blue-400" />} color="blue" />
        <KpiCard label="Em Processamento" value={String(totalProcessando)} icon={<Hourglass className="h-5 w-5 text-amber-400" />} color="amber" />
        <KpiCard label="Rejeitadas / Erro" value={String(totalRejeitadas + totalErros)} icon={<XCircle className="h-5 w-5 text-red-400" />} color="red" />
      </div>

      {/* Info */}
      <div className="flex items-start gap-3 p-4 rounded-xl border border-blue-500/20 bg-blue-500/5">
        <Info className="h-4 w-4 text-blue-400 mt-0.5 shrink-0" />
        <p className="text-xs text-muted-foreground leading-relaxed">
          O status <strong className="text-foreground">não é imediato</strong> — a SEFAZ/Prefeitura leva de segundos a minutos para processar.
          O retorno final chega via <strong className="text-foreground">webhook</strong> (configure a URL em Configurações → Fiscal) ou use{" "}
          <strong className="text-foreground">"Sincronizar status"</strong> como fallback.
          Notas com <strong className="text-foreground">erro de rede</strong> podem ser reenviadas com o botão ↺.
        </p>
      </div>

      {/* Filters + List */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Filter className="h-4 w-4" /> Histórico de Notas
            </CardTitle>
            <div className="flex gap-2">
              <Select value={filtroTipo} onValueChange={setFiltroTipo}>
                <SelectTrigger className="w-32 h-8 text-xs" id="filtro-tipo">
                  <SelectValue placeholder="Tipo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="nfe">NF-e</SelectItem>
                  <SelectItem value="nfse">NFS-e</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filtroStatus} onValueChange={setFiltroStatus}>
                <SelectTrigger className="w-40 h-8 text-xs" id="filtro-status">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="authorized">Autorizadas</SelectItem>
                  <SelectItem value="processing">Em processamento</SelectItem>
                  <SelectItem value="pending">Aguardando envio</SelectItem>
                  <SelectItem value="rejected">Rejeitadas</SelectItem>
                  <SelectItem value="error">Erro (reemissível)</SelectItem>
                  <SelectItem value="cancelled">Canceladas</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-14 w-full rounded-lg" />
              ))}
            </div>
          ) : notas.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
              <FileText className="h-12 w-12 text-muted-foreground/30" />
              <p className="text-muted-foreground text-sm">Nenhuma nota fiscal encontrada.</p>
              <p className="text-xs text-muted-foreground/60">
                Notas são emitidas ao finalizar vendas ou serviços (quando PlugNotas estiver configurado).
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {notas.map((nota) => (
                <NotaRow
                  key={nota.id}
                  nota={nota}
                  onDetail={() => setDetailNota(nota)}
                  onCancel={() => setCancelModal({ open: true, nota })}
                  onRetry={async () => {
                    await api.post(`/fiscal/${nota.id}/reenviar`);
                    carregarNotas();
                  }}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal: Emitir Nota */}
      <Dialog open={emitModal.open} onOpenChange={(v) => setEmitModal((p) => ({ ...p, open: v }))}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Send className="h-5 w-5 text-primary" />
              Emitir {emitModal.tipo.toUpperCase()} Manualmente
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="emit-id" className="text-xs font-bold uppercase">
                {emitModal.tipo === "nfe" ? "ID da Venda (sale_id)" : "ID do Agendamento (appointment_id)"}
              </Label>
              <Input id="emit-id" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" value={emitId} onChange={(e) => setEmitId(e.target.value)} className="font-mono text-sm" />
            </div>
            <div className="p-3 rounded-lg bg-muted/50 text-xs text-muted-foreground space-y-1">
              {emitModal.tipo === "nfe" ? (
                <>
                  <p>✓ CNPJ e endereço do emitente configurados em Configurações → Fiscal</p>
                  <p>✓ Certificado A1 cadastrado no painel PlugNotas</p>
                  <p>✓ CFOP, NCM e CST validados com o contador</p>
                  <p className="text-amber-400 mt-1">O status retornado será <strong>Em processamento</strong>. O status final chega via webhook ou polling.</p>
                </>
              ) : (
                <>
                  <p>✓ Agendamento com status 'Concluído'</p>
                  <p>✓ Inscrição Municipal e código de serviço configurados</p>
                  <p>✓ Alíquota ISS correta para o município</p>
                  <p className="text-amber-400 mt-1">Regras NFS-e variam por município. Confirme com seu contador.</p>
                </>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEmitModal({ open: false, tipo: "nfe" })}>Cancelar</Button>
            <Button onClick={emitirNota} disabled={emitting || !emitId.trim()}>
              {emitting ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <Send className="h-4 w-4 mr-1.5" />}
              Emitir Nota
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Cancelar Nota */}
      <Dialog open={cancelModal.open} onOpenChange={(v) => setCancelModal((p) => ({ ...p, open: v }))}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-500">
              <Ban className="h-5 w-5" /> Cancelar Nota Fiscal
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 space-y-1">
              <p>Esta ação é irreversível. A nota será cancelada junto à SEFAZ/Prefeitura.</p>
              <p>Prazo máximo: <strong>168h após autorização</strong> para NF-e (NFS-e varia por município).</p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cancel-motivo" className="text-xs font-bold uppercase">Justificativa (mín. 15 caracteres)</Label>
              <Input id="cancel-motivo" placeholder="Descreva o motivo do cancelamento..." value={cancelMotivo} onChange={(e) => setCancelMotivo(e.target.value)} />
              <p className="text-[11px] text-muted-foreground">{cancelMotivo.length} / 15 caracteres mínimos</p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCancelModal({ open: false, nota: null })}>Voltar</Button>
            <Button variant="destructive" onClick={cancelarNota} disabled={cancelling || cancelMotivo.length < 15}>
              {cancelling ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <Ban className="h-4 w-4 mr-1.5" />}
              Confirmar Cancelamento
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Detalhes */}
      <Dialog open={!!detailNota} onOpenChange={(v) => !v && setDetailNota(null)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" /> Detalhes da Nota Fiscal
            </DialogTitle>
          </DialogHeader>
          {detailNota && (
            <div className="space-y-4 py-2 text-sm">
              <div className="flex gap-2 flex-wrap">
                <TipoBadge tipo={detailNota.tipo} />
                <StatusBadge status={detailNota.status} />
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <Detail label="Destinatário" value={detailNota.destinatario_nome} />
                <Detail label="CPF/CNPJ" value={detailNota.destinatario_cpf_cnpj} />
                <Detail label="Número" value={detailNota.numero_nota} />
                <Detail label="Série" value={detailNota.serie} />
                <Detail label="Valor Total" value={moeda(detailNota.valor_total)} />
                <Detail label="Emitida em" value={detailNota.created_at ? format(new Date(detailNota.created_at), "dd/MM/yyyy HH:mm", { locale: ptBR }) : "—"} />
                {detailNota.authorized_at && (
                  <Detail label="Autorizada em" value={format(new Date(detailNota.authorized_at), "dd/MM/yyyy HH:mm", { locale: ptBR })} />
                )}
                {detailNota.webhook_recebido_em && (
                  <Detail label="Webhook recebido" value={format(new Date(detailNota.webhook_recebido_em), "dd/MM/yyyy HH:mm", { locale: ptBR })} />
                )}
                {detailNota.tentativas !== null && (
                  <Detail label="Tentativas" value={`${detailNota.tentativas} / ${detailNota.max_tentativas}`} />
                )}
                {detailNota.chave_acesso && (
                  <div className="col-span-2">
                    <p className="text-muted-foreground mb-0.5">Chave de Acesso (44 dígitos)</p>
                    <p className="font-mono text-[10px] break-all bg-muted/50 p-2 rounded">{detailNota.chave_acesso}</p>
                  </div>
                )}
                {detailNota.motivo_rejeicao && (
                  <div className="col-span-2">
                    <p className="text-red-400 mb-0.5 font-bold flex items-center gap-1.5"><AlertCircle className="h-3.5 w-3.5" /> Erro SEFAZ</p>
                    <p className="font-mono text-[10px] bg-red-400/10 p-2 rounded text-red-400/80">{detailNota.motivo_rejeicao}</p>
                    
                    {detailNota.explicacao_ai && (
                      <div className="mt-3 bg-primary/10 border border-primary/20 p-3 rounded-xl space-y-1 animate-in fade-in slide-in-from-top-2">
                        <p className="text-[10px] font-bold text-primary flex items-center gap-1.5 uppercase tracking-wider">
                           <Sparkles className="h-3.5 w-3.5" /> Sugestão da IA
                        </p>
                        <p className="text-sm font-medium leading-relaxed italic">
                          "{detailNota.explicacao_ai}"
                        </p>
                      </div>
                    )}
                  </div>
                )}
                {detailNota.ultimo_erro && (
                  <div className="col-span-2">
                    <p className="text-orange-400 mb-0.5">Último erro de comunicação</p>
                    <p className="text-orange-400/80 text-[11px]">{detailNota.ultimo_erro}</p>
                  </div>
                )}
              </div>
              <div className="flex gap-2 flex-wrap pt-2">
                {detailNota.danfe_url && (
                  <a href={detailNota.danfe_url} target="_blank" rel="noreferrer">
                    <Button size="sm" variant="outline"><Download className="h-3.5 w-3.5 mr-1.5" /> DANFE (PDF)</Button>
                  </a>
                )}
                {detailNota.xml_url && (
                  <a href={detailNota.xml_url} target="_blank" rel="noreferrer">
                    <Button size="sm" variant="outline"><ExternalLink className="h-3.5 w-3.5 mr-1.5" /> XML</Button>
                  </a>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function KpiCard({ label, value, icon, color }: { label: string; value: string; icon: React.ReactNode; color: string; }) {
  const bg: Record<string, string> = {
    emerald: "from-emerald-500/10 to-emerald-500/5 border-emerald-500/20",
    blue: "from-blue-500/10 to-blue-500/5 border-blue-500/20",
    amber: "from-amber-500/10 to-amber-500/5 border-amber-500/20",
    red: "from-red-500/10 to-red-500/5 border-red-500/20",
  };
  return (
    <div className={`rounded-xl border bg-gradient-to-br ${bg[color] || ""} p-4 flex flex-col gap-2`}>
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">{label}</p>
        {icon}
      </div>
      <p className="text-xl font-bold">{value}</p>
    </div>
  );
}

function NotaRow({
  nota,
  onDetail,
  onCancel,
  onRetry,
}: {
  nota: NotaFiscal;
  onDetail: () => void;
  onCancel: () => void;
  onRetry: () => Promise<void>;
}) {
  const [retrying, setRetrying] = useState(false);

  const handleRetry = async () => {
    setRetrying(true);
    try {
      await onRetry();
      toast.success("Nota reenviada ao PlugNotas.");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Erro ao reenviar.");
    } finally {
      setRetrying(false);
    }
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between px-5 py-4 gap-3 hover:bg-muted/30 transition-colors">
      <div className="flex items-start gap-3 min-w-0">
        <div className="shrink-0 mt-0.5"><TipoBadge tipo={nota.tipo} /></div>
        <div className="min-w-0">
          <p className="text-sm font-semibold truncate">{nota.destinatario_nome || "Consumidor Final"}</p>
          <p className="text-xs text-muted-foreground truncate">{nota.descricao}</p>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            {nota.created_at ? format(new Date(nota.created_at), "dd/MM/yyyy HH:mm", { locale: ptBR }) : ""}
            {nota.numero_nota && ` · Nº ${nota.numero_nota}`}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        <div className="text-right hidden sm:block">
          <p className="text-sm font-bold">{moeda(nota.valor_total)}</p>
          <StatusBadge status={nota.status} />
        </div>
        <div className="flex gap-1">
          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={onDetail} title="Ver detalhes">
            <Info className="h-4 w-4" />
          </Button>
          {nota.danfe_url && (
            <a href={nota.danfe_url} target="_blank" rel="noreferrer">
              <Button size="icon" variant="ghost" className="h-8 w-8" title="Baixar DANFE">
                <Download className="h-4 w-4" />
              </Button>
            </a>
          )}
          {nota.status === "error" && (
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8 text-orange-400 hover:text-orange-500"
              onClick={handleRetry}
              disabled={retrying || (nota.tentativas ?? 0) >= (nota.max_tentativas ?? 3)}
              title={`Reenviar (${nota.tentativas ?? 0}/${nota.max_tentativas ?? 3} tentativas)`}
            >
              {retrying ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
            </Button>
          )}
          {nota.status === "authorized" && (
            <Button
              size="icon"
              variant="ghost"
              className="h-8 w-8 text-red-400 hover:text-red-500"
              onClick={onCancel}
              title="Cancelar nota"
            >
              <Ban className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <p className="text-muted-foreground mb-0.5">{label}</p>
      <p className="font-medium">{value || "—"}</p>
    </div>
  );
}

export default Fiscal;
