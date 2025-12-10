"""
Writing Agent and QA Agent
"""
import logging
from typing import Dict, Any, List

from base_agent import BaseAgent, AgentState
from config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# WRITING AGENT
# ============================================================================

class WritingAgent(BaseAgent):
    """Agent specialized in content creation and writing"""
    
    def __init__(self):
        super().__init__("writing")
    
    def execute(self, task: str, state: AgentState) -> Dict[str, Any]:
        """
        Execute writing task
        
        Args:
            task: Writing task description
            state: Shared agent state
        
        Returns:
            Written content
        """
        try:
            logger.info(f"{self.name}: Starting writing task")
            
            # Gather context from other agents
            research_results = state.context.get("research_results", "")
            data_analysis = state.context.get("data_analysis", "")
            generated_code = state.context.get("generated_code", "")
            
            # Create comprehensive content
            content = self._create_content(
                task=task,
                research=research_results,
                analysis=data_analysis,
                code=generated_code,
                context=state.context
            )
            
            # Store in state
            state.update_context({"written_content": content})
            
            return self.format_result(
                output=content,
                success=True,
                metadata={
                    "word_count": len(content.split()),
                    "has_research": bool(research_results),
                    "has_analysis": bool(data_analysis)
                }
            )
            
        except Exception as e:
            logger.error(f"{self.name}: Execution failed: {e}")
            return self.format_result(
                output=None,
                success=False,
                error=str(e)
            )
    
    def _create_content(
        self,
        task: str,
        research: str = "",
        analysis: str = "",
        code: str = "",
        context: Dict[str, Any] = None
    ) -> str:
        """
        Create content based on inputs
        
        Args:
            task: Writing task
            research: Research results
            analysis: Data analysis
            code: Generated code
            context: Additional context
        
        Returns:
            Written content
        """
        # Build context string
        context_parts = []
        if research:
            context_parts.append(f"Research Findings:\n{research}")
        if analysis:
            context_parts.append(f"Data Analysis:\n{analysis}")
        if code:
            context_parts.append(f"Generated Code:\n```python\n{code}\n```")
        
        context_str = "\n\n".join(context_parts) if context_parts else "No additional context."
        
        # Create writing prompt
        writing_prompt = f"""Create high-quality content for this task: {task}

Available Information:
{context_str}

Requirements:
1. Well-structured and organized
2. Clear and engaging writing
3. Use markdown formatting
4. Include relevant sections/headers
5. Cite sources when using research
6. Be comprehensive but concise
7. Professional tone

Create complete, ready-to-use content."""
        
        messages = self._build_messages(writing_prompt, context)
        content = self._call_llm(messages, temperature=0.8, max_tokens=2000)
        
        return content
    
    def edit_content(self, content: str, instructions: str) -> str:
        """
        Edit existing content
        
        Args:
            content: Content to edit
            instructions: Edit instructions
        
        Returns:
            Edited content
        """
        edit_prompt = f"""Edit this content according to the instructions.

Content:
{content}

Instructions: {instructions}

Provide the edited version, maintaining the original style and format."""
        
        messages = self._build_messages(edit_prompt)
        edited = self._call_llm(messages, temperature=0.5)
        
        return edited
    
    def format_markdown(self, text: str) -> str:
        """
        Format text as markdown
        
        Args:
            text: Plain text
        
        Returns:
            Markdown formatted text
        """
        format_prompt = f"""Convert this text to well-formatted markdown.

Text:
{text}

Add:
- Appropriate headers
- Bullet points for lists
- Bold/italic emphasis
- Code blocks if needed
- Links if URLs present"""
        
        messages = self._build_messages(format_prompt)
        formatted = self._call_llm(messages, temperature=0.3)
        
        return formatted


# ============================================================================
# QA AGENT
# ============================================================================

class QAAgent(BaseAgent):
    """Agent specialized in quality assurance and validation"""
    
    def __init__(self):
        super().__init__("qa")
    
    def execute(self, task: str, state: AgentState) -> Dict[str, Any]:
        """
        Execute QA task
        
        Args:
            task: QA task description
            state: Shared agent state
        
        Returns:
            QA results and feedback
        """
        try:
            logger.info(f"{self.name}: Starting QA review")
            
            # Gather outputs to review
            outputs_to_review = {
                "research": state.context.get("research_results"),
                "analysis": state.context.get("data_analysis"),
                "code": state.context.get("generated_code"),
                "writing": state.context.get("written_content")
            }
            
            # Remove None values
            outputs_to_review = {
                k: v for k, v in outputs_to_review.items() if v
            }
            
            if not outputs_to_review:
                return self.format_result(
                    output="No outputs available to review.",
                    success=True
                )
            
            # Perform QA review
            qa_results = self._perform_qa_review(
                task=task,
                outputs=outputs_to_review,
                context=state.context
            )
            
            # Store in state
            state.update_context({"qa_results": qa_results})
            
            return self.format_result(
                output=qa_results,
                success=True,
                metadata={
                    "reviewed_agents": list(outputs_to_review.keys()),
                    "issues_found": qa_results.count("Issue:")
                }
            )
            
        except Exception as e:
            logger.error(f"{self.name}: Execution failed: {e}")
            return self.format_result(
                output=None,
                success=False,
                error=str(e)
            )
    
    def _perform_qa_review(
        self,
        task: str,
        outputs: Dict[str, str],
        context: Dict[str, Any]
    ) -> str:
        """
        Perform comprehensive QA review
        
        Args:
            task: Original task
            outputs: Agent outputs to review
            context: Additional context
        
        Returns:
            QA review results
        """
        # Build review content
        review_content = []
        for agent_name, output in outputs.items():
            review_content.append(f"**{agent_name.title()} Output:**")
            review_content.append(str(output)[:1000])  # Limit length
            review_content.append("")
        
        content_str = "\n".join(review_content)
        
        # Create QA prompt
        qa_prompt = f"""Review the following agent outputs for quality and completeness.

Original Task: {task}

Agent Outputs:
{content_str}

Provide a comprehensive QA review including:

1. **Completeness Check**
   - Does it fully address the task?
   - Are all required elements present?

2. **Accuracy Check**
   - Are facts correct?
   - Is information accurate?
   - Any logical errors?

3. **Quality Check**
   - Is it well-structured?
   - Is it clear and understandable?
   - Professional quality?

4. **Issues Found**
   - List any problems or concerns
   - Severity: Critical/Major/Minor

5. **Recommendations**
   - Specific improvements needed
   - What should be added or changed?

6. **Final Assessment**
   - Pass/Needs Revision/Fail
   - Overall quality score (1-10)

Be thorough and specific."""
        
        messages = self._build_messages(qa_prompt, context)
        review = self._call_llm(messages, temperature=0.3, max_tokens=1500)
        
        return review
    
    def check_facts(self, content: str, sources: List[str]) -> Dict[str, Any]:
        """
        Verify facts against sources
        
        Args:
            content: Content to check
            sources: Source materials
        
        Returns:
            Fact check results
        """
        sources_text = "\n\n".join(sources) if sources else "No sources provided"
        
        fact_check_prompt = f"""Verify the facts in this content against the sources.

Content:
{content[:1000]}

Sources:
{sources_text[:1000]}

For each claim:
1. Identify the claim
2. Check against sources
3. Mark as: Verified/Unverified/Contradicted

Provide detailed fact check results."""
        
        messages = self._build_messages(fact_check_prompt)
        fact_check = self._call_llm(messages, temperature=0.2)
        
        return {
            "fact_check": fact_check,
            "sources_used": len(sources)
        }
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validate code quality
        
        Args:
            code: Code to validate
        
        Returns:
            Validation results
        """
        validation_prompt = f"""Review this code for:
1. Syntax errors
2. Logic errors
3. Security issues
4. Best practices
5. Performance concerns

Code:
```python
{code}
```

Provide specific issues and recommendations."""
        
        messages = self._build_messages(validation_prompt)
        validation = self._call_llm(messages, temperature=0.2)
        
        return {
            "validation": validation,
            "code_length": len(code)
        }