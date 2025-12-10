"""
Orchestrator Agent - Coordinates all specialized agents
"""
import logging
from typing import Dict, Any, List, Optional
import json

from base_agent import BaseAgent, AgentState, AgentMessage
from config import settings, WORKFLOW_TEMPLATES

logger = logging.getLogger(__name__)


class Orchestrator(BaseAgent):
    """
    Main orchestrator that coordinates all agents
    Decides which agents to use and in what order
    """
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        super().__init__("orchestrator")
        self.agents = agents
        self.workflow_templates = WORKFLOW_TEMPLATES
    
    def execute(self, task: str, state: AgentState) -> Dict[str, Any]:
        """
        Execute task by coordinating agents
        
        Args:
            task: User's task description
            state: Shared agent state
        
        Returns:
            Final result from agent collaboration
        """
        try:
            logger.info(f"{self.name}: Starting orchestration for task")
            
            # Analyze task and create plan
            plan = self._create_plan(task, state)
            logger.info(f"{self.name}: Created plan with {len(plan)} steps")
            
            # Execute plan
            results = []
            for step_num, step in enumerate(plan, 1):
                logger.info(
                    f"{self.name}: Executing step {step_num}/{len(plan)}: "
                    f"{step['agent']}"
                )
                
                result = self._execute_step(step, state)
                results.append(result)
                
                # Check if we should continue
                if not result.get("success"):
                    logger.warning(
                        f"{self.name}: Step {step_num} failed, "
                        "attempting recovery"
                    )
                    # Could implement retry logic here
                
                # Update iteration count
                state.iteration += 1
                
                # Check max iterations
                if state.iteration >= settings.max_iterations:
                    logger.warning(
                        f"{self.name}: Max iterations reached"
                    )
                    break
            
            # Synthesize final result
            final_result = self._synthesize_results(
                task=task,
                plan=plan,
                results=results,
                state=state
            )
            
            return self.format_result(
                output=final_result,
                success=True,
                metadata={
                    "plan": plan,
                    "steps_executed": len(results),
                    "agents_used": list(set(s["agent"] for s in plan))
                }
            )
            
        except Exception as e:
            logger.error(f"{self.name}: Orchestration failed: {e}")
            return self.format_result(
                output=None,
                success=False,
                error=str(e)
            )
    
    def _create_plan(
        self,
        task: str,
        state: AgentState
    ) -> List[Dict[str, Any]]:
        """
        Create execution plan for task
        
        Args:
            task: Task description
            state: Current state
        
        Returns:
            List of execution steps
        """
        # Check if task matches a template
        template = self._match_template(task)
        
        if template:
            logger.info(
                f"{self.name}: Using template '{template['name']}'"
            )
            return template["steps"]
        
        # Otherwise, create custom plan
        return self._create_custom_plan(task, state)
    
    def _match_template(self, task: str) -> Optional[Dict]:
        """Match task to workflow template"""
        task_lower = task.lower()
        
        keywords = {
            "research_report": ["research", "report", "analysis", "study"],
            "data_analysis": ["analyze", "data", "dataset", "csv"],
            "code_project": ["code", "build", "create", "program", "script"]
        }
        
        for template_id, template_keywords in keywords.items():
            if any(kw in task_lower for kw in template_keywords):
                return self.workflow_templates.get(template_id)
        
        return None
    
    def _create_custom_plan(
        self,
        task: str,
        state: AgentState
    ) -> List[Dict[str, Any]]:
        """
        Create custom execution plan using LLM
        
        Args:
            task: Task description
            state: Current state
        
        Returns:
            List of execution steps
        """
        # Get available agents
        agent_descriptions = "\n".join(
            f"- {agent_id}: {agent.role}"
            for agent_id, agent in self.agents.items()
        )
        
        planning_prompt = f"""Create an execution plan for this task: {task}

Available agents:
{agent_descriptions}

Create a plan with 2-5 steps. Each step should use one agent.

Respond in JSON format:
[
    {{"agent": "agent_id", "action": "what to do", "reasoning": "why"}},
    ...
]"""
        
        messages = self._build_messages(planning_prompt)
        response = self._call_llm(messages, temperature=0.3)
        
        try:
            # Parse JSON response
            plan = json.loads(response)
            
            # Validate plan
            valid_agents = set(self.agents.keys())
            plan = [
                step for step in plan
                if step.get("agent") in valid_agents
            ]
            
            if not plan:
                # Fallback plan
                logger.warning(
                    f"{self.name}: Generated plan was invalid, using fallback"
                )
                plan = [
                    {"agent": "research", "action": "gather information"},
                    {"agent": "writing", "action": "create output"}
                ]
            
            return plan
            
        except json.JSONDecodeError:
            logger.error(
                f"{self.name}: Failed to parse plan, using default"
            )
            # Default fallback plan
            return [
                {"agent": "research", "action": "research task"},
                {"agent": "writing", "action": "write response"}
            ]
    
    def _execute_step(
        self,
        step: Dict[str, Any],
        state: AgentState
    ) -> Dict[str, Any]:
        """
        Execute a single step in the plan
        
        Args:
            step: Step definition
            state: Current state
        
        Returns:
            Step execution result
        """
        agent_id = step["agent"]
        action = step.get("action", "execute task")
        
        if agent_id not in self.agents:
            logger.error(f"{self.name}: Agent '{agent_id}' not found")
            return {
                "success": False,
                "error": f"Agent '{agent_id}' not available"
            }
        
        agent = self.agents[agent_id]
        state.current_agent = agent_id
        
        # Create message for agent
        message = AgentMessage(
            sender=self.agent_id,
            recipient=agent_id,
            content=action,
            message_type="task"
        )
        state.add_message(message)
        
        # Execute agent
        try:
            result = agent.execute(action, state)
            
            # Store result
            state.set_result(agent_id, result)
            
            # Create response message
            response = AgentMessage(
                sender=agent_id,
                recipient=self.agent_id,
                content=str(result.get("output", "")),
                message_type="result",
                metadata=result.get("metadata", {})
            )
            state.add_message(response)
            
            return result
            
        except Exception as e:
            logger.error(
                f"{self.name}: Agent '{agent_id}' execution failed: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "agent": agent_id
            }
    
    def _synthesize_results(
        self,
        task: str,
        plan: List[Dict],
        results: List[Dict],
        state: AgentState
    ) -> str:
        """
        Synthesize final result from all agent outputs
        
        Args:
            task: Original task
            plan: Execution plan
            results: Agent results
            state: Final state
        
        Returns:
            Synthesized final output
        """
        # Collect successful outputs
        outputs = []
        for step, result in zip(plan, results):
            if result.get("success"):
                agent_name = self.agents[step["agent"]].name
                output = result.get("output", "")
                outputs.append(f"**{agent_name}**:\n{output}\n")
        
        if not outputs:
            return "No successful outputs from agents."
        
        outputs_text = "\n".join(outputs)
        
        # Synthesize
        synthesis_prompt = f"""Synthesize the following agent outputs into a comprehensive response to the user's task.

Original Task: {task}

Agent Outputs:
{outputs_text}

Provide a well-structured, cohesive response that:
1. Directly addresses the user's task
2. Integrates information from all agents
3. Maintains a clear and professional tone
4. Includes relevant details and citations where applicable"""
        
        messages = self._build_messages(synthesis_prompt)
        synthesized = self._call_llm(messages, max_tokens=2000)
        
        return synthesized
    
    def get_execution_summary(self, state: AgentState) -> Dict[str, Any]:
        """Get summary of execution"""
        agents_used = {}
        for msg in state.messages:
            if msg.sender != self.agent_id:
                if msg.sender not in agents_used:
                    agents_used[msg.sender] = 0
                agents_used[msg.sender] += 1
        
        return {
            "total_iterations": state.iteration,
            "agents_used": agents_used,
            "messages_exchanged": len(state.messages),
            "results_generated": len(state.results)
        }