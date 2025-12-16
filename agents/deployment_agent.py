"""
Deployment Configuration Agent - Generates deployment files and instructions.
"""
from typing import Dict
from autogen import ConversableAgent
from utils.config import Config
from utils.logger import get_logger, log_agent_activity, log_api_call

logger = get_logger(__name__)


class DeploymentAgent:
    """Agent responsible for generating deployment configuration files."""
    
    def __init__(self):
        """Initialize the Deployment Configuration Agent."""
        self.agent = ConversableAgent(
            name="deployment_specialist",
            system_message="""You are a DevOps Engineer specializing in Python project deployment and configuration.

Your responsibilities:
1. Generate requirements.txt with all necessary dependencies
2. Create clear project setup instructions
3. Generate run scripts for different platforms
4. Ensure reproducibility and simplicity

Output Format:
Provide your output as structured text that can be parsed into:
- requirements.txt content
- Setup instructions
- Run script content

Focus on:
- Complete dependency lists
- Clear, step-by-step instructions
- Cross-platform compatibility where possible
- Simplicity and ease of use""",
            llm_config={
                "config_list": [{
                    "model": Config.MODEL,
                    "api_key": Config.OPENAI_API_KEY,
                    "temperature": Config.TEMPERATURE,
                }],
                "timeout": 120,
            },
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
        )
    
    def generate_deployment_config(self, code: str, requirements: Dict) -> Dict[str, str]:
        """
        Generate deployment configuration files.
        
        Args:
            code: Generated Python code
            requirements: Original requirements dictionary
            
        Returns:
            Dictionary with 'requirements', 'setup_instructions', and 'run_script' keys
        """
        req_text = self._format_requirements(requirements)
        
        log_agent_activity(logger, "DeploymentAgent", "Generating deployment config", {"code_length": len(code)})
        
        prompt = f"""Generate deployment configuration for the following Python project:

ORIGINAL REQUIREMENTS:
{req_text}

GENERATED CODE:
```python
{code}
```

Generate:
1. requirements.txt - List all Python dependencies needed (include versions where critical)
2. Setup Instructions - Step-by-step instructions for setting up and running the project
3. Run Script - A shell script (run.sh) that can be used to run the project

Format your response clearly with sections marked as:
[REQUIREMENTS]
[SETUP_INSTRUCTIONS]
[RUN_SCRIPT]"""
        
        log_api_call(logger, "DeploymentAgent", Config.MODEL, len(prompt))
        
        response = self.agent.generate_reply(
            messages=[{"role": "user", "content": prompt}]
        )
        
        if response is None:
            raise ValueError("Agent returned None response. Check API key and model configuration.")
        
        content = response.get("content", "") if isinstance(response, dict) else str(response)
        
        return self._parse_deployment_output(content)
    
    def _format_requirements(self, requirements: Dict) -> str:
        """Format requirements for deployment context."""
        text = "FUNCTIONAL REQUIREMENTS:\n"
        for req in requirements.get("functional_requirements", []):
            text += f"- {req}\n"
        
        return text
    
    def _parse_deployment_output(self, content: str) -> Dict[str, str]:
        """Parse the agent's output into structured deployment config."""
        requirements = ""
        setup_instructions = ""
        run_script = ""
        
        if "[REQUIREMENTS]" in content:
            req_start = content.find("[REQUIREMENTS]") + len("[REQUIREMENTS]")
            req_end = content.find("[SETUP_INSTRUCTIONS]", req_start)
            if req_end == -1:
                req_end = content.find("[RUN_SCRIPT]", req_start)
            if req_end > req_start:
                requirements = content[req_start:req_end].strip()
        
        if "[SETUP_INSTRUCTIONS]" in content:
            setup_start = content.find("[SETUP_INSTRUCTIONS]") + len("[SETUP_INSTRUCTIONS]")
            setup_end = content.find("[RUN_SCRIPT]", setup_start)
            if setup_end > setup_start:
                setup_instructions = content[setup_start:setup_end].strip()
        
        if "[RUN_SCRIPT]" in content:
            script_start = content.find("[RUN_SCRIPT]") + len("[RUN_SCRIPT]")
            run_script = content[script_start:].strip()
        
        if not requirements:
            requirements = self._generate_default_requirements()
        
        if not setup_instructions:
            setup_instructions = self._generate_default_setup()
        
        if not run_script:
            run_script = self._generate_default_run_script()
        
        return {
            "requirements": requirements,
            "setup_instructions": setup_instructions,
            "run_script": run_script,
        }
    
    def _generate_default_requirements(self) -> str:
        """Generate default requirements.txt if parsing fails."""
        return """python-dotenv>=1.0.0
pyautogen>=0.2.0
openai>=1.0.0
streamlit>=1.28.0
pytest>=7.4.0"""
    
    def _generate_default_setup(self) -> str:
        """Generate default setup instructions if parsing fails."""
        return """1. Install Python 3.10 or higher
2. Create a virtual environment: python -m venv venv
3. Activate the virtual environment:
   - Windows: venv\\Scripts\\activate
   - Linux/Mac: source venv/bin/activate
4. Install dependencies: pip install -r requirements.txt
5. Create a .env file with your OPENAI_API_KEY
6. Run the application: streamlit run app.py"""
    
    def _generate_default_run_script(self) -> str:
        """Generate default run script if parsing fails."""
        return """#!/bin/bash
# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run Streamlit app
streamlit run app.py"""

