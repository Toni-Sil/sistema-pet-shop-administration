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


def resolve_agent_model(ai_agents_config: dict, target_agent: str, default_model: str = "gpt-4o-mini") -> str:
    agent_cfg = ai_agents_config.get(target_agent)
    if isinstance(agent_cfg, str) and agent_cfg:
        return agent_cfg

    if isinstance(agent_cfg, dict):
        model = agent_cfg.get("model")
        if isinstance(model, str) and model.strip():
            return model.strip()

    return default_model

class AIService:
    def __init__(self):
        # Para ativar o Gemini real:
        # import google.generativeai as genai
        # genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        # self.model = genai.GenerativeModel('gemini-1.5-flash')
        pass

    async def process_chat(self, db: Session, store_id: UUID, request: ChatRequest):
        from app.models.store import Store
        store = db.query(Store).filter(Store.id == store_id).first()
        ai_agents_config = store.settings.get("ai_agents", {}) if store.settings else {}
        
        msg = request.message.lower()
        
        # Lógica de Roteamento Avançada
        target_agent = "orchestrator"
        tool_data = None
        suggestions = ["Ver estoque baixo", "Resumo financeiro", "Agenda de hoje"]
        actions = []
        
        # Detecção de intenção
        if any(w in msg for w in ["estoque", "produto", "repor", "falta", "comprar"]):
            target_agent = "inventory"
            tool_data = ai_tools.get_stock_levels(db, store_id)
            suggestions = ["Produtos mais vendidos", "Custo de reposição"]
            # Seleciona o primeiro item crítico para apontar no layout se o usuário já estiver na página
            critical_id = tool_data[0]['id'] if tool_data and 'id' in tool_data[0] else None
            # Nova lógica preditiva integrada
            predictions = ai_tools.get_inventory_predictions(db, store_id)
            tool_data = predictions if predictions else tool_data
            
            actions = [{"label": "📦 Ver Estoque", "type": "navigate", "payload": "/estoque", "target_selector": f"#product-{critical_id}" if critical_id else "#nav-estoque"}]
            
        elif any(w in msg for w in ["faturamento", "dinheiro", "venda", "ganhei", "lucro", "financeiro"]):
            target_agent = "financial"
            tool_data = ai_tools.get_financial_summary(db, store_id)
            suggestions = ["Despesas do mês", "Ticket médio detalhado"]
            actions = [{"label": "📊 Ver Relatórios", "type": "navigate", "payload": "/relatorios", "target_selector": "#nav-relatorios"}]
            
        elif any(w in msg for w in ["agenda", "hoje", "compromisso", "marcado", "banho", "tosa"]):
            target_agent = "scheduling"
            tool_data = ai_tools.get_todays_appointments(db, store_id)
            suggestions = ["Ver amanhã", "Horários livres"]
            actions = [{"label": "📅 Ver Agenda", "type": "navigate", "payload": "/agendamentos", "target_selector": "#nav-agenda"}]
            
        elif any(w in msg for w in ["vacina", "vencendo", "dose", "pet", "saúde", "histórico"]):
            target_agent = "crm"
            tool_data = ai_tools.get_upcoming_vaccines(db, store_id)
            suggestions = ["Pets sem visita há 30 dias", "Lembrar tutores"]
            actions = [
                {"label": "🐾 Ver Pets", "type": "navigate", "payload": "/pets", "target_selector": f"#nav-pets"},
                {"label": "📲 Notificar WhatsApp", "type": "whatsapp", "payload": {"phone": "5511999999999", "message": "Olá! Notei que a vacina do seu pet está vencendo."}}
            ]
            
        # NOVAS INTENÇÕES DE VOZ (SUPER SMART ACTIONS)
        elif any(w in msg for w in ["registrar venda", "nova venda", "vender"]):
            target_agent = "financial"
            response_text = "💳 **Comando de Voz**: Entendido! Estou abrindo o módulo de vendas para você. Como deseja proceder?"
            actions = [{"label": "🚀 Abrir Caixa", "type": "navigate", "payload": "/caixa"}]
            if "pix" in msg:
                response_text = "💳 **Comando de Voz**: Iniciando venda via **PIX**. O módulo de pagamento automático já foi sinalizado."
                actions.append({"label": "💠 Iniciar Pix", "type": "payment_start", "payload": "pix"})
            
        elif any(w in msg for w in ["agendar", "marcar", "reservar"]):
            target_agent = "scheduling"
            response_text = "📅 **Comando de Voz**: Abrindo o assistente de agendamento. O que deseja agendar?"
            actions = [{"label": "📅 Novo Agendamento", "type": "navigate", "payload": "/servicos/novo-agendamento"}]
            
            # Tenta identificar o tipo
            if "entrega" in msg:
                response_text = "📅 **Comando de Voz**: Entendido. Iniciando agendamento de **Entrega de Material**."
                actions = [{"label": "📅 Agendar Entrega", "type": "navigate", "payload": "/servicos/novo-agendamento?type=entrega"}]
            elif "recebimento" in msg or "mercadoria" in msg:
                response_text = "📅 **Comando de Voz**: Entendido. Iniciando agendamento de **Recebimento de Mercadoria**."
                actions = [{"label": "📅 Agendar Recebimento", "type": "navigate", "payload": "/servicos/novo-agendamento?type=recebimento"}]
            else:
                # Tenta identificar o pet (ex: "agendar para o Bono")
                pets_known = ["bono", "thor", "mel", "luna", "amora"]
                found_pet = next((p for p in pets_known if p in msg), None)
                if found_pet:
                    response_text = f"📅 **Comando de Voz**: Iniciando agendamento direto para o **{found_pet.title()}**. Qual serviço deseja realizar?"
                    actions = [{"label": f"📅 Agendar {found_pet.title()}", "type": "navigate", "payload": f"/servicos/novo-agendamento?pet={found_pet}"}]

        elif any(w in msg for w in ["comprar", "repor", "faltando"]):
            target_agent = "inventory"
            response_text = "📦 **Comando de Voz**: Entendido. Abrindo a gestão de estoque e ativando a inteligência de reposição."
            actions = [{"label": "📦 Ver Inventário", "type": "navigate", "payload": "/estoque"}]
            if "ração" in msg:
                 response_text = "📦 **Comando de Voz**: Verificando estoque de **Rações**. O item mais crítico já está selecionado."
                 actions = [{"label": "📦 Repor Ração", "type": "navigate", "payload": "/estoque?category=Ração"}]

        elif any(w in msg for w in ["relatório", "faturamento", "quanto ganhei"]):
            target_agent = "financial"
            response_text = "📊 **Comando de Voz**: Gerando relatório financeiro instantâneo. Veja os números na tela."
            actions = [{"label": "📊 Ver Relatórios", "type": "navigate", "payload": "/relatorios"}]

        # Identifica o modelo configurado para o agente alvo
        used_model = resolve_agent_model(ai_agents_config, target_agent)

        # Respostas dos Agentes Especialistas
        response_text = ""
        
        if target_agent == "inventory":
            if tool_data:
                # Resposta rica com previsões
                items_list = []
                for i in tool_data[:5]: # Mostrar top 5 críticos
                    dias = i.get('dias_restantes', 0)
                    aviso = f"acaba em **{dias} dias**" if dias > 0 else "estoque **esgotado**"
                    items_list.append(f"- **{i['nome']}**: {aviso} (Sugerido comprar: {i['sugestao_compra']} un)")
                
                resumo = "\n".join(items_list)
                response_text = (
                    f"📦 **[Agente de Estoque Semiautônomo]**: Analisei seu histórico de vendas e níveis atuais.\n\n"
                    f"⚠️ **Previsão de Ruptura:**\n{resumo}\n\n"
                    f"Deseja que eu gere o rascunho do pedido de compra para esses itens?"
                )
            else:
                response_text = "📦 **[Agente de Estoque]**: Ótimas notícias! Baseado na sua velocidade de vendas atual, seu estoque está seguro para os próximos 15 dias em todos os itens principais."
        
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
            if "cadastrar" in msg or "novo" in msg:
                response_text = "✨ **Assistente**: Claro! Posso ajudar com novos cadastros. O que você gostaria de registrar?"
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
            model_used=used_model,
            suggestions=suggestions,
            actions=actions
        )

    async def process_audio_scribe(self, audio_content: bytes):
        """
        Recebe o áudio da consulta e retorna um JSON estruturado com os dados clínicos.
        Idealmente usaria Gemini 1.5 Flash que aceita áudio nativamente.
        """
        # Exemplo de prompt para a IA estruturar o prontuário
        prompt = """
        Você é um assistente veterinário especializado em transcrição de consultas. 
        Analise o áudio (ou texto transcrito) da consulta e extraia as seguintes informações em JSON:
        {
            "anamnese": "Histórico relatado pelo tutor",
            "exame_fisico": "Observações clínicas do veterinário",
            "suspeita_diagnostica": "Diagnóstico provisório",
            "prescricao": "Medicamentos, doses e recomendações"
        }
        Seja preciso e mantenha os termos técnicos veterinários.
        """
        
        # Simulação de resposta estruturada (em um ambiente real, enviamos o áudio para a API do Gemini)
        # Aqui, como estamos configurando a infraestrutura, deixaremos o hook pronto.
        return {
            "anamnese": "O tutor relatou que o pet está apático e sem apetite há 2 dias.",
            "exame_fisico": "Temperatura 39.2°C, mucosas levemente pálidas, dor abdominal à palpação.",
            "suspeita_diagnostica": "Gastroenterite ou Hemoparasitose",
            "prescricao": "Doxiciclina 100mg (1 comprimido a cada 12h por 14 dias), Dipirona (10 gotas se dor)."
        }


ai_service = AIService()
