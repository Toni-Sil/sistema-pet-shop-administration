import { ReactNode, useState, useEffect } from "react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { AIChat } from "@/components/AIChat";
import { AIGuide } from "@/components/AIGuide";
import { POSModal } from "@/components/POSModal";
import { Button } from "@/components/ui/button";
import { Plus, CalendarPlus, User, ChevronDown } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { VoiceCommander } from "@/components/VoiceCommander";

import { useNavigate, useLocation } from "react-router-dom";
import {
  DropdownMenu,

  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [isPOSOpen, setIsPOSOpen] = useState(false);


  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          {/* ... breadcrumbs or header ... */}
          <header className="h-14 flex items-center border-b border-border/50 bg-background/60 backdrop-blur-md px-4 gap-3 flex-shrink-0 sticky top-0 z-10 transition-all">
            <SidebarTrigger className="mr-1" />


            <div className="flex-1" />

            <ThemeToggle />

            <Button size="sm" variant="outline" onClick={() => setIsPOSOpen(true)} className="hidden sm:flex">
              <Plus className="h-4 w-4 mr-1.5" />
              Nova venda
            </Button>


            {/* User avatar */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2 hover:bg-secondary rounded-lg px-2 py-1.5 transition-colors">
                  <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                    <User className="h-4 w-4 text-primary-foreground" />
                  </div>
                  <ChevronDown className="h-3 w-3 text-muted-foreground hidden sm:block" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => navigate("/configuracoes")}>
                  Configurações
                </DropdownMenuItem>
                <DropdownMenuItem>Sair</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </header>

          <main className="flex-1 overflow-auto p-4 md:p-6">
            {children}
          </main>
        </div>
      </div>
      <AIChat />
      <AIGuide />
      <POSModal open={isPOSOpen} onOpenChange={setIsPOSOpen} />
      <VoiceCommander />

    </SidebarProvider>
  );
}
