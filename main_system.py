"""
Multi-Agent LLM System - Main Entry Point
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from config import settings
from base_agent import AgentState
from orchestrator import Orchestrator
from research_agent import ResearchAgent
from code_agent import CodeAgent
from data_agent import DataAgent
from writing_agent import WritingAgent, QAAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"{settings.logs_dir}/multi_agent_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)

logger = logging.getLogger(__name__)


class MultiAgentSystem:
    """
    Main Multi-Agent System
    Coordinates all agents to accomplish complex tasks
    """
    
    def __init__(self):
        """Initialize the multi-agent system"""
        logger.info("Initializing Multi-Agent System")
        
        # Initialize all agents
        self.agents = {
            "research": ResearchAgent(),
            "code": CodeAgent(),
            "data": DataAgent(),
            "writing": WritingAgent(),
            "qa": QAAgent()
        }
        
        # Initialize orchestrator with agents
        self.orchestrator = Orchestrator(self.agents)
        
        # System state
        self.current_state: Optional[AgentState] = None
        self.execution_history = []
        
        logger.info(f"System initialized with {len(self.agents)} agents")
    
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using the multi-agent system
        
        Args:
            task: Task description in natural language
            context: Optional context (data, files, etc.)
        
        Returns:
            Execution results including output and metadata
        """
        logger.info("=" * 80)
        logger.info(f"NEW TASK: {task}")
        logger.info("=" * 80)
        
        try:
            # Create new state
            self.current_state = AgentState()
            
            # Add context if provided
            if context:
                self.current_state.update_context(context)
            
            # Execute via orchestrator
            start_time = datetime.now()
            result = self.orchestrator.execute(task, self.current_state)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Get execution summary
            summary = self.orchestrator.get_execution_summary(self.current_state)
            
            # Build complete result
            complete_result = {
                "task": task,
                "output": result.get("output"),
                "success": result.get("success"),
                "error": result.get("error"),
                "execution_time": execution_time,
                "summary": summary,
                "state": self.current_state.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in history
            self.execution_history.append(complete_result)
            
            # Log completion
            if result.get("success"):
                logger.info(f"Task completed successfully in {execution_time:.2f}s")
            else:
                logger.error(f"Task failed: {result.get('error')}")
            
            return complete_result
            
        except Exception as e:
            logger.error(f"System execution failed: {e}", exc_info=True)
            return {
                "task": task,
                "output": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics for all agents"""
        stats = {}
        for agent_id, agent in self.agents.items():
            stats[agent_id] = agent.get_stats()
        stats["orchestrator"] = self.orchestrator.get_stats()
        return stats
    
    def reset_stats(self):
        """Reset statistics for all agents"""
        for agent in self.agents.values():
            agent.reset_stats()
        self.orchestrator.reset_stats()
        logger.info("All agent statistics reset")
    
    def get_history(self, limit: int = 10) -> list:
        """Get execution history"""
        return self.execution_history[-limit:]
    
    def clear_history(self):
        """Clear execution history"""
        self.execution_history = []
        logger.info("Execution history cleared")


def main():
    """Main entry point for CLI usage"""
    import sys
    
    # Create system
    system = MultiAgentSystem()
    
    # Check if task provided as argument
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        
        # Execute task
        result = system.execute(task)
        
        # Print result
        print("\n" + "=" * 80)
        print("RESULT:")
        print("=" * 80)
        print(result.get("output", "No output"))
        print("\n" + "=" * 80)
        print(f"Success: {result.get('success')}")
        print(f"Execution Time: {result.get('execution_time', 0):.2f}s")
        print("=" * 80)
        
    else:
        # Interactive mode
        print("\n" + "=" * 80)
        print("Multi-Agent LLM System - Interactive Mode")
        print("=" * 80)
        print("Enter your task (or 'quit' to exit):\n")
        
        while True:
            try:
                task = input("> ").strip()
                
                if not task:
                    continue
                
                if task.lower() in ['quit', 'exit', 'q']:
                    break
                
                if task.lower() == 'stats':
                    stats = system.get_agent_stats()
                    print("\nAgent Statistics:")
                    for agent_id, agent_stats in stats.items():
                        print(f"  {agent_id}: {agent_stats}")
                    print()
                    continue
                
                # Execute task
                result = system.execute(task)
                
                # Print result
                print("\n" + "-" * 80)
                print(result.get("output", "No output"))
                print("-" * 80 + "\n")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"\nError: {e}\n")
        
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
    