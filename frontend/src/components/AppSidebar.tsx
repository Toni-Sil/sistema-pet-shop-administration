import { Home, Calendar, ShoppingCart, Users, PawPrint, BarChart3, Settings, CreditCard, DollarSign, FileText, Hotel } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useLocation } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

const menuItems = [
  { id: "nav-inicio", title: "Início", url: "/", icon: Home },
  { id: "nav-agenda", title: "Agenda", url: "/servicos", icon: Calendar },
  { id: "nav-caixa", title: "Caixa (PDV)", url: "/caixa", icon: CreditCard },
  { id: "nav-financeiro", title: "Financeiro", url: "/financeiro", icon: DollarSign },
  { id: "nav-estoque", title: "Estoque", url: "/estoque", icon: ShoppingCart },
  { id: "nav-clientes", title: "Clientes", url: "/clientes", icon: Users },
  { id: "nav-pets", title: "Pets", url: "/pets", icon: PawPrint },
  { id: "nav-hotel", title: "Hotel / Creche", url: "/hotel", icon: Hotel },
  { id: "nav-relatorios", title: "Relatórios", url: "/relatorios", icon: BarChart3 },
  { id: "nav-fiscal", title: "Notas Fiscais", url: "/fiscal", icon: FileText },
  { id: "nav-configuracoes", title: "Configurações", url: "/configuracoes", icon: Settings },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const location = useLocation();

  return (
    <Sidebar collapsible="icon">
      <SidebarContent className="pt-4">
        <div className="px-4 pb-4 mb-2 border-b border-sidebar-border">
          <div className="flex items-center gap-2">
            {collapsed ? (
              <img src="/ATPetShop.jpeg" alt="Auto Tech Lith pet shop system" className="h-8 w-8 object-cover rounded-md flex-shrink-0" />
            ) : (
              <img src="/ATPetShop.jpeg" alt="Auto Tech Lith pet shop system" className="h-8 w-auto max-w-[40px] object-contain rounded-md flex-shrink-0" />
            )}
            {!collapsed && (
              <span className="font-heading text-sm font-bold text-sidebar-foreground truncate" title="Auto Tech Lith pet shop system">
                Auto Tech Lith
              </span>
            )}
          </div>
        </div>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      id={item.id}
                      to={item.url}
                      end={item.url === "/"}
                      className="hover:bg-sidebar-accent/50"
                      activeClassName="bg-sidebar-accent text-sidebar-primary font-medium"
                    >
                      <item.icon className="mr-2 h-5 w-5 flex-shrink-0" />
                      {!collapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
