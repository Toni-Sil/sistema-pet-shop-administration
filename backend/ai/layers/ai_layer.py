from __future__ import annotations
"""
AI LAYER - Reasoning
Responsabilidade: LLM calls, prompts, reasoning logic
Separada das regras de negócio e tools
"""

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from openai import AsyncOpenAI

from ai.config import AgentConfig, get_agent_config


@dataclass
class ReasoningStep:
    thought: str
    action: str | None = None
    observation: str | None = None
    confidence: float = 0.0


@dataclass
class ReasoningChain:
    steps: List[ReasoningStep] = field(default_factory=list)
    final_decision: str = ""
    confidence: float = 0.0

    def add_step(self, thought: str, action: str | None = None, observation: str | None = None, confidence: float = 0.5) -> None:
        self.steps.append(ReasoningStep(
            thought=thought,
            action=action,
            observation=observation,
            confidence=confidence
        ))


class IntentClassifier:
    SYSTEM_PROMPT = """Você é um classificador de intenções para um pet shop.
    Analise a mensagem do cliente e classifique a intenção principal.
    
    Intenções possíveis:
    - agendamento: quer agendar serviço
    - consulta: tem dúvidas gerais
    - reclamacao: quer relatar problema
    - compra: quer comprar produto
    - pagamento: quer informação sobre pagamento
    - consulta_veterinaria: precisa de atendimento veterinário
    - informacoes: quer saber horários, localização, etc
    - outro: nenhuma das anteriores
    
    Responda em JSON com:
    {"intent": "agendamento", "entities": {"pet": "nome", "service": "banho"}, "confidence": 0.9}
    """

    def __init__(self, llm: AsyncOpenAI, model: str = "gpt-4o-mini") -> None:
        self.llm = llm
        self.model = model

    async def classify(self, message: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        try:
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ],
                max_tokens=256,
                temperature=0.1,
            )
            
            result = json.loads(response.choices[0].message.content or "{}")
            return {
                "intent": result.get("intent", "outro"),
                "entities": result.get("entities", {}),
                "confidence": result.get("confidence", 0.5),
            }
        except Exception as e:
            return {
                "intent": "outro",
                "entities": {},
                "confidence": 0.0,
                "error": str(e),
            }


class ReasoningAgent:
    SYSTEM_PROMPT = """Você é um agente de raciocínio para um pet shop.
    
    Sua tarefa é:
    1. Analisar a situação
    2. Pensar em próximos passos
    3. Executar ações quando necessário
    4. Retornar resultado
    
    Pense em voz alta (chain of thought) e depois tome decisões.
    """

    def __init__(self, llm: AsyncOpenAI, config: AgentConfig) -> None:
        self.llm = llm
        self.config = config

    async def reason(
        self,
        task: str,
        context: Dict[str, Any],
        tools: Dict[str, Callable] | None = None,
    ) -> ReasoningChain:
        chain = ReasoningChain()
        
        chain.add_step(
            thought=f"Analisando tarefa: {task}",
            confidence=0.8
        )
        
        prompt = f"""
        Tarefa: {task}
        
        Contexto:
        {json.dumps(context, indent=2, default=str)}
        
        Ferramentas disponíveis: {list(tools.keys()) if tools else 'nenhuma'}
        
        Pense passo a passo e retorne sua decisão final em JSON:
        {{
            "thoughts": ["pensamento 1", "pensamento 2"],
            "action": "acao_escolhida",
            "parameters": {{}},
            "decision": "decisao_final",
            "confidence": 0.85
        }}
        """
        
        try:
            response = await self.llm.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            
            result = json.loads(response.choices[0].message.content or "{}")
            
            for thought in result.get("thoughts", []):
                chain.add_step(thought=thought, confidence=result.get("confidence", 0.5))
            
            chain.final_decision = result.get("decision", "")
            chain.confidence = result.get("confidence", 0.5)
            
            if tools and result.get("action"):
                action = result["action"]
                params = result.get("parameters", {})
                if action in tools:
                    observation = await tools[action](**params)
                    chain.add_step(
                        thought=f"Executando {action}",
                        action=action,
                        observation=str(observation),
                        confidence=0.9
                    )
        
        except Exception as e:
            chain.add_step(
                thought=f"Erro no raciocínio: {str(e)}",
                confidence=0.0
            )
        
        return chain


class SupervisorReasoning:
    SYSTEM_PROMPT = """Você é o Supervisor Cognitivo de um pet shop.
    
    Sua função é:
    1. Receber requisições de diferentes agentes
    2. Decidir como coordenar (serial, paralelo, aprovar humano, escalar)
    3. Resolver conflitos entre agentes
    4. Determinar prioridade
    5. Pedir aprovação humana quando necessário
    
    Decisões possíveis:
    - execute_single: executar um agente
    - execute_parallel: executar múltiplos agentes simultaneamente
    - execute_sequential: executar agentes em sequência
    - require_approval: precisa aprovação humana
    - escalate: escalar para humano
    - defer: adiar para depois
    
    Responda em JSON com a decisão e justificativa.
    """

    def __init__(self, llm: AsyncOpenAI, model: str = "gpt-4o") -> None:
        self.llm = llm
        self.model = model

    async def decide(
        self,
        message: str,
        active_agents: List[str],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = f"""
        Mensagem: {message}
        
        Agentes ativos: {active_agents}
        
        Contexto:
        {json.dumps(context, default=str)}
        
        Retorne sua decisão:
        {{
            "decision": "execute_single|execute_parallel|execute_sequential|require_approval|escalate|defer",
            "target_agents": ["agente1", "agente2"],
            "reasoning": "justificativa",
            "priority": 1-10,
            "requires_approval": true/false,
            "approval_reason": "motivo se precisar aprovação"
        }}
        """

        try:
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=512,
                temperature=0.2,
            )
            
            result = json.loads(response.choices[0].message.content or "{}")
            return {
                "decision": result.get("decision", "defer"),
                "target_agents": result.get("target_agents", []),
                "reasoning": result.get("reasoning", ""),
                "priority": result.get("priority", 5),
                "requires_approval": result.get("requires_approval", False),
                "approval_reason": result.get("approval_reason"),
            }
        except Exception as e:
            return {
                "decision": "defer",
                "target_agents": [],
                "reasoning": f"Erro: {str(e)}",
                "priority": 5,
                "requires_approval": False,
            }


class ConversationAgent:
    SYSTEM_PROMPT = """Você é o agente de conversas do pet shop.
    
    Características:
    - Sempre seja educado e prestativo
    - Use emojis moderadamente
    - Mantenha conversas curtas e objetivas
    - Para agendamentos, colete: pet, serviço, data, horário
    - Não invente informações
    - Quando unsure, peça clarification
    
    Histórico de conversa deve ser considerado.
    """

    def __init__(self, llm: AsyncOpenAI, model: str = "gpt-4o-mini") -> None:
        self.llm = llm
        self.model = model

    async def respond(
        self,
        message: str,
        history: List[Dict[str, str]],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        
        for h in history[-10:]:
            messages.append({"role": h["role"], "content": h["content"]})
        
        context_str = f"\nContexto: {json.dumps(context, default=str)}"
        messages.append({"role": "user", "content": message + context_str})

        try:
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=256,
                temperature=0.7,
            )
            
            return {
                "response": response.choices[0].message.content or "",
                "needs_action": any(kw in message.lower() for kw in ["agendar", "marcar", "comprar"]),
                "intent_detected": context.get("intent", "conversa"),
            }
        except Exception as e:
            return {
                "response": "Desculpe, tive um problema. Pode reformular?",
                "error": str(e),
            }


def create_ai_layer(llm: AsyncOpenAI, store_settings: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "intent_classifier": IntentClassifier(llm),
        "reasoning_agent": ReasoningAgent(llm, get_agent_config("orchestrator", store_settings)),
        "supervisor": SupervisorReasoning(llm),
        "conversation": ConversationAgent(llm),
    }