import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Trash2, Package, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";

interface Service {
  id: string;
  name: string;
  price: number;
}

interface PackageItem {
  service_id: string;
  quantity: number;
}

const PackageManager = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [packages, setPackages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Create Package State
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [selectedItems, setSelectedItems] = useState<PackageItem[]>([]);

  const loadData = async () => {
    try {
      const [sRes, pRes] = await Promise.all([
        api.get("/services"),
        api.get("/pacotes")
      ]);
      setServices(sRes.data);
      setPackages(pRes.data);
    } catch {
      toast.error("Erro ao carregar dados de pacotes.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleAddItem = () => {
    if (services.length > 0) {
      setSelectedItems([...selectedItems, { service_id: services[0].id, quantity: 4 }]);
    }
  };

  const handleRemoveItem = (index: number) => {
    setSelectedItems(selectedItems.filter((_, i) => i !== index));
  };

  const updateItem = (index: number, field: keyof PackageItem, value: any) => {
    const next = [...selectedItems];
    next[index] = { ...next[index], [field]: value };
    setSelectedItems(next);
  };

  const handleCreate = async () => {
    if (!name || !price || selectedItems.length === 0) {
      toast.error("Preencha todos os campos do pacote.");
      return;
    }

    try {
      await api.post("/pacotes", {
        name,
        price: parseFloat(price),
        items: selectedItems
      });
      toast.success("Pacote criado com sucesso!");
      setName("");
      setPrice("");
      setSelectedItems([]);
      loadData();
    } catch {
      toast.error("Erro ao criar pacote.");
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Plus className="h-5 w-5 text-primary" /> Criar Novo Pacote
          </CardTitle>
          <CardDescription>Defina um nome, preço promocional e a quantidade de serviços incluídos.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Nome do Pacote</Label>
              <Input value={name} onChange={e => setName(e.target.value)} placeholder="Ex: Combo 4 Banhos P" />
            </div>
            <div className="space-y-2">
              <Label>Preço do Pacote (R$)</Label>
              <Input type="number" value={price} onChange={e => setPrice(e.target.value)} placeholder="180.00" />
            </div>
          </div>

          <div className="space-y-3">
            <Label className="text-xs uppercase font-black text-muted-foreground">Serviços Inclusos</Label>
            {selectedItems.map((item, idx) => (
              <div key={idx} className="flex items-center gap-3 bg-muted/20 p-2 rounded-xl border">
                <select 
                  className="flex-1 bg-transparent text-sm outline-none"
                  value={item.service_id}
                  onChange={e => updateItem(idx, 'service_id', e.target.value)}
                >
                  {services.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
                <div className="flex items-center gap-2">
                  <Label className="text-[10px] uppercase">Qtd:</Label>
                  <Input 
                    type="number" 
                    className="w-16 h-8 text-xs" 
                    value={item.quantity} 
                    onChange={e => updateItem(idx, 'quantity', parseInt(e.target.value))} 
                  />
                </div>
                <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => handleRemoveItem(idx)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button variant="outline" size="sm" className="w-full border-dashed" onClick={handleAddItem}>
              <Plus className="h-3 w-3 mr-1" /> Adicionar Serviço ao Pacote
            </Button>
          </div>

          <Button className="w-full" onClick={handleCreate}>Criar Pacote</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Package className="h-5 w-5 text-primary" /> Pacotes Ativos
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p>Carregando...</p>
          ) : packages.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">Nenhum pacote cadastrado.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {packages.map(p => (
                <div key={p.id} className="p-4 rounded-2xl border bg-card hover:shadow-md transition-all">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-bold">{p.name}</h4>
                    <Badge variant="secondary">R$ {Number(p.price).toFixed(2)}</Badge>
                  </div>
                  <div className="space-y-1">
                    {p.items?.map((item: any, idx: number) => (
                      <div key={idx} className="flex items-center gap-2 text-xs text-muted-foreground">
                        <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                        {item.quantity}x {item.service?.name || "Serviço"}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PackageManager;
