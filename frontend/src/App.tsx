import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Layout } from "@/components/Layout";
import { PrivateRoute } from "@/components/PrivateRoute";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Index from "./pages/Index";
import Services from "./pages/Services";
import Shop from "./pages/Shop";
import Clients from "./pages/Clients";
import Pets from "./pages/Pets";
import Reports from "./pages/Reports";
import Financeiro from "./pages/Financeiro";
import Settings from "./pages/Settings";
import NewAppointment from "./pages/NewAppointment";
import POS from "./pages/POS";
import PetProfile from "./pages/PetProfile";
import ServiceManagement from "./pages/ServiceManagement";
import PublicBooking from "./pages/PublicBooking";
import Fiscal from "./pages/Fiscal";
import Hotel from "./pages/Hotel";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <ThemeProvider defaultTheme="system" enableSystem attribute="class" storageKey="app-theme">
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            {/* Rotas públicas */}
            <Route path="/login" element={<Login />} />
            <Route path="/cadastro" element={<Signup />} />
            <Route path="/agendar/:slug" element={<PublicBooking />} />

            {/* Rotas protegidas */}
            <Route path="/" element={<PrivateRoute><Layout><Index /></Layout></PrivateRoute>} />
            <Route path="/servicos" element={<PrivateRoute><Layout><Services /></Layout></PrivateRoute>} />
            <Route path="/servicos/gerenciar" element={<PrivateRoute><Layout><ServiceManagement /></Layout></PrivateRoute>} />
            <Route path="/servicos/novo-agendamento" element={<PrivateRoute><Layout><NewAppointment /></Layout></PrivateRoute>} />
            <Route path="/estoque" element={<PrivateRoute><Layout><Shop /></Layout></PrivateRoute>} />
            <Route path="/loja" element={<PrivateRoute><Layout><Shop /></Layout></PrivateRoute>} />
            <Route path="/caixa" element={<PrivateRoute><Layout><POS /></Layout></PrivateRoute>} />
            <Route path="/clientes" element={<PrivateRoute><Layout><Clients /></Layout></PrivateRoute>} />
            <Route path="/pets" element={<PrivateRoute><Layout><Pets /></Layout></PrivateRoute>} />
            <Route path="/pets/:id" element={<PrivateRoute><Layout><PetProfile /></Layout></PrivateRoute>} />
            <Route path="/relatorios" element={<PrivateRoute><Layout><Reports /></Layout></PrivateRoute>} />
            <Route path="/financeiro" element={<PrivateRoute><Layout><Financeiro /></Layout></PrivateRoute>} />
            <Route path="/fiscal" element={<PrivateRoute><Layout><Fiscal /></Layout></PrivateRoute>} />
            <Route path="/hotel" element={<PrivateRoute><Layout><Hotel /></Layout></PrivateRoute>} />
            <Route path="/configuracoes" element={<PrivateRoute><Layout><Settings /></Layout></PrivateRoute>} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  </ThemeProvider>
);

export default App;
