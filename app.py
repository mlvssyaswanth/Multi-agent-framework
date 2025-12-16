"""
Streamlit UI for Multi-Agent Coding Framework.
Provides interactive interface for user requirements and displays all agent outputs.
"""
import streamlit as st
import sys
import os
import logging
from orchestrator import Orchestrator
from utils.config import Config
from utils.logger import setup_logging, get_logger

# Setup logging
setup_logging(
    level=logging.INFO,
    log_to_file=True,
    log_file_path="logs/streamlit_app.log"
)
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Coding Framework",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-section {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: transparent;
        border: 1px solid #c3e6cb;
        color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if "orchestrator" not in st.session_state:
        try:
            # Force reload config to get latest model settings
            import importlib
            import utils.config
            importlib.reload(utils.config)
            st.session_state.orchestrator = Orchestrator()
        except ValueError as e:
            st.error(f"Configuration Error: {str(e)}")
            st.stop()
        except Exception as e:
            st.error(f"Initialization Error: {str(e)}")
            st.stop()
    
    if "results" not in st.session_state:
        st.session_state.results = None
    
    if "processing" not in st.session_state:
        st.session_state.processing = False
    
    if "stop_requested" not in st.session_state:
        st.session_state.stop_requested = False


def display_requirements(results: dict):
    """Display requirement analysis results."""
    st.subheader("📋 Requirement Analysis")
    
    requirements = results.get("requirements", {})
    
    # Display ambiguity information if available
    ambiguity_detected = requirements.get("ambiguity_detected", False)
    clarifying_questions = requirements.get("clarifying_questions", [])
    ambiguity_notes = requirements.get("ambiguity_notes", "")
    
    if ambiguity_detected or clarifying_questions:
        with st.expander("🔍 Ambiguity Detection & Clarifying Questions", expanded=True):
            if ambiguity_detected:
                st.warning("⚠️ Ambiguity detected in requirements")
            if ambiguity_notes:
                st.info(f"**Notes:** {ambiguity_notes}")
            if clarifying_questions:
                st.markdown("**Clarifying Questions Generated:**")
                for i, question in enumerate(clarifying_questions, 1):
                    st.markdown(f"{i}. {question}")
            else:
                st.info("No specific clarifying questions generated")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Functional Requirements:**")
        func_reqs = requirements.get("functional_requirements", [])
        if func_reqs:
            for req in func_reqs:
                st.markdown(f"- {req}")
        else:
            st.info("No functional requirements extracted")
        
        st.markdown("**Assumptions:**")
        assumptions = requirements.get("assumptions", [])
        if assumptions:
            for assumption in assumptions:
                st.markdown(f"- {assumption}")
        else:
            st.info("No assumptions identified")
    
    with col2:
        st.markdown("**Non-Functional Requirements:**")
        non_func_reqs = requirements.get("non_functional_requirements", [])
        if non_func_reqs:
            for req in non_func_reqs:
                st.markdown(f"- {req}")
        else:
            st.info("No non-functional requirements extracted")
        
        st.markdown("**Constraints:**")
        constraints = requirements.get("constraints", [])
        if constraints:
            for constraint in constraints:
                st.markdown(f"- {constraint}")
        else:
            st.info("No constraints identified")


def display_code(results: dict):
    """Display generated code."""
    st.subheader("💻 Generated Code")
    
    code = results.get("code", "")
    if code:
        st.code(code, language="python")
        
        # Download button for code
        st.download_button(
            label="📥 Download Code",
            data=code,
            file_name="generated_code.py",
            mime="text/x-python"
        )
    else:
        st.error("No code generated")


def display_review_feedback(results: dict):
    """Display code review feedback."""
    st.subheader("🔍 Code Review")
    
    feedbacks = results.get("review_feedback", [])
    iterations = results.get("iterations", 0)
    
    st.info(f"Total Iterations: {iterations}")
    
    if feedbacks:
        for i, feedback in enumerate(feedbacks, 1):
            with st.expander(f"Iteration {i} Feedback", expanded=(i == len(feedbacks))):
                if feedback.upper().startswith("APPROVED"):
                    st.success(feedback)
                else:
                    st.warning(feedback)
    else:
        st.info("No review feedback available")


def display_documentation(results: dict):
    """Display generated documentation."""
    st.subheader("📚 Documentation")
    
    documentation = results.get("documentation", "")
    if documentation:
        # Show table of contents indicator
        if "##" in documentation or "#" in documentation:
            st.markdown("#### 📑 Documentation Structure")
            st.success("✅ Documentation includes: Overview, Agent Overview, Workflow, Setup, Usage, API Reference, and Examples")
        
        # Display documentation with better formatting
        st.markdown(documentation)
        
        # Download button for documentation
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Documentation",
                data=documentation,
                file_name="documentation.md",
                mime="text/markdown",
                use_container_width=True
            )
    else:
        st.info("No documentation generated")


def display_test_cases(results: dict):
    """Display generated test cases."""
    st.subheader("🧪 Test Cases")
    
    test_cases = results.get("test_cases", "")
    if test_cases:
        # Show test code
        with st.expander("📝 View Test Code", expanded=True):
            st.code(test_cases, language="python")
        
        # Execution results section
        st.markdown("#### 📊 Test Execution Information")
        st.info("""
        **Note:** The test cases include expected execution results in comments.
        To execute the tests:
        1. Save the generated code to a file (e.g., `generated_code.py`)
        2. Save the test cases to `test_generated_code.py`
        3. Run: `pytest test_generated_code.py -v`
        """)
        
        # Download button for test cases
        st.download_button(
            label="📥 Download Test Cases",
            data=test_cases,
            file_name="test_generated_code.py",
            mime="text/x-python"
        )
    else:
        st.info("No test cases generated")


def display_deployment_config(results: dict):
    """Display deployment configuration."""
    st.subheader("🚀 Deployment Configuration")
    
    deployment = results.get("deployment_config", {})
    
    if deployment:
        # Requirements.txt
        st.markdown("**requirements.txt:**")
        requirements = deployment.get("requirements", "")
        if requirements:
            st.code(requirements, language="text")
            st.download_button(
                label="📥 Download requirements.txt",
                data=requirements,
                file_name="requirements.txt",
                mime="text/plain"
            )
        
        # Setup Instructions
        st.markdown("**Setup Instructions:**")
        setup = deployment.get("setup_instructions", "")
        if setup:
            st.markdown(setup)
        
        # Run Script
        st.markdown("**Run Script:**")
        run_script = deployment.get("run_script", "")
        if run_script:
            st.code(run_script, language="bash")
            st.download_button(
                label="📥 Download run.sh",
                data=run_script,
                file_name="run.sh",
                mime="text/x-sh"
            )
    else:
        st.info("No deployment configuration generated")


def main():
    """Main Streamlit application."""
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🤖 Multi-Agent Coding Framework</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.info(f"Model: {Config.MODEL}")
        st.info(f"Max Iterations: {Config.MAX_ITERATIONS}")
        
        st.header("📖 Instructions")
        st.markdown("""
        1. Enter your software requirements in natural language
        2. Click 'Generate Code' to start the multi-agent pipeline
        3. Review outputs from each agent:
           - Requirement Analysis
           - Generated Code
           - Code Review Feedback
           - Documentation
           - Test Cases
           - Deployment Configuration
        4. Download any generated files as needed
        """)
        
        if st.button("🔄 Clear Results"):
            st.session_state.results = None
            st.rerun()
    
    # Main content area
    st.header("📝 Enter Requirements")
    
    # Input validation helper
    with st.expander("ℹ️  How to Write Good Requirements", expanded=False):
        st.markdown("""
        **Tips for best results:**
        - Be specific about functionality needed
        - Mention any constraints or requirements
        - Include examples if helpful
        - Specify input/output formats if relevant
        
        **Example:**
        ```
        Create a Python calculator that can perform basic arithmetic operations 
        (addition, subtraction, multiplication, division) with error handling 
        for division by zero. The calculator should accept two numbers and an 
        operation as input, and return the result.
        ```
        """)
    
    user_input = st.text_area(
        "Describe your software requirements:",
        height=150,
        placeholder="Example: Create a Python calculator that can perform basic arithmetic operations (addition, subtraction, multiplication, division) with error handling for division by zero.",
        help="Enter detailed requirements for the software you want to generate. Be as specific as possible for best results."
    )
    
    # Input validation
    input_valid = True
    if user_input:
        if len(user_input.strip()) < 10:
            st.warning("⚠️  Input is very short. Please provide more detailed requirements for better results.")
        if len(user_input) > 5000:
            st.error("❌ Input is too long. Please keep requirements under 5000 characters.")
            input_valid = False
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        generate_button = st.button("🚀 Generate Code", type="primary", use_container_width=True, disabled=not input_valid or st.session_state.get("processing", False))
    with col2:
        if st.button("📋 Load Example", use_container_width=True):
            example_text = """Create a Python calculator that can perform basic arithmetic operations 
(addition, subtraction, multiplication, division) with error handling for division by zero. 
The calculator should accept two numbers and an operation as input, and return the result. 
Include proper input validation and user-friendly error messages."""
            st.session_state.example_loaded = example_text
            st.rerun()
    with col3:
        stop_button = st.button("⏹️ Stop", use_container_width=True, disabled=not st.session_state.get("processing", False))
        if stop_button:
            st.session_state.stop_requested = True
            st.session_state.processing = False
            st.warning("⏹️ Stop requested. Execution will stop after current step completes.")
            st.rerun()
    
    # Load example if requested
    if "example_loaded" in st.session_state:
        user_input = st.session_state.example_loaded
        del st.session_state.example_loaded
    
    # Process user input
    if generate_button:
        if not user_input or not user_input.strip():
            st.error("❌ Please enter your requirements before generating code.")
        elif len(user_input.strip()) < 10:
            st.warning("⚠️  Requirements are too short. Please provide more details for better results.")
        else:
            st.session_state.processing = True
            st.session_state.results = None
            st.session_state.stop_requested = False
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Progress callback function
            def update_progress(progress: int, message: str):
                """Update progress bar and status text."""
                progress_bar.progress(progress)
                if progress < 100:
                    status_text.info(message)
                else:
                    status_text.success(message)
            
            # Stop check callback function
            def check_stop() -> bool:
                """Check if stop was requested."""
                return st.session_state.get("stop_requested", False)
            
            try:
                with st.spinner("🤖 Agents are working... This may take a few minutes."):
                    results = st.session_state.orchestrator.execute_pipeline(
                        user_input, 
                        progress_callback=update_progress,
                        stop_check=check_stop
                    )
                    
                    st.session_state.results = results
                    st.session_state.processing = False
                    st.session_state.stop_requested = False
                    
                    # Check if execution was stopped
                    if results.get("status") == "stopped":
                        st.warning("⏹️ Execution stopped by user. Partial results are shown below.")
                    
                    # Small delay to show completion
                    import time
                    time.sleep(0.5)
                    st.rerun()
            except ValueError as e:
                st.error(f"❌ Input Error: {str(e)}")
                st.info("💡 Tip: Make sure your requirements are clear and specific.")
                st.session_state.processing = False
                st.session_state.stop_requested = False
                progress_bar.empty()
                status_text.empty()
            except KeyboardInterrupt:
                st.warning("⏹️ Execution interrupted by user.")
                st.session_state.processing = False
                st.session_state.stop_requested = False
                progress_bar.empty()
                status_text.empty()
            except Exception as e:
                st.error(f"❌ Error during pipeline execution: {str(e)}")
                with st.expander("🔍 View Error Details"):
                    st.exception(e)
                st.session_state.processing = False
                st.session_state.stop_requested = False
                progress_bar.empty()
                status_text.empty()
    
    # Display results
    if st.session_state.results:
        results = st.session_state.results
        status = results.get("status", "unknown")
        
        if status == "completed":
            st.markdown('<div class="success-box">✅ Pipeline execution completed successfully!</div>', unsafe_allow_html=True)
        elif status == "stopped":
            st.markdown('<div class="error-box">⏹️ Pipeline execution stopped by user. Partial results are shown below.</div>', unsafe_allow_html=True)
        elif status == "failed":
            st.markdown('<div class="error-box">❌ Pipeline execution failed. Please check the error messages below.</div>', unsafe_allow_html=True)
        elif status == "error":
            st.markdown('<div class="error-box">❌ An error occurred during pipeline execution.</div>', unsafe_allow_html=True)
            if "error" in results:
                st.error(f"Error: {results['error']}")
        
        # Display all agent outputs (show partial results if stopped)
        if status in ["completed", "stopped"]:
            st.divider()
            if results.get("requirements"):
                display_requirements(results)
                st.divider()
            if results.get("code"):
                display_code(results)
                st.divider()
            if results.get("review_feedback"):
                display_review_feedback(results)
                st.divider()
            if results.get("documentation"):
                display_documentation(results)
                st.divider()
            if results.get("test_cases"):
                display_test_cases(results)
                st.divider()
            if results.get("deployment_config"):
                display_deployment_config(results)


if __name__ == "__main__":
    main()

