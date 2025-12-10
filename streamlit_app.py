"""
Streamlit Web Interface for Multi-Agent LLM System
"""
import streamlit as st
import sys
from pathlib import Path
import time
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main_system import MultiAgentSystem


# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Multi-Agent LLM System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
    .agent-status {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: bold;
    }
    .agent-active {
        background-color: #28a745;
        color: white;
    }
    .agent-idle {
        background-color: #6c757d;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE
# ============================================================================

if 'system' not in st.session_state:
    st.session_state.system = None
    st.session_state.history = []
    st.session_state.current_result = None
    st.session_state.initialized = False


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=Multi-Agent+System", width="stretch")
    
    st.markdown("### 🎯 System Status")
    
    # Initialize system
    if not st.session_state.initialized:
        with st.spinner("Initializing Multi-Agent System..."):
            try:
                st.session_state.system = MultiAgentSystem()
                st.session_state.initialized = True
                st.success("✅ System initialized!")
            except Exception as e:
                st.error(f"❌ Initialization failed: {e}")
    
    # Agent status
    if st.session_state.initialized:
        st.markdown("### 🤖 Active Agents")
        
        agents = {
            "🔍 Research": "Gathers information from web",
            "💻 Code": "Generates and executes code",
            "📊 Data": "Analyzes and visualizes data",
            "✍️ Writing": "Creates written content",
            "✅ QA": "Ensures quality"
        }
        
        for agent_name, description in agents.items():
            with st.expander(agent_name):
                st.caption(description)
        
        # Statistics
        if st.button("📊 View Statistics"):
            stats = st.session_state.system.get_agent_stats()
            st.json(stats)
        
        # Clear history
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.session_state.current_result = None
            st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.caption("""
    This is a Multi-Agent LLM System where specialized AI agents 
    collaborate to solve complex tasks through autonomous coordination.
    """)


# ============================================================================
# MAIN AREA
# ============================================================================

st.markdown('<div class="main-header">🤖 Multi-Agent LLM System</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📜 History", "📊 Analytics", "⚙️ Settings"])


# ============================================================================
# TAB 1: CHAT INTERFACE
# ============================================================================

with tab1:
    st.markdown("### 💬 Ask the Multi-Agent System")
    st.caption("Enter your task and watch specialized agents collaborate to solve it!")
    
    # Example tasks
    with st.expander("💡 Example Tasks"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Research & Analysis:**
            - Research AI trends in 2025
            - Compare Python vs JavaScript for web development
            - Analyze the impact of remote work
            """)
        
        with col2:
            st.markdown("""
            **Data & Code:**
            - Write a Python script to analyze CSV data
            - Create a data visualization for sales trends
            - Build a REST API for a todo app
            """)
    
    # Task input
    task_input = st.text_area(
        "Enter your task:",
        height=100,
        placeholder="Example: Research the latest developments in AI and create a summary report"
    )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col1, col2 = st.columns(2)
        with col1:
            max_iterations = st.slider("Max Iterations", 1, 20, 10)
        with col2:
            temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    
    # Execute button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        execute_button = st.button("🚀 Execute Task", type="primary", width="stretch")
    
    # Execute task
    if execute_button and task_input:
        if not st.session_state.initialized:
            st.error("❌ System not initialized. Please check the sidebar.")
        else:
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Agent activity container
            agent_activity = st.container()
            
            with agent_activity:
                st.markdown("#### 🔄 Agent Activity")
                activity_placeholder = st.empty()
            
            try:
                # Start execution
                status_text.text("🚀 Starting task execution...")
                progress_bar.progress(10)
                
                start_time = time.time()
                
                # Execute
                status_text.text("🤖 Agents are working...")
                progress_bar.progress(30)
                
                result = st.session_state.system.execute(task_input)
                
                progress_bar.progress(90)
                
                # Store result
                st.session_state.current_result = result
                st.session_state.history.append(result)
                
                progress_bar.progress(100)
                execution_time = time.time() - start_time
                
                # Clear progress
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                
                # Display results
                st.markdown("---")
                st.markdown("### 📊 Results")
                
                if result.get("success"):
                    st.success(f"✅ Task completed in {execution_time:.2f}s")
                    
                    # Output
                    st.markdown("#### 📄 Output")
                    st.markdown(result.get("output", "No output"))
                    
                    # Metadata
                    with st.expander("📋 Execution Details"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Execution Time", f"{result.get('execution_time', 0):.2f}s")
                        
                        with col2:
                            summary = result.get("summary", {})
                            agents_used = summary.get("agents_used", {})
                            st.metric("Agents Used", len(agents_used))
                        
                        with col3:
                            st.metric("Iterations", summary.get("total_iterations", 0))
                        
                        st.json(result.get("summary", {}))
                
                else:
                    st.error(f"❌ Task failed: {result.get('error')}")
                
            except Exception as e:
                st.error(f"❌ Execution error: {e}")
                progress_bar.empty()
                status_text.empty()


# ============================================================================
# TAB 2: HISTORY
# ============================================================================

with tab2:
    st.markdown("### 📜 Execution History")
    
    if not st.session_state.history:
        st.info("No execution history yet. Run a task to see results here!")
    else:
        # Display history in reverse order (newest first)
        for i, result in enumerate(reversed(st.session_state.history)):
            with st.expander(
                f"{'✅' if result.get('success') else '❌'} "
                f"{result.get('task', 'Unknown task')[:100]}... "
                f"({result.get('timestamp', 'Unknown time')})"
            ):
                st.markdown(f"**Task:** {result.get('task')}")
                st.markdown(f"**Status:** {'Success' if result.get('success') else 'Failed'}")
                st.markdown(f"**Time:** {result.get('execution_time', 0):.2f}s")
                
                if result.get('success'):
                    st.markdown("**Output:**")
                    st.markdown(result.get('output', 'No output'))
                else:
                    st.error(f"Error: {result.get('error')}")
                
                # Download button
                st.download_button(
                    label="📥 Download Result",
                    data=json.dumps(result, indent=2),
                    file_name=f"result_{i+1}.json",
                    mime="application/json"
                )


# ============================================================================
# TAB 3: ANALYTICS
# ============================================================================

with tab3:
    st.markdown("### 📊 System Analytics")
    
    if st.session_state.initialized and st.session_state.history:
        # Overall stats
        total_tasks = len(st.session_state.history)
        successful_tasks = sum(1 for r in st.session_state.history if r.get('success'))
        failed_tasks = total_tasks - successful_tasks
        avg_time = sum(r.get('execution_time', 0) for r in st.session_state.history) / total_tasks if total_tasks > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tasks", total_tasks)
        with col2:
            st.metric("Successful", successful_tasks, delta=f"{successful_tasks/total_tasks*100:.0f}%")
        with col3:
            st.metric("Failed", failed_tasks)
        with col4:
            st.metric("Avg Time", f"{avg_time:.2f}s")
        
        # Agent statistics
        st.markdown("#### 🤖 Agent Statistics")
        
        if st.button("Refresh Stats"):
            stats = st.session_state.system.get_agent_stats()
            
            st.json(stats)
    
    else:
        st.info("Run some tasks to see analytics!")


# ============================================================================
# TAB 4: SETTINGS
# ============================================================================

with tab4:
    st.markdown("### ⚙️ System Settings")
    
    st.markdown("#### 🔑 API Configuration")
    st.info("API keys are loaded from .env file. Please configure them there.")
    
    st.markdown("#### 🎛️ Agent Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Default Model", value="gpt-5 nano", disabled=True)
        st.slider("Default Temperature", 0.0, 1.0, 0.7, 0.1, disabled=True)
    
    with col2:
        st.number_input("Max Iterations", value=10, disabled=True)
        st.number_input("Timeout (seconds)", value=300, disabled=True)
    
    st.caption("Note: Settings are currently read-only. Modify config.py to change settings.")
    
    st.markdown("---")
    st.markdown("#### 🛠️ System Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reset Stats"):
            if st.session_state.initialized:
                st.session_state.system.reset_stats()
                st.success("Statistics reset!")
    
    with col2:
        if st.button("🗑️ Clear Cache"):
            st.cache_data.clear()
            st.success("Cache cleared!")
    
    with col3:
        if st.button("♻️ Restart System"):
            st.session_state.initialized = False
            st.session_state.system = None
            st.rerun()


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Multi-Agent LLM System v1.0 | Built with Streamlit & LangChain | 
        <a href='https://github.com/yourusername/multi-agent-system'>GitHub</a></p>
    </div>
    """,
    unsafe_allow_html=True
)
