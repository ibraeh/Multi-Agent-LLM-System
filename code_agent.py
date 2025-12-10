"""
Code Agent - Specialized in code generation and execution
"""
import logging
from typing import Dict, Any, Optional
import subprocess
import sys
import tempfile
import os
from pathlib import Path

from base_agent import ToolUsingAgent, AgentState
from config import settings

logger = logging.getLogger(__name__)


class CodeAgent(ToolUsingAgent):
    """Agent specialized in code generation and execution"""
    
    def __init__(self):
        super().__init__("code")
        
        # Register tools
        self.register_tool("python_execute", self._execute_python)
        self.register_tool("write_file", self._write_file)
        self.register_tool("read_file", self._read_file)
        self.register_tool("install_package", self._install_package)
    
    def execute(self, task: str, state: AgentState) -> Dict[str, Any]:
        """
        Execute code-related task
        
        Args:
            task: Code generation/execution task
            state: Shared agent state
        
        Returns:
            Code and execution results
        """
        try:
            logger.info(f"{self.name}: Starting code task")
            
            # Generate code
            code = self._generate_code(task, state.context)
            
            # Execute if requested
            execution_result = None
            if settings.enable_code_execution and self._should_execute(task):
                logger.info(f"{self.name}: Executing generated code")
                execution_result = self._execute_python(code)
            
            # Store in state
            state.update_context({
                "generated_code": code,
                "execution_result": execution_result
            })
            
            # Format output
            output = f"**Generated Code:**\n```python\n{code}\n```\n"
            if execution_result:
                output += f"\n**Execution Result:**\n```\n{execution_result.get('output', '')}\n```"
            
            return self.format_result(
                output=output,
                success=True,
                metadata={
                    "code": code,
                    "executed": execution_result is not None,
                    "execution_result": execution_result
                }
            )
            
        except Exception as e:
            logger.error(f"{self.name}: Execution failed: {e}")
            return self.format_result(
                output=None,
                success=False,
                error=str(e)
            )
    
    def _generate_code(self, task: str, context: Dict[str, Any]) -> str:
        """
        Generate Python code for task
        
        Args:
            task: Task description
            context: Additional context
        
        Returns:
            Generated Python code
        """
        code_prompt = f"""Generate clean, well-documented Python code for this task:

{task}

Requirements:
1. Include docstrings
2. Add error handling
3. Use type hints
4. Follow PEP 8
5. Add helpful comments
6. Make it production-ready

Generate ONLY the code, no explanations."""
        
        messages = self._build_messages(code_prompt, context)
        code = self._call_llm(messages, temperature=0.2, max_tokens=2000)
        
        # Clean code output
        code = self._extract_code_block(code)
        
        return code
    
    def _extract_code_block(self, text: str) -> str:
        """Extract code from markdown code blocks"""
        # Remove markdown code fences
        if "```python" in text:
            text = text.split("```python")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        return text.strip()
    
    def _should_execute(self, task: str) -> bool:
        """Determine if code should be executed"""
        execute_keywords = ["execute", "run", "test", "output"]
        task_lower = task.lower()
        return any(keyword in task_lower for keyword in execute_keywords)
    
    def _execute_python(
        self,
        code: str,
        timeout: int = None
    ) -> Dict[str, Any]:
        """
        Execute Python code safely
        
        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds
        
        Returns:
            Execution results
        """
        if not settings.enable_code_execution:
            return {
                "success": False,
                "error": "Code execution is disabled"
            }
        
        timeout = timeout or settings.code_timeout
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute code in subprocess
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=settings.workspace_dir
                )
                
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None,
                    "return_code": result.returncode
                }
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                
        except subprocess.TimeoutExpired:
            logger.error(f"{self.name}: Code execution timeout")
            return {
                "success": False,
                "error": f"Execution timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"{self.name}: Code execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _write_file(
        self,
        filename: str,
        content: str,
        directory: str = None
    ) -> Dict[str, Any]:
        """
        Write content to file
        
        Args:
            filename: Name of file
            content: Content to write
            directory: Target directory (default: workspace)
        
        Returns:
            Write operation result
        """
        try:
            directory = directory or settings.workspace_dir
            filepath = Path(directory) / filename
            
            # Create directory if needed
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(filepath, 'w') as f:
                f.write(content)
            
            logger.info(f"{self.name}: Wrote file {filepath}")
            
            return {
                "success": True,
                "filepath": str(filepath),
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to write file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _read_file(self, filepath: str) -> Dict[str, Any]:
        """
        Read content from file
        
        Args:
            filepath: Path to file
        
        Returns:
            File content
        """
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to read file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _install_package(self, package: str) -> Dict[str, Any]:
        """
        Install Python package
        
        Args:
            package: Package name
        
        Returns:
            Installation result
        """
        # Check if package is allowed
        if package not in settings.allowed_packages:
            return {
                "success": False,
                "error": f"Package '{package}' not in allowed list"
            }
        
        try:
            logger.info(f"{self.name}: Installing package {package}")
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
            
        except Exception as e:
            logger.error(f"{self.name}: Package installation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_tests(self, code: str) -> str:
        """
        Generate unit tests for code
        
        Args:
            code: Code to test
        
        Returns:
            Generated test code
        """
        test_prompt = f"""Generate pytest unit tests for this code:

```python
{code}
```

Requirements:
1. Use pytest framework
2. Test all functions
3. Include edge cases
4. Add docstrings
5. Test error handling

Generate ONLY the test code."""
        
        messages = self._build_messages(test_prompt)
        tests = self._call_llm(messages, temperature=0.2)
        
        return self._extract_code_block(tests)
    
    def review_code(self, code: str) -> str:
        """
        Review code for issues
        
        Args:
            code: Code to review
        
        Returns:
            Code review feedback
        """
        review_prompt = f"""Review this code and provide feedback:

```python
{code}
```

Check for:
1. Bugs and errors
2. Performance issues
3. Security concerns
4. Code quality
5. Best practices

Provide specific, actionable feedback."""
        
        messages = self._build_messages(review_prompt)
        review = self._call_llm(messages, temperature=0.3)
        
        return review