import os
from sqlalchemy.orm import Session
from uuid import UUID
import json

from app.services.ai_tools import ai_tools
from app.schemas.ai import ChatRequest, ChatResponse

# System Prompts para cada Agente
SYSTEM_PROMPTS = {
    "orchestrator": """Você é o Orquestrador do Pet Shop. Sua função é receber pedidos do usuário e decidir qual especialista deve responder.
    Especialistas:
    - inventory: Para dúvidas sobre estoque, falta de produtos.
    - financial: Para faturamento, lucros e gastos.
    - scheduling: Para agenda, banhos e tosas do dia.
    - crm: Para histórico de pets, vacinas e clientes.
    
    Se o usuário pedir algo genérico, responda você mesmo. Se for específico, cite qual agente está cuidando disso.""",
    
    "inventory": "Você é o Agente de Estoque. Analise os níveis de produtos e sugira reposições.",
    "financial": "Você é o Agente Financeiro. Ajude o dono a entender a saúde do negócio.",
    "scheduling": "Você é o Agente de Agendamento. Organize a agenda e evite conflitos.",
    "crm": "Você é o Agente de Relacionamento. Foco na saúde dos pets e fidelidade dos clientes."
}

class AIService:
    def __init__(self):
        # Para ativar o Gemini real:
        # import google.generativeai as genai
        # genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # self.model = genai.GenerativeModel('gemini-1.5-flash')
        pass

    async def process_chat(self, db: Session, store_id: UUID, request: ChatRequest):
        msg = request.message.lower()
        
        # Lógica de Roteamento Avançada
        target_agent = "orchestrator"
        tool_data = None
        suggestions = ["Ver estoque baixo", "Resumo financeiro", "Agenda de hoje"]
        
        # Detecção de intenção
        if any(w in msg for w in ["estoque", "produto", "repor", "falta", "comprar"]):
            target_agent = "inventory"
            tool_data = ai_tools.get_stock_levels(db, store_id)
            suggestions = ["Produtos mais vendidos", "Custo de reposição"]
            
        elif any(w in msg for w in ["faturamento", "dinheiro", "venda", "ganhei", "lucro", "financeiro"]):
            target_agent = "financial"
            tool_data = ai_tools.get_financial_summary(db, store_id)
            suggestions = ["Despesas do mês", "Ticket médio detalhado"]
            
        elif any(w in msg for w in ["agenda", "hoje", "compromisso", "marcado", "banho", "tosa"]):
            target_agent = "scheduling"
            tool_data = ai_tools.get_todays_appointments(db, store_id)
            suggestions = ["Ver amanhã", "Horários livres"]
            
        elif any(w in msg for w in ["vacina", "vencendo", "dose", "pet", "saúde", "histórico"]):
            target_agent = "crm"
            tool_data = ai_tools.get_upcoming_vaccines(db, store_id)
            suggestions = ["Pets sem visita há 30 dias", "Lembrar tutores"]

        # Respostas dos Agentes Especialistas
        response_text = ""
        
        if target_agent == "inventory":
            if tool_data:
                items = ", ".join([f"*{i['nome']}* ({i['estoque']} em estoque)" for i in tool_data])
                response_text = f"📦 **[Agente de Estoque]**: Olá! Fiz uma varredura e identifiquei que {len(tool_data)} itens estão em nível crítico: {items}. Recomendo a reposição imediata para evitar rupturas de vendas."
            else:
                response_text = "📦 **[Agente de Estoque]**: Ótimas notícias! Realizei a conferência e todos os seus produtos estão com níveis saudáveis de estoque. Nada para se preocupar por agora."
        
        elif target_agent == "financial":
            response_text = (
                f"💰 **[Agente Financeiro]**: Analisei o caixa. Até o momento, o faturamento total é de **R$ {tool_data['faturamento_total']:.2f}**.\n\n"
                f"📈 **Indicadores:**\n"
                f"- Volume: {tool_data['total_vendas']} vendas realizadas.\n"
                f"- Ticket Médio: R$ {tool_data['ticket_medio']:.2f}.\n"
                "A saúde financeira está estável. Deseja ver a projeção para o fim do mês?"
            )
            
        elif target_agent == "scheduling":
            if tool_data:
                count = len(tool_data)
                next_app = tool_data[0]
                response_text = (
                    f"📅 **[Agente de Agendamento]**: Você tem **{count}** compromissos agendados para hoje.\n"
                    f"⏰ O próximo atendimento é o pet **{next_app['pet']}** ({next_app['servico']}) marcado para as **{next_app['hora']}**.\n"
                    "Deseja que eu separe os materiais necessários para esses serviços?"
                )
            else:
                response_text = "📅 **[Agente de Agendamento]**: Sua agenda para hoje está livre. É um bom momento para realizar manutenções ou focar em campanhas de fidelização."

        elif target_agent == "crm":
            if tool_data:
                vax_list = "\n".join([f"- **{v['pet']}**: {v['vacina']} ({v['data']})" for v in tool_data])
                response_text = (
                    f"🩺 **[Agente de CRM]**: Identifiquei pets com vacinas vencendo nos próximos 7 dias:\n{vax_list}\n"
                    "Posso gerar as mensagens de lembrete para os tutores no WhatsApp?"
                )
            else:
                response_text = "🩺 **[Agente de CRM]**: Todos os pets da casa estão com as vacinas em dia para a próxima semana. Ótimo trabalho de acompanhamento!"
        
        else:
            response_text = (
                "👋 Olá! Sou o **Orquestrador da sua IA**. Meu papel é garantir que seu Pet Shop rode com máxima eficiência.\n\n"
                "Posso chamar meus especialistas para ajudar com:\n"
                "- **Estoque** (repor produtos)\n"
                "- **Financeiro** (lucros e vendas)\n"
                "- **Agenda** (limpeza e horários)\n"
                "- **CRM** (saúde e vacinas)\n\n"
                "O que vamos analisar agora?"
            )

        return ChatResponse(
            response=response_text,
            agent_id=target_agent,
            suggestions=suggestions
        )

ai_service = AIService()
