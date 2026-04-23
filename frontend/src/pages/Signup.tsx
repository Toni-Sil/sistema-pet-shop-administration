import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { api } from "@/lib/api";

export default function Signup() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    storeName: "",
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password !== form.confirmPassword) {
      toast.error("As senhas não coincidem.");
      return;
    }
    setLoading(true);
    try {
      await api.post("/auth/register", {
        store_name: form.storeName,
        name: form.name,
        email: form.email,
        password: form.password,
      });
      toast.success("Conta criada! Faça login para continuar.");
      navigate("/login");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Erro ao criar conta.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center animated-gradient p-4">
      <div className="w-full max-w-md p-8 pt-10 space-y-6 glass-panel rounded-2xl animate-fade-in relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/20 rounded-full blur-2xl -mt-10 -mr-10"></div>
        <div className="absolute bottom-0 left-0 w-32 h-32 bg-accent/20 rounded-full blur-2xl -mb-10 -ml-10"></div>
        
        <div className="text-center relative z-10">
          <h1 className="text-2xl font-bold tracking-tight text-foreground font-heading">Criar uma conta</h1>
          <p className="text-sm text-muted-foreground mt-2">Configure sua loja em minutos</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 relative z-10">
          <div className="space-y-2">
            <Label htmlFor="storeName">Nome da sua Pet Shop *</Label>
            <Input
              id="storeName"
              placeholder="Pet Shop das Estrelas"
              required
              value={form.storeName}
              onChange={set("storeName")}
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="name">Seu nome *</Label>
            <Input
              id="name"
              placeholder="Maria Silva"
              required
              value={form.name}
              onChange={set("name")}
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">E-mail *</Label>
            <Input
              id="email"
              type="email"
              placeholder="maria@petshop.com"
              required
              value={form.email}
              onChange={set("email")}
              disabled={loading}
              autoComplete="email"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="password">Senha *</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                required
                value={form.password}
                onChange={set("password")}
                disabled={loading}
                autoComplete="new-password"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirmar senha *</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                required
                value={form.confirmPassword}
                onChange={set("confirmPassword")}
                disabled={loading}
                autoComplete="new-password"
              />
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Criando conta..." : "Criar conta"}
          </Button>
        </form>

        <p className="text-center text-sm text-gray-500">
          Já tem uma conta?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Fazer login
          </Link>
        </p>
      </div>
    </div>
  );
}
