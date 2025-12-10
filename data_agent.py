"""
Data Agent - Specialized in data analysis and visualization
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import json
from io import StringIO

from base_agent import ToolUsingAgent, AgentState
from config import settings

logger = logging.getLogger(__name__)


class DataAgent(ToolUsingAgent):
    """Agent specialized in data analysis and visualization"""
    
    def __init__(self):
        super().__init__("data")
        
        # Register tools
        self.register_tool("load_csv", self._load_csv)
        self.register_tool("analyze_data", self._analyze_data)
        self.register_tool("create_visualization", self._create_visualization)
        self.register_tool("statistical_summary", self._statistical_summary)
    
    def execute(self, task: str, state: AgentState) -> Dict[str, Any]:
        """
        Execute data analysis task
        
        Args:
            task: Data analysis task description
            state: Shared agent state
        
        Returns:
            Analysis results and visualizations
        """
        try:
            logger.info(f"{self.name}: Starting data analysis task")
            
            # Check if data is provided in context
            data = state.context.get("data")
            data_file = state.context.get("data_file")
            
            # Load data if file provided
            if data_file and data is None:
                data = self._load_csv(data_file)
                state.update_context({"data": data})
            
            # Perform analysis
            analysis_result = self._perform_analysis(
                task=task,
                data=data,
                context=state.context
            )
            
            # Store in state
            state.update_context({
                "data_analysis": analysis_result,
                "analysis_metadata": {
                    "rows": len(data) if data is not None else 0,
                    "columns": len(data.columns) if data is not None else 0
                }
            })
            
            return self.format_result(
                output=analysis_result,
                success=True,
                metadata={
                    "has_data": data is not None,
                    "analysis_type": "comprehensive"
                }
            )
            
        except Exception as e:
            logger.error(f"{self.name}: Execution failed: {e}")
            return self.format_result(
                output=None,
                success=False,
                error=str(e)
            )
    
    def _load_csv(self, filepath: str) -> pd.DataFrame:
        """
        Load CSV file into DataFrame
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            Pandas DataFrame
        """
        try:
            logger.info(f"{self.name}: Loading CSV from {filepath}")
            df = pd.read_csv(filepath)
            logger.info(f"{self.name}: Loaded {len(df)} rows, {len(df.columns)} columns")
            return df
        except Exception as e:
            logger.error(f"{self.name}: Failed to load CSV: {e}")
            raise
    
    def _analyze_data(
        self,
        data: pd.DataFrame,
        analysis_type: str = "summary"
    ) -> Dict[str, Any]:
        """
        Analyze DataFrame
        
        Args:
            data: DataFrame to analyze
            analysis_type: Type of analysis (summary, correlation, trends)
        
        Returns:
            Analysis results
        """
        results = {}
        
        if analysis_type == "summary":
            results["shape"] = data.shape
            results["columns"] = list(data.columns)
            results["dtypes"] = data.dtypes.to_dict()
            results["missing"] = data.isnull().sum().to_dict()
            results["statistics"] = data.describe().to_dict()
        
        elif analysis_type == "correlation":
            numeric_cols = data.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 1:
                results["correlation"] = data[numeric_cols].corr().to_dict()
        
        elif analysis_type == "trends":
            numeric_cols = data.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                results[col] = {
                    "mean": float(data[col].mean()),
                    "trend": "increasing" if data[col].is_monotonic_increasing else "varying"
                }
        
        return results
    
    def _statistical_summary(self, data: pd.DataFrame) -> str:
        """
        Generate statistical summary
        
        Args:
            data: DataFrame to summarize
        
        Returns:
            Summary text
        """
        summary_parts = [
            f"Dataset Shape: {data.shape[0]} rows × {data.shape[1]} columns",
            f"\nColumns: {', '.join(data.columns)}",
            f"\nData Types:\n{data.dtypes.to_string()}",
            f"\n\nStatistical Summary:\n{data.describe().to_string()}"
        ]
        
        # Check for missing values
        missing = data.isnull().sum()
        if missing.any():
            summary_parts.append(f"\n\nMissing Values:\n{missing[missing > 0].to_string()}")
        
        return "\n".join(summary_parts)
    
    def _create_visualization(
        self,
        data: pd.DataFrame,
        chart_type: str = "auto",
        x_column: Optional[str] = None,
        y_column: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create visualization specification
        
        Args:
            data: DataFrame to visualize
            chart_type: Type of chart (bar, line, scatter, auto)
            x_column: X-axis column
            y_column: Y-axis column
        
        Returns:
            Visualization specification
        """
        # This returns a specification that could be used with Plotly
        # In a real implementation, this would generate actual charts
        
        viz_spec = {
            "type": chart_type,
            "data": data.head(100).to_dict('records'),  # Limit for performance
            "x": x_column,
            "y": y_column,
            "title": f"{y_column} vs {x_column}" if x_column and y_column else "Data Visualization"
        }
        
        return viz_spec
    
    def _perform_analysis(
        self,
        task: str,
        data: Optional[pd.DataFrame],
        context: Dict[str, Any]
    ) -> str:
        """
        Perform comprehensive data analysis
        
        Args:
            task: Analysis task
            data: DataFrame to analyze
            context: Additional context
        
        Returns:
            Analysis report
        """
        if data is None:
            return "No data available for analysis. Please provide a dataset."
        
        # Get statistical summary
        stats_summary = self._statistical_summary(data)
        
        # Perform basic analysis
        analysis = self._analyze_data(data, "summary")
        
        # Build context for LLM
        analysis_context = f"""Dataset Information:
{stats_summary}

Analysis Results:
{json.dumps(analysis, indent=2, default=str)}
"""
        
        # Use LLM to interpret and explain
        analysis_prompt = f"""Analyze this dataset and provide insights for the task: {task}

{analysis_context}

Provide:
1. **Key Findings** - What stands out in the data?
2. **Patterns & Trends** - What patterns do you see?
3. **Insights** - What insights can be drawn?
4. **Recommendations** - What actions or further analysis would you recommend?

Format as a clear, structured analysis."""
        
        messages = self._build_messages(analysis_prompt, context)
        analysis_result = self._call_llm(messages, temperature=0.3, max_tokens=1500)
        
        return analysis_result
    
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess data
        
        Args:
            data: DataFrame to clean
        
        Returns:
            Cleaned DataFrame
        """
        logger.info(f"{self.name}: Cleaning data")
        
        cleaned = data.copy()
        
        # Remove duplicates
        cleaned = cleaned.drop_duplicates()
        
        # Handle missing values (simple strategy)
        # Numeric: fill with median
        numeric_cols = cleaned.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            cleaned[col].fillna(cleaned[col].median(), inplace=True)
        
        # Categorical: fill with mode
        categorical_cols = cleaned.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            cleaned[col].fillna(cleaned[col].mode()[0] if len(cleaned[col].mode()) > 0 else "Unknown", inplace=True)
        
        logger.info(f"{self.name}: Cleaned data - removed {len(data) - len(cleaned)} duplicate rows")
        
        return cleaned
    
    def find_correlations(
        self,
        data: pd.DataFrame,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find strong correlations in data
        
        Args:
            data: DataFrame to analyze
            threshold: Correlation threshold (0-1)
        
        Returns:
            List of correlation findings
        """
        numeric_cols = data.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) < 2:
            return []
        
        corr_matrix = data[numeric_cols].corr()
        
        findings = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) >= threshold:
                    findings.append({
                        "column1": corr_matrix.columns[i],
                        "column2": corr_matrix.columns[j],
                        "correlation": float(corr_value),
                        "strength": "strong" if abs(corr_value) > 0.7 else "moderate"
                    })
        
        return findings
    
    def generate_insights(self, data: pd.DataFrame) -> str:
        """
        Generate insights from data using LLM
        
        Args:
            data: DataFrame to analyze
        
        Returns:
            Insights text
        """
        # Get summary statistics
        stats = data.describe().to_string()
        
        # Get correlations
        correlations = self.find_correlations(data)
        corr_text = "\n".join(
            f"- {c['column1']} and {c['column2']}: {c['correlation']:.2f} ({c['strength']})"
            for c in correlations
        )
        
        insights_prompt = f"""Analyze this dataset and provide key insights:

Statistical Summary:
{stats}

Correlations:
{corr_text if corr_text else "No strong correlations found"}

Provide 5-7 key insights about this data, focusing on:
- Notable patterns
- Outliers or anomalies  
- Business implications
- Potential opportunities or risks"""
        
        messages = self._build_messages(insights_prompt)
        insights = self._call_llm(messages, temperature=0.4)
        
        return insights
