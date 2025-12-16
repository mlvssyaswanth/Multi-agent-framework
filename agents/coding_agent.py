"""
Coding Agent - Generates clean, modular Python code from requirements.
"""
from typing import Dict, Any
from autogen import ConversableAgent
from utils.config import Config
from utils.logger import get_logger, log_agent_activity, log_api_call

logger = get_logger(__name__)


class CodingAgent:
    """Agent responsible for generating Python code from structured requirements."""
    
    def __init__(self):
        """Initialize the Coding Agent."""
        self.agent = ConversableAgent(
            name="coder",
            system_message="""You are an expert Python software engineer specializing in clean, modular, production-ready code.

Your responsibilities:
1. Convert structured requirements into well-designed, WORKING Python code
2. Follow Python best practices (PEP 8, type hints, docstrings)
3. Write efficient, readable, and maintainable code
4. Include comprehensive error handling for incorrect inputs and failures
5. Ensure code is complete, executable, and handles edge cases gracefully

Code Quality Requirements:
- EFFICIENCY: Use appropriate algorithms and data structures, avoid unnecessary computations
- READABILITY: Clear variable names, logical structure, proper formatting
- MAINTAINABILITY: Modular design, separation of concerns, well-documented
- ERROR HANDLING: Gracefully handle incorrect inputs, missing data, edge cases
- ROBUSTNESS: Validate inputs, handle exceptions, provide meaningful error messages

Guidelines:
- Use meaningful variable and function names
- Add comprehensive docstrings to all functions and classes
- Include type hints where appropriate
- Write self-contained, testable modules
- Handle edge cases and invalid inputs gracefully
- Include input validation
- Provide clear error messages
- Do NOT include placeholder code or TODOs
- Do NOT review your own code - focus only on implementation
- Ensure code actually works and can be executed

Output only the Python code, properly formatted and ready for execution.""",
            llm_config={
                "config_list": [{
                    "model": Config.MODEL,
                    "api_key": Config.OPENAI_API_KEY,
                    "temperature": Config.TEMPERATURE,
                }],
                "timeout": 180,
            },
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
        )
    
    def generate_code(self, requirements: Dict[str, Any], feedback: str = None) -> str:
        """
        Generate Python code from structured requirements.
        
        Args:
            requirements: Structured requirements dictionary
            feedback: Optional feedback from code review agent
            
        Returns:
            Generated Python code as string
        """
        req_text = self._format_requirements(requirements)
        
        log_agent_activity(
            logger, 
            "CodingAgent", 
            "Generating code",
            {"has_feedback": bool(feedback), "requirements_count": len(requirements.get("functional_requirements", []))}
        )
        
        if feedback:
            prompt = f"""Based on the following requirements and review feedback, generate improved Python code:

REQUIREMENTS:
{req_text}

REVIEW FEEDBACK:
{feedback}

Generate complete, production-ready Python code that addresses the feedback."""
            logger.debug(f"📝 Generating code with feedback | Feedback length: {len(feedback)} chars")
        else:
            prompt = f"""Based on the following structured requirements, generate complete Python code:

REQUIREMENTS:
{req_text}

Generate complete, production-ready Python code following best practices."""
            logger.debug("📝 Generating initial code")
        
        log_api_call(logger, "CodingAgent", Config.MODEL, len(prompt))
        
        import time
        max_retries = 3
        code = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.agent.generate_reply(
                    messages=[{"role": "user", "content": prompt}]
                )
                
                if response is None:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                        continue
                    raise ValueError("Agent returned None response after retries. This may be due to API rate limiting or model unavailability.")
                
                code = response.get("content", "") if isinstance(response, dict) else str(response)
                
                if not code or not code.strip():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                        continue
                    raise ValueError("Agent returned empty code after retries.")
                
                break  # Success, exit retry loop
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                raise ValueError(f"API call failed after {max_retries} attempts: {str(e)}. Check API key, model configuration, and network connection.")
        
        if not code:
            error_msg = f"Failed to generate code after {max_retries} attempts"
            if last_error:
                error_msg += f": {str(last_error)}"
            raise ValueError(error_msg)
        
        # Extract code blocks from the response
        code = self._extract_code_blocks(code)
        
        return code
    
    def _format_requirements(self, requirements: Dict[str, Any]) -> str:
        """Format requirements dictionary into readable text."""
        text = "FUNCTIONAL REQUIREMENTS:\n"
        for req in requirements.get("functional_requirements", []):
            text += f"- {req}\n"
        
        text += "\nNON-FUNCTIONAL REQUIREMENTS:\n"
        for req in requirements.get("non_functional_requirements", []):
            text += f"- {req}\n"
        
        text += "\nASSUMPTIONS:\n"
        for assumption in requirements.get("assumptions", []):
            text += f"- {assumption}\n"
        
        text += "\nCONSTRAINTS:\n"
        for constraint in requirements.get("constraints", []):
            text += f"- {constraint}\n"
        
        return text
    
    def _extract_code_blocks(self, content: str) -> str:
        """Extract Python code from markdown code blocks."""
        if "```python" in content:
            start = content.find("```python") + 9
            end = content.find("```", start)
            return content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            return content[start:end].strip()
        return content.strip()

