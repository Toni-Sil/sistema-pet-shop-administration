from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import httpx
from openai import AsyncOpenAI

from .config import AgentConfig, get_agent_config


@dataclass
class AgentContext:
    """Contexto passado para os agentes.

    Aqui no futuro você pode incluir:
    - store_id (instância do pet shop)
    - user_id (quem está chamando)
    - idioma
    - etc.
    """

    store_id: str | None = None
    user_id: str | None = None


class BaseAgent:
    def __init__(self, cfg: AgentConfig, llm_client: AsyncOpenAI) -> None:
        self.cfg = cfg
        self.llm = llm_client

    async def call_llm(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        """Chama o modelo configurado para o agente.

        Inicialmente usa OpenAI; no futuro, pode ser trocado por outro provedor
        (Claude, Gemini, Sabiá, etc.) via camada de abstração.
        """

        response = await self.llm.chat.completions.create(
            model=self.cfg.model,
            max_tokens=self.cfg.max_tokens,
            temperature=self.cfg.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
        )
        return response.choices[0].message.content or ""

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - interface
        raise NotImplementedError


class OrchestratorAgent(BaseAgent):
    """Decide para qual agente rotear a requisição.

    Retorna um dicionário com:
    - target_agent: nome do agente
    - reasoning: breve explicação
    """

    SYSTEM_PROMPT = (
        "Você é o orquestrador de um sistema de gestão de pet shop. "
        "Sua função é APENAS decidir qual módulo deve tratar a solicitação: "
        "'estoque', 'financeiro', 'agendamento', 'crm', 'relatorios' ou 'whatsapp'. "
        "Responda em JSON com as chaves 'target_agent' e 'reasoning'."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        user_message = payload.get("message", "")
        messages = [
            {"role": "user", "content": user_message},
        ]
        raw = await self.call_llm(self.SYSTEM_PROMPT, messages)
        # Para manter simples, tentamos interpretar como JSON;
        # se falhar, caímos em um default.
        try:
            import json

            data = json.loads(raw)
            target = data.get("target_agent", "estoque")
            reasoning = data.get("reasoning", "")
        except Exception:
            target = "estoque"
            reasoning = "Não consegui interpretar corretamente, roteando para estoque por padrão."

        return {"target_agent": target, "reasoning": reasoning, "raw": raw}


class EstoqueAgent(BaseAgent):
    """Agente especializado em estoque.

    Versão inicial: apenas responde perguntas em linguagem natural
    usando os dados que forem passados no payload.
    Em versões futuras, pode chamar o banco para buscar produtos, alertas, etc.
    """

    SYSTEM_PROMPT = (
        "Você é um assistente especializado em ESTOQUE de um pet shop. "
        "Responda de forma objetiva em português do Brasil. "
        "Use apenas as informações fornecidas no contexto e no payload."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        question = payload.get("question", "")
        context = payload.get("context", "")
        messages = [
            {"role": "system", "content": f"Contexto:\n{context}"},
            {"role": "user", "content": question},
        ]
        answer = await self.call_llm(self.SYSTEM_PROMPT, messages)
        return {"answer": answer}


class FinanceiroAgent(BaseAgent):
    SYSTEM_PROMPT = (
        "Você é um assistente financeiro para um pet shop. "
        "Explique resultados de vendas, despesas e lucro de forma clara, em linguagem simples."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        question = payload.get("question", "")
        context = payload.get("context", "")
        messages = [
            {"role": "system", "content": f"Contexto financeiro:\n{context}"},
            {"role": "user", "content": question},
        ]
        answer = await self.call_llm(self.SYSTEM_PROMPT, messages)
        return {"answer": answer}


class AgendamentoAgent(BaseAgent):
    """Agente de agendamento - cria e gerencia compromissos."""
    
    SYSTEM_PROMPT = (
        "Você é o Agente de Agendamento de um pet shop. Suas capacidades:\n"
        "1. Criar novos agendamentos (banho, tosa, consulta, etc.)\n"
        "2. Verificar horários disponíveis\n"
        "3. Sugerir melhores horários baseado no histórico do pet\n"
        "4. Verificar conflitos de horário\n"
        "5. Enviar lembretes automáticos para tutores\n\n"
        "Sempre confirme detalhes antes de executar ações."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "consult")
        
        if action == "create":
            return await self._create_appointment(ctx, payload)
        elif action == "check_availability":
            return await self._check_availability(ctx, payload)
        elif action == "suggest_slots":
            return await self._suggest_slots(ctx, payload)
        else:
            return await self._consult_schedule(ctx, payload)

    async def _create_appointment(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um novo agendamento com validação."""
        return {
            "action": "create_appointment",
            "requires_confirmation": True,
            "proposed": {
                "pet_id": payload.get("pet_id"),
                "service": payload.get("service"),
                "date": payload.get("date"),
                "time": payload.get("time"),
                "professional": payload.get("professional"),
                "notes": payload.get("notes")
            },
            "message": f"✅ Pronto para agendar {payload.get('service')} para {payload.get('pet_name')} no dia {payload.get('date')} às {payload.get('time')}.\n\nDeseja confirmar?"
        }

    async def _check_availability(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica disponibilidade de horários."""
        return {
            "action": "check_availability",
            "date": payload.get("date"),
            "message": f"Consultando horários disponíveis para {payload.get('date')}..."
        }

    async def _suggest_slots(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sugere melhores horários baseado em histórico."""
        return {
            "action": "suggest_slots",
            "pet_id": payload.get("pet_id"),
            "message": "Analisando histórico de agendamentos para sugerir o melhor horário..."
        }

    async def _consult_schedule(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta simples da agenda."""
        question = payload.get("question", "")
        context = payload.get("context", "")
        messages = [
            {"role": "system", "content": f"Contexto da agenda:\n{context}"},
            {"role": "user", "content": question},
        ]
        answer = await self.call_llm(self.SYSTEM_PROMPT, messages)
        return {"answer": answer}


class CRMAgent(BaseAgent):
    """Agente de CRM - relacionamento e saúde dos pets."""
    
    SYSTEM_PROMPT = (
        "Você é o Agente de Relacionamento (CRM) de um pet shop. Suas capacidades:\n"
        "1. Rastrear vacinas e tratamentos dos pets\n"
        "2. Identificar clientes inativos para campanhas de retorno\n"
        "3. Sugerir serviços baseados no histórico do pet\n"
        "4. Enviar mensagens personalizadas de aniversário\n"
        "5. Alertar sobre pets sem visita há muito tempo\n"
        "6. Criar programas de fidelidade personalizados\n\n"
        "Seja proativo em identificar oportunidades de cuidado."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "consult")
        
        if action == "vaccine_alert":
            return await self._vaccine_alert(ctx, payload)
        elif action == "inactive_clients":
            return await self._inactive_clients(ctx, payload)
        elif action == "suggest_services":
            return await self._suggest_services(ctx, payload)
        elif action == "birthday_campaign":
            return await self._birthday_campaign(ctx, payload)
        else:
            return await self._consult_crm(ctx, payload)

    async def _vaccine_alert(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Alerta sobre vacinas vencendo."""
        return {
            "action": "vaccine_alert",
            "requires_action": True,
            "message": "🩺 Identifiquei pets com vacinas vencendo. Deseja que eu gere mensagens de lembrete para os tutores?",
            "suggested_messages": []
        }

    async def _inactive_clients(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Identifica clientes inativos."""
        days = payload.get("days", 60)
        return {
            "action": "inactive_clients",
            "days": days,
            "message": f"🔍 Analisando clientes sem visita nos últimos {days} dias...",
            "suggested_campaign": "Oferecer desconto de 20% no próximo banho+tosa"
        }

    async def _suggest_services(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sugere serviços baseados no histórico."""
        return {
            "action": "suggest_services",
            "pet_id": payload.get("pet_id"),
            "message": "💡 Analisando histórico do pet para sugerir serviços personalizados..."
        }

    async def _birthday_campaign(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Campanha de aniversário."""
        return {
            "action": "birthday_campaign",
            "month": payload.get("month"),
            "message": "🎂 Identificando aniversariantes do mês para campanha especial..."
        }

    async def _consult_crm(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta simples de CRM."""
        question = payload.get("question", "")
        context = payload.get("context", "")
        messages = [
            {"role": "system", "content": f"Contexto do CRM:\n{context}"},
            {"role": "user", "content": question},
        ]
        answer = await self.call_llm(self.SYSTEM_PROMPT, messages)
        return {"answer": answer}


class ComprasAgent(BaseAgent):
    """Agente de compras - automação de reposição de estoque."""
    
    SYSTEM_PROMPT = (
        "Você é o Agente de Compras de um pet shop. Suas capacidades:\n"
        "1. Identificar produtos abaixo do estoque mínimo\n"
        "2. Sugerir quantidades de compra baseado em vendas históricas\n"
        "3. Calcular melhor momento para comprar (evitar desperdício)\n"
        "4. Sugerir fornecedores baseado em preços anteriores\n"
        "5. Criar lista de compras otimizada\n"
        "6. Calcular ponto de pedido (reorder point)\n\n"
        "Otimize o capital de giro sem deixar faltar produtos."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "analyze")
        
        if action == "low_stock_report":
            return await self._low_stock_report(ctx, payload)
        elif action == "create_purchase_list":
            return await self._create_purchase_list(ctx, payload)
        elif action == "optimize_inventory":
            return await self._optimize_inventory(ctx, payload)
        else:
            return await self._analyze_purchases(ctx, payload)

    async def _low_stock_report(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Relatório de produtos em falta."""
        return {
            "action": "low_stock_report",
            "requires_action": True,
            "message": "📦 Gerando relatório de produtos que precisam de reposição urgente...",
            "suggested_order": []
        }

    async def _create_purchase_list(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Cria lista inteligente de compras."""
        return {
            "action": "create_purchase_list",
            "budget": payload.get("budget"),
            "priority": payload.get("priority", "balanced"),
            "message": f"🛒 Criando lista de compras otimizada dentro do orçamento de R$ {payload.get('budget', 'ilimitado')}..."
        }

    async def _optimize_inventory(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sugere otimizações de estoque."""
        return {
            "action": "optimize_inventory",
            "message": "📊 Analisando giro de produtos para sugerir melhorias no estoque...",
            "recommendations": []
        }

    async def _analyze_purchases(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Análise de compras."""
        question = payload.get("question", "")
        context = payload.get("context", "")
        messages = [
            {"role": "system", "content": f"Contexto de compras:\n{context}"},
            {"role": "user", "content": question},
        ]
        answer = await self.call_llm(self.SYSTEM_PROMPT, messages)
        return {"answer": answer}


class MarketingAgent(BaseAgent):
    """Agente de Marketing - campanhas e fidelização."""
    
    SYSTEM_PROMPT = (
        "Você é o Agente de Marketing de um pet shop. Suas capacidades:\n"
        "1. Criar campanhas de recuperação de clientes inativos\n"
        "2. Sugerir promoções sazonais (Dia do Cão, Black Friday, etc.)\n"
        "3. Segmentar clientes para campanhas personalizadas\n"
        "4. Criar scripts de mensagens para WhatsApp\n"
        "5. Analisar efetividade de promoções anteriores\n"
        "6. Sugerir upsell e cross-sell\n\n"
        "Crie campanhas que geram resultados reais."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "consult")
        
        if action == "win_back_campaign":
            return await self._win_back_campaign(ctx, payload)
        elif action == "seasonal_promo":
            return await self._seasonal_promo(ctx, payload)
        elif action == "segment_customers":
            return await self._segment_customers(ctx, payload)
        elif action == "whatsapp_script":
            return await self._whatsapp_script(ctx, payload)
        else:
            return await self._consult_marketing(ctx, payload)

    async def _win_back_campaign(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Campanha de recuperação de clientes."""
        return {
            "action": "win_back_campaign",
            "requires_approval": True,
            "message": "🎯 Criando campanha de recuperação de clientes inativos...",
            "suggested_offer": "20% OFF no pacote Banho + Tosa",
            "channel": "WhatsApp + Email",
            "expected_roi": "3x"
        }

    async def _seasonal_promo(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Promoção sazonal."""
        season = payload.get("season", "primavera")
        return {
            "action": "seasonal_promo",
            "season": season,
            "message": f"🌟 Criando promoção especial de {season}...",
            "suggested_campaigns": []
        }

    async def _segment_customers(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Segmentação de clientes."""
        return {
            "action": "segment_customers",
            "message": "👥 Segmentando base de clientes para campanhas personalizadas...",
            "segments": []
        }

    async def _whatsapp_script(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Gera scripts para WhatsApp."""
        purpose = payload.get("purpose", "reminder")
        return {
            "action": "whatsapp_script",
            "purpose": purpose,
            "message": f"💬 Gerando script otimizado para {purpose}...",
            "script": ""
        }

    async def _consult_marketing(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta de marketing."""
        question = payload.get("question", "")
        context = payload.get("context", "")
        messages = [
            {"role": "system", "content": f"Contexto de marketing:\n{context}"},
            {"role": "user", "content": question},
        ]
        answer = await self.call_llm(self.SYSTEM_PROMPT, messages)
        return {"answer": answer}


class PrecificacaoAgent(BaseAgent):
    """Agente de Precificação Inteligente."""
    
    SYSTEM_PROMPT = (
        "Você é o Agente de Precificação de um pet shop. Suas capacidades:\n"
        "1. Analisar margem de lucro atual por produto/serviço\n"
        "2. Sugerir ajustes de preço baseado em sazonalidade\n"
        "3. Identificar produtos com margem baixa\n"
        "4. Calcular markup ideal para cada categoria\n"
        "5. Sugerir pacotes promocionais lucrativos\n"
        "6. Analisar elasticidade de preço (o quanto pode aumentar sem perder vendas)\n\n"
        "Maximize lucratividade sem perder competitividade."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "analyze")
        
        if action == "margin_analysis":
            return await self._margin_analysis(ctx, payload)
        elif action == "suggest_prices":
            return await self._suggest_prices(ctx, payload)
        elif action == "create_packages":
            return await self._create_packages(ctx, payload)
        else:
            return await self._analyze_pricing(ctx, payload)

    async def _margin_analysis(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Análise de margens."""
        return {
            "action": "margin_analysis",
            "message": "💰 Analisando margens de lucro de todos os produtos e serviços...",
            "low_margin_products": [],
            "high_performers": []
        }

    async def _suggest_prices(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sugere novos preços."""
        return {
            "action": "suggest_prices",
            "category": payload.get("category"),
            "target_margin": payload.get("target_margin", 50),
            "message": f"📈 Calculando preços ideais para margem de {payload.get('target_margin', 50)}%..."
        }

    async def _create_packages(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Cria pacotes promocionais."""
        return {
            "action": "create_packages",
            "message": "🎁 Criando pacotes promocionais que aumentam ticket médio...",
            "suggested_packages": []
        }

    async def _analyze_pricing(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Análise geral de precificação."""
        question = payload.get("question", "")
        context = payload.get("context", "")
        messages = [
            {"role": "system", "content": f"Contexto de precificação:\n{context}"},
            {"role": "user", "content": question},
        ]
        answer = await self.call_llm(self.SYSTEM_PROMPT, messages)
        return {"answer": answer}


class AnalisePreditivaAgent(BaseAgent):
    """Agente de Análise Preditiva - previsões inteligentes."""
    
    SYSTEM_PROMPT = (
        "Você é o Agente de Análise Preditiva de um pet shop. Suas capacidades:\n"
        "1. Prever demanda de produtos para próximos 30/60/90 dias\n"
        "2. Identificar tendências de vendas\n"
        "3. Alertar sobre sazonalidades (quando vender mais ração, quando ter mais agenda, etc.)\n"
        "4. Prever fluxo de caixa\n"
        "5. Sugerir quando contratar mais profissionais\n"
        "6. Identificar riscos de estoque\n\n"
        "Transforme dados em previsões acionáveis."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "forecast")
        
        if action == "demand_forecast":
            return await self._demand_forecast(ctx, payload)
        elif action == "cash_flow_prediction":
            return await self._cash_flow_prediction(ctx, payload)
        elif action == "seasonal_analysis":
            return await self._seasonal_analysis(ctx, payload)
        elif action == "staffing_needs":
            return await self._staffing_needs(ctx, payload)
        else:
            return await self._general_forecast(ctx, payload)

    async def _demand_forecast(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Previsão de demanda."""
        days = payload.get("days", 30)
        return {
            "action": "demand_forecast",
            "period": days,
            "message": f"🔮 Gerando previsão de demanda para os próximos {days} dias...",
            "top_products": [],
            "risk_items": []
        }

    async def _cash_flow_prediction(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Previsão de fluxo de caixa."""
        return {
            "action": "cash_flow_prediction",
            "message": "💵 Prevendo fluxo de caixa para próximas semanas...",
            "warnings": [],
            "opportunities": []
        }

    async def _seasonal_analysis(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Análise sazonal."""
        return {
            "action": "seasonal_analysis",
            "current_month": payload.get("month"),
            "message": "📅 Analisando padrões sazonais para otimizar operações...",
            "recommendations": []
        }

    async def _staffing_needs(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Necessidade de equipe."""
        return {
            "action": "staffing_needs",
            "message": "👨‍💼 Analisando demanda para sugerir contratações ou ajustes de escala...",
            "recommendations": []
        }

    async def _general_forecast(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Previsão geral."""
        question = payload.get("question", "")
        context = payload.get("context", "")
        messages = [
            {"role": "system", "content": f"Contexto de análise:\n{context}"},
            {"role": "user", "content": question},
        ]
        answer = await self.call_llm(self.SYSTEM_PROMPT, messages)
        return {"answer": answer}


class AtendimentoAgent(BaseAgent):
    """Agente de Atendimento - FAQ e suporte ao cliente."""
    
    SYSTEM_PROMPT = (
        "Você é o Agente de Atendimento Virtual de um pet shop. Suas capacidades:\n"
        "1. Responder perguntas frequentes (horário de funcionamento, preços, serviços)\n"
        "2. Explicar processos (como agendar, o que levar, tempo de espera)\n"
        "3. Calmamente conduzir conversas difíceis (reclamações)\n"
        "4. Encaminhar para humano quando necessário\n"
        "5. Informar sobre políticas da loja\n"
        "6. Sugerir serviços baseados na necessidade do cliente\n\n"
        "Seja cordial, claro e empático."
    )

    async def run(self, ctx: AgentContext, payload: Dict[str, Any]) -> Dict[str, Any]:
        question = payload.get("question", "")
        
        # FAQ automático com respostas pré-definidas para agilidade
        faq_responses = {
            "horario": "🕐 Funcionamos de segunda a sábado, das 8h às 19h. Domingos apenas com agendamento prévio.",
            "preco": "💰 Nossos preços variam conforme o porte do pet e serviço desejado. Posso verificar valores específicos para você!",
            "agendar": "📅 Você pode agendar pelo app, WhatsApp ou telefone. Precisa de ajuda para marcar?",
            "banho": "🛁 O banho inclui: higienização completa, secagem, hidratação e perfumagem. Tempo médio: 1h30.",
            "tosa": "✂️ Oferecemos tosa higiênica, tosa na tesoura e tosa na máquina. Qual seu pet prefere?",
            "vacina": "💉 Vacinamos cães e gatos com as principais vacinas (V8, V10, V3, V4, antirrábica). Carteira em dia garantida!",
            "emergencia": "🚨 Para emergências veterinárias fora do horário comercial, temos parceria com clínica 24h. Deseja o contato?",
        }
        
        # Verifica FAQ primeiro
        q_lower = question.lower()
        for keyword, response in faq_responses.items():
            if keyword in q_lower:
                return {"answer": response, "source": "faq", "escalate": False}
        
        # Caso não encontre no FAQ, usa LLM
        context = payload.get("context", "")
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Contexto: {context}\n\nPergunta: {question}"},
        ]
        answer = await self.call_llm(self.SYSTEM_PROMPT, messages)
        
        return {
            "answer": answer,
            "source": "llm",
            "escalate": "reclamação" in q_lower or "problema" in q_lower or "ruim" in q_lower
        }


def get_openai_api_key_from_settings(store_settings: Dict[str, Any] | None) -> str | None:
    """Extrai a chave de API da OpenAI das configurações da loja."""
    if not store_settings:
        return None
        
    # 1. Tenta buscar em ai_providers
    providers = store_settings.get("ai_providers", [])
    if isinstance(providers, list):
        for provider in providers:
            if isinstance(provider, dict) and provider.get("id") == "openai":
                return provider.get("apiKey")
    elif isinstance(providers, dict):
        openai_p = providers.get("openai")
        if isinstance(openai_p, dict):
            return openai_p.get("apiKey")
            
    # 2. Tenta buscar chaves diretas
    for k in ["openai_api_key", "openai_key", "api_key"]:
        if store_settings.get(k):
            return store_settings.get(k)
            
    return None


def build_llm_client(api_key: str | None = None) -> AsyncOpenAI:
    """Cria cliente LLM.

    - Por enquanto usa OpenAI, lendo OPENAI_API_KEY do ambiente ou chave dinâmica.
    - No futuro, pode ser estendido para múltiplos provedores.
    """
    if api_key:
        return AsyncOpenAI(api_key=api_key)
    return AsyncOpenAI()


def get_agent(name: str, llm_client: AsyncOpenAI, store_settings: Dict[str, Any] | None = None) -> BaseAgent:
    cfg = get_agent_config(name, store_settings)

    agent_map = {
        "orchestrator": OrchestratorAgent,
        "estoque": EstoqueAgent,
        "inventory": EstoqueAgent,
        "financeiro": FinanceiroAgent,
        "financial": FinanceiroAgent,
        "agendamento": AgendamentoAgent,
        "scheduling": AgendamentoAgent,
        "crm": CRMAgent,
        "compras": ComprasAgent,
        "purchasing": ComprasAgent,
        "marketing": MarketingAgent,
        "precificacao": PrecificacaoAgent,
        "pricing": PrecificacaoAgent,
        "analise": AnalisePreditivaAgent,
        "analytics": AnalisePreditivaAgent,
        "atendimento": AtendimentoAgent,
        "support": AtendimentoAgent,
    }

    agent_class = agent_map.get(name)
    if agent_class:
        return agent_class(cfg, llm_client)

    # Fallback para orquestrador se não encontrar
    return OrchestratorAgent(cfg, llm_client)
