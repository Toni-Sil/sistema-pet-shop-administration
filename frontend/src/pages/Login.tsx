import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { api } from "@/lib/api";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setEmail("");
    setPassword("");
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await api.post("/auth/login", { email, password });

      localStorage.setItem("token", response.data.access_token);
      toast.success("Login realizado com sucesso!");
      navigate("/"); // Dashboard
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Erro ao realizar login. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full items-center justify-center animated-gradient p-4">
      <div className="w-full max-w-md p-8 space-y-6 glass-panel rounded-2xl animate-fade-in relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/20 rounded-full blur-2xl -mt-10 -mr-10"></div>
        <div className="absolute bottom-0 left-0 w-32 h-32 bg-accent/20 rounded-full blur-2xl -mb-10 -ml-10"></div>

        <div className="text-center relative z-10">
          <div className="mb-4 flex flex-col items-center justify-center">
            <img src="/ATPetShop.jpeg" alt="Auto Tech Lith pet shop system" className="max-h-24 w-auto object-contain mx-auto rounded-lg shadow-sm" />
          </div>
          <h1 className="text-2xl font-heading font-bold tracking-tight text-foreground">Auto Tech Lith pet shop system</h1>
          <p className="text-sm text-muted-foreground mt-2">Acesse sua conta para continuar</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4 relative z-10">
          <div className="space-y-2">
            <Label htmlFor="login_email_input">E-mail</Label>
            <Input
              id="login_email_input"
              type="email"
              placeholder=""
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
              autoComplete="new-password"
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="login_password_input">Senha</Label>
            <Input
              id="login_password_input"
              type="password"
              placeholder=""
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
              autoComplete="new-password"
              className="w-full"
            />
          </div>

          <Button type="submit" className="w-full transition-all" disabled={loading}>
            {loading ? "Entrando..." : "Entrar"}
          </Button>
        </form>

        <p className="text-center text-sm text-gray-500">
          Não tem conta?{" "}
          <a href="/cadastro" className="font-medium text-primary hover:underline">
            Criar minha pet shop agora
          </a>
        </p>
      </div>
    </div>
  );
}
