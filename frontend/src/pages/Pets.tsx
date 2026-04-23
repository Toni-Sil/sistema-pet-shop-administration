import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { PawPrint, Search, Plus, ArrowDown, ArrowUp, Filter } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface Pet {
  id: string;
  name: string;
  species: string;
  breed?: string;
  weight?: string;
  client_id: string;
}

interface Client {
  id: string;
  name: string;
  pets: Pet[];
}

const speciesLabel: Record<string, string> = {
  dog: "Cão",
  cat: "Gato",
  bird: "Pássaro",
  other: "Outro",
};

const Pets = () => {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [speciesFilter, setSpeciesFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"name" | "tutor">("name");
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  // form
  const [clientId, setClientId] = useState("");
  const [petName, setPetName] = useState("");
  const [species, setSpecies] = useState("dog");
  const [breed, setBreed] = useState("");
  const [weight, setWeight] = useState("");

  const loadPets = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/clientes?limit=100");
      setClients(data);
    } catch {
      toast.error("Erro ao carregar pets.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadPets(); }, []);

  const allPets = clients.flatMap((c) =>
    c.pets.map((p) => ({ ...p, tutorName: c.name }))
  );

  const speciesOptions = useMemo(() => {
    const set = new Set<string>(["all"]);
    allPets.forEach((p) => {
      if (p.species) set.add(p.species);
    });
    return Array.from(set).sort();
  }, [allPets]);

  const filtered = useMemo(() => {
    let result = [...allPets];
    const term = search.trim().toLowerCase();
    if (term) {
      result = result.filter(
        (p) =>
          p.name.toLowerCase().includes(term) ||
          p.tutorName.toLowerCase().includes(term)
      );
    }
    if (speciesFilter && speciesFilter !== "all") {
      result = result.filter((p) => p.species === speciesFilter);
    }
    if (sortBy === "name") {
      result.sort((a, b) => a.name.localeCompare(b.name));
    } else if (sortBy === "tutor") {
      result.sort((a, b) => a.tutorName.localeCompare(b.tutorName));
    }
    return result;
  }, [allPets, search, speciesFilter, sortBy]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/clientes/${clientId}/pets`, {
        name: petName,
        species,
        breed: breed || undefined,
        weight: weight || undefined,
      });
      toast.success("Pet cadastrado!");
      setIsOpen(false);
      setPetName(""); setBreed(""); setWeight(""); setClientId("");
      loadPets();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erro ao salvar pet.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-heading font-bold">Pets</h1>
          <p className="text-muted-foreground mt-1">
            {allPets.length} pet(s) cadastrado(s)
          </p>
        </div>
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-1.5" /> Cadastrar pet
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Novo Pet</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Tutor (Cliente) *</Label>
                <select 
                  required 
                  className="w-full flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-primary" 
                  value={clientId} 
                  onChange={e => setClientId(e.target.value)}
                >
                  <option value="">Selecione o tutor</option>
                  {clients.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label>Nome do Pet *</Label>
                <Input required value={petName} onChange={e => setPetName(e.target.value)} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Espécie</Label>
                  <select
                    className="w-full flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={species}
                    onChange={e => setSpecies(e.target.value)}
                  >
                    <option value="dog">Cão</option>
                    <option value="cat">Gato</option>
                    <option value="bird">Pássaro</option>
                    <option value="other">Outro</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Raça</Label>
                  <Input value={breed} onChange={e => setBreed(e.target.value)} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Peso</Label>
                <Input placeholder="ex: 5kg" value={weight} onChange={e => setWeight(e.target.value)} />
              </div>
              <Button type="submit" className="w-full" disabled={saving}>
                {saving ? "Salvando..." : "Cadastrar pet"}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex flex-col sm:flex-row gap-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar pet (nome do pet ou do tutor)"
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <select
            value={speciesFilter}
            onChange={(e) => setSpeciesFilter(e.target.value)}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm focus:ring-1 focus:ring-primary outline-none"
          >
            {speciesOptions.map((s) => (
              <option key={s} value={s}>
                {s === "all" ? "Todas espécies" : speciesLabel[s] || s}
              </option>
            ))}
          </select>
          <button
            onClick={() => setSortBy((prev) => (prev === "name" ? "tutor" : "name"))}
            className="h-10 px-3 rounded-md border border-input bg-background text-sm flex items-center gap-1 hover:bg-muted/40 transition-colors"
            title={sortBy === "name" ? "Ordenar por tutor" : "Ordenar por nome"}
          >
            {sortBy === "name" ? (
              <><ArrowDown className="h-4 w-4" /> Nome A-Z</>
            ) : (
              <><ArrowUp className="h-4 w-4" /> Tutor A-Z</>
            )}
          </button>
        </div>
      </div>

      <Card className="glass-card shadow-lg">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3].map(i => <Skeleton key={i} className="h-14 w-full rounded" />)}
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-12 text-center flex flex-col items-center">
              <PawPrint className="h-10 w-10 text-muted-foreground/40 mb-3" />
              <p className="text-muted-foreground mb-4">
                {search ? "Nenhum pet encontrado." : "Nenhum pet cadastrado ainda."}
              </p>
              {!search && (
                <Button onClick={() => setIsOpen(true)} variant="outline">
                  Cadastrar meu primeiro pet
                </Button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="p-4">Nome</th>
                    <th className="p-4">Tutor</th>
                    <th className="p-4">Espécie</th>
                    <th className="p-4">Raça</th>
                    <th className="p-4">Peso</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((p) => (
                    <tr 
                      key={p.id} 
                      className="border-b last:border-0 hover:bg-muted/30 cursor-pointer transition-colors"
                      onClick={() => navigate(`/pets/${p.id}`)}
                    >
                      <td className="p-4 font-medium">
                        <span className="flex items-center gap-2">
                          <PawPrint className="h-4 w-4 text-primary flex-shrink-0" />
                          {p.name}
                        </span>
                      </td>
                      <td className="p-4">{(p as any).tutorName}</td>
                      <td className="p-4">{speciesLabel[p.species] ?? p.species}</td>
                      <td className="p-4 text-muted-foreground">{p.breed || "—"}</td>
                      <td className="p-4 text-muted-foreground">{p.weight || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Pets;
