"""
Configuration management for Multi-Agent LLM System
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    serpapi_api_key: Optional[str] = None  # For web search
    tavily_api_key: Optional[str] = None   # Alternative search
    
    # Agent Settings
    orchestrator_model: str = "gpt-4"
    agent_model: str = "gpt-4"
    agent_temperature: float = 0.7
    max_iterations: int = 10
    timeout_seconds: int = 300
    
    # Code Execution Settings
    enable_code_execution: bool = True
    code_timeout: int = 30
    max_memory_mb: int = 512
    allowed_packages: List[str] = [
        "pandas", "numpy", "matplotlib", "plotly", 
        "scikit-learn", "requests", "beautifulsoup4"
    ]
    
    # Search Settings
    max_search_results: int = 10
    search_timeout: int = 10
    
    # File Paths
    workspace_dir: str = "workspace"
    logs_dir: str = "logs"
    cache_dir: str = "cache"
    
    # Application Settings
    app_name: str = "Multi-Agent LLM System"
    debug: bool = False
    log_level: str = "INFO"
    
    # UI Settings
    show_agent_thoughts: bool = True
    show_tool_usage: bool = True
    stream_output: bool = True
    
    # Performance Settings
    max_concurrent_agents: int = 3
    agent_retry_attempts: int = 2
    cache_results: bool = True
    
    # Safety Settings
    enable_human_approval: bool = False
    dangerous_actions_require_approval: bool = True
    max_file_size_mb: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()

# Ensure directories exist
Path(settings.workspace_dir).mkdir(parents=True, exist_ok=True)
Path(settings.logs_dir).mkdir(parents=True, exist_ok=True)
Path(settings.cache_dir).mkdir(parents=True, exist_ok=True)


# Agent Configurations
AGENT_CONFIGS = {
    "orchestrator": {
        "name": "Orchestrator",
        "role": "Task Coordinator",
        "model": settings.orchestrator_model,
        "temperature": 0.3,
        "system_prompt": """You are an orchestrator agent that coordinates multiple specialized agents.
Your role is to:
1. Analyze incoming tasks
2. Break them down into subtasks
3. Route subtasks to appropriate agents
4. Synthesize results into a final output

Available agents:
- Research Agent: Web search, information gathering
- Code Agent: Write and execute code
- Data Agent: Data analysis and visualization
- Writing Agent: Content creation and editing
- QA Agent: Quality assurance and validation

You must decide which agents to use and in what order."""
    },
    
    "research": {
        "name": "Research Agent",
        "role": "Information Gatherer",
        "model": settings.agent_model,
        "temperature": 0.5,
        "system_prompt": """You are a research agent specialized in gathering information.
Your capabilities:
- Web search and information retrieval
- Fact verification
- Source citation
- Data collection

Always provide sources and verify information accuracy.""",
        "tools": ["web_search", "web_scrape", "wikipedia"]
    },
    
    "code": {
        "name": "Code Agent",
        "role": "Software Developer",
        "model": settings.agent_model,
        "temperature": 0.2,
        "system_prompt": """You are a code agent specialized in writing and executing code.
Your capabilities:
- Python code generation
- Code execution
- Debugging
- Package installation

Always write clean, well-documented code with error handling.""",
        "tools": ["python_repl", "code_executor", "file_operations"]
    },
    
    "data": {
        "name": "Data Agent",
        "role": "Data Analyst",
        "model": settings.agent_model,
        "temperature": 0.3,
        "system_prompt": """You are a data agent specialized in data analysis.
Your capabilities:
- Data processing with pandas
- Statistical analysis
- Visualization with plotly/matplotlib
- Machine learning basics

Always explain your analysis and provide visualizations.""",
        "tools": ["pandas_operations", "visualization", "statistics"]
    },
    
    "writing": {
        "name": "Writing Agent",
        "role": "Content Creator",
        "model": settings.agent_model,
        "temperature": 0.8,
        "system_prompt": """You are a writing agent specialized in content creation.
Your capabilities:
- Article and report writing
- Editing and proofreading
- Format adaptation (markdown, HTML, etc.)
- Style customization

Always create engaging, well-structured content.""",
        "tools": ["text_generation", "markdown_formatting", "grammar_check"]
    },
    
    "qa": {
        "name": "QA Agent",
        "role": "Quality Assurance",
        "model": settings.agent_model,
        "temperature": 0.2,
        "system_prompt": """You are a QA agent specialized in validation.
Your capabilities:
- Fact checking
- Quality review
- Error detection
- Completeness verification

Always provide specific feedback and improvement suggestions.""",
        "tools": ["fact_check", "quality_metrics", "validation"]
    }
}


# Tool Configurations
TOOL_CONFIGS = {
    "web_search": {
        "name": "Web Search",
        "description": "Search the web for information",
        "max_results": settings.max_search_results,
        "timeout": settings.search_timeout
    },
    
    "python_repl": {
        "name": "Python REPL",
        "description": "Execute Python code",
        "timeout": settings.code_timeout,
        "memory_limit_mb": settings.max_memory_mb,
        "sandbox": True
    },
    
    "file_operations": {
        "name": "File Operations",
        "description": "Read and write files",
        "max_file_size_mb": settings.max_file_size_mb,
        "allowed_extensions": [".txt", ".csv", ".json", ".md"]
    },
    
    "visualization": {
        "name": "Data Visualization",
        "description": "Create charts and graphs",
        "libraries": ["plotly", "matplotlib", "seaborn"]
    }
}


# Workflow Templates
WORKFLOW_TEMPLATES = {
    "research_report": {
        "name": "Research Report",
        "description": "Create a comprehensive research report",
        "agents": ["research", "data", "writing", "qa"],
        "steps": [
            {"agent": "research", "action": "gather_information"},
            {"agent": "data", "action": "analyze_data"},
            {"agent": "writing", "action": "create_report"},
            {"agent": "qa", "action": "review_quality"}
        ]
    },
    
    "data_analysis": {
        "name": "Data Analysis",
        "description": "Analyze dataset and generate insights",
        "agents": ["code", "data", "writing"],
        "steps": [
            {"agent": "code", "action": "load_and_clean_data"},
            {"agent": "data", "action": "perform_analysis"},
            {"agent": "data", "action": "create_visualizations"},
            {"agent": "writing", "action": "summarize_insights"}
        ]
    },
    
    "code_project": {
        "name": "Code Project",
        "description": "Generate code with tests and documentation",
        "agents": ["code", "qa", "writing"],
        "steps": [
            {"agent": "code", "action": "generate_code"},
            {"agent": "code", "action": "write_tests"},
            {"agent": "qa", "action": "code_review"},
            {"agent": "writing", "action": "create_documentation"}
        ]
    }
}