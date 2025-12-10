"""
Base Agent class for Multi-Agent System
All specialized agents inherit from this base class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import OpenAI
import logging
import json

from config import settings, AGENT_CONFIGS

logger = logging.getLogger(__name__)


class AgentMessage:
    """Message passed between agents"""
    
    def __init__(
        self,
        sender: str,
        recipient: str,
        content: str,
        message_type: str = "task",
        metadata: Optional[Dict] = None
    ):
        self.sender = sender
        self.recipient = recipient
        self.content = content
        self.message_type = message_type
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "type": self.message_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class AgentState:
    """Shared state between agents"""
    
    def __init__(self):
        self.messages: List[AgentMessage] = []
        self.results: Dict[str, Any] = {}
        self.context: Dict[str, Any] = {}
        self.history: List[Dict] = []
        self.current_agent: Optional[str] = None
        self.iteration: int = 0
    
    def add_message(self, message: AgentMessage):
        """Add message to state"""
        self.messages.append(message)
        self.history.append({
            "type": "message",
            "data": message.to_dict()
        })
    
    def set_result(self, agent: str, result: Any):
        """Store agent result"""
        self.results[agent] = result
        self.history.append({
            "type": "result",
            "agent": agent,
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_result(self, agent: str) -> Optional[Any]:
        """Get agent result"""
        return self.results.get(agent)
    
    def update_context(self, updates: Dict):
        """Update shared context"""
        self.context.update(updates)
    
    def to_dict(self) -> Dict:
        """Export state as dictionary"""
        return {
            "messages": [m.to_dict() for m in self.messages],
            "results": self.results,
            "context": self.context,
            "history": self.history,
            "current_agent": self.current_agent,
            "iteration": self.iteration
        }


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.config = AGENT_CONFIGS.get(agent_id, {})
        self.name = self.config.get("name", agent_id)
        self.role = self.config.get("role", "Agent")
        self.model = self.config.get("model", settings.agent_model)
        self.temperature = self.config.get("temperature", settings.agent_temperature)
        self.system_prompt = self.config.get("system_prompt", "")
        self.tools = self.config.get("tools", [])
        
        # Initialize OpenAI client
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None
            logger.warning(f"{self.name}: OpenAI client not initialized")
        
        self.execution_count = 0
        self.total_tokens = 0
        
        logger.info(f"Initialized {self.name} ({self.role})")
    
    @abstractmethod
    def execute(self, task: str, state: AgentState) -> Dict[str, Any]:
        """
        Execute agent's task
        Must be implemented by all agents
        
        Args:
            task: Task description
            state: Shared agent state
        
        Returns:
            Dictionary with result and metadata
        """
        pass
    
    def _call_llm(
        self,
        messages: List[Dict],
        temperature: Optional[float] = None,
        max_tokens: int = 2000
    ) -> str:
        """
        Call LLM with messages
        
        Args:
            messages: List of message dictionaries
            temperature: Override default temperature
            max_tokens: Maximum tokens in response
        
        Returns:
            LLM response text
        """
        if not self.client:
            raise RuntimeError(f"{self.name}: OpenAI client not available")
        
        try:
            logger.info(f"{self.name}: Calling LLM with {len(messages)} messages")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                # temperature=temperature or self.temperature,
                # max_tokens=max_tokens
            )
            
            # Track usage
            self.execution_count += 1
            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.total_tokens
                logger.info(
                    f"{self.name}: Used {response.usage.total_tokens} tokens "
                    f"(Total: {self.total_tokens})"
                )
            
            result = response.choices[0].message.content
            return result
            
        except Exception as e:
            logger.error(f"{self.name}: LLM call failed: {e}")
            raise
    
    def _build_messages(
        self,
        task: str,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Build message list for LLM
        
        Args:
            task: Current task
            context: Additional context
        
        Returns:
            List of message dictionaries
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add context if provided
        if context:
            context_str = "\n".join(
                f"{k}: {v}" for k, v in context.items() if v
            )
            if context_str:
                messages.append({
                    "role": "system",
                    "content": f"Context:\n{context_str}"
                })
        
        # Add main task
        messages.append({
            "role": "user",
            "content": task
        })
        
        return messages
    
    def think(self, task: str, context: Optional[Dict] = None) -> str:
        """
        Agent's thinking process
        Calls LLM to reason about task
        
        Args:
            task: Task to think about
            context: Additional context
        
        Returns:
            Agent's thoughts
        """
        messages = self._build_messages(task, context)
        thoughts = self._call_llm(messages)
        
        logger.info(f"{self.name} thinking: {thoughts[:100]}...")
        return thoughts
    
    def decide_next_action(
        self,
        task: str,
        available_tools: List[str],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Decide next action to take
        
        Args:
            task: Current task
            available_tools: List of available tool names
            context: Additional context
        
        Returns:
            Dictionary with action and parameters
        """
        tools_str = "\n".join(f"- {tool}" for tool in available_tools)
        
        decision_prompt = f"""Given the task: {task}

Available tools:
{tools_str}

Decide the next action. Respond in JSON format:
{{
    "action": "tool_name or 'complete'",
    "parameters": {{}},
    "reasoning": "why this action"
}}"""
        
        messages = self._build_messages(decision_prompt, context)
        response = self._call_llm(messages, temperature=0.3)
        
        try:
            decision = json.loads(response)
            logger.info(f"{self.name} decided: {decision.get('action')}")
            return decision
        except json.JSONDecodeError:
            logger.warning(f"{self.name}: Invalid decision format, defaulting")
            return {
                "action": "complete",
                "parameters": {},
                "reasoning": "Error parsing decision"
            }
    
    def format_result(
        self,
        output: Any,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Format agent result consistently
        
        Args:
            output: Agent's output
            success: Whether execution succeeded
            error: Error message if failed
            metadata: Additional metadata
        
        Returns:
            Formatted result dictionary
        """
        return {
            "agent": self.agent_id,
            "name": self.name,
            "output": output,
            "success": success,
            "error": error,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "executions": self.execution_count,
            "tokens_used": self.total_tokens
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "agent": self.name,
            "executions": self.execution_count,
            "total_tokens": self.total_tokens,
            "average_tokens": (
                self.total_tokens / self.execution_count 
                if self.execution_count > 0 else 0
            )
        }
    
    def reset_stats(self):
        """Reset agent statistics"""
        self.execution_count = 0
        self.total_tokens = 0
        logger.info(f"{self.name}: Statistics reset")
    
    def __repr__(self) -> str:
        return f"{self.name} ({self.role})"


class ToolUsingAgent(BaseAgent):
    """Base class for agents that use tools"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.tool_registry = {}
    
    def register_tool(self, tool_name: str, tool_function):
        """Register a tool function"""
        self.tool_registry[tool_name] = tool_function
        logger.info(f"{self.name}: Registered tool '{tool_name}'")
    
    def use_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> Any:
        """
        Use a registered tool
        
        Args:
            tool_name: Name of tool to use
            **kwargs: Tool parameters
        
        Returns:
            Tool result
        """
        if tool_name not in self.tool_registry:
            raise ValueError(f"Tool '{tool_name}' not registered")
        
        logger.info(f"{self.name}: Using tool '{tool_name}'")
        
        try:
            result = self.tool_registry[tool_name](**kwargs)
            logger.info(f"{self.name}: Tool '{tool_name}' succeeded")
            return result
        except Exception as e:
            logger.error(f"{self.name}: Tool '{tool_name}' failed: {e}")
            raise
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return list(self.tool_registry.keys())