"""
Requirement Analysis Agent - Converts natural language to structured requirements.
"""
import json
from typing import Dict, Any
from autogen import ConversableAgent
from utils.config import Config
from utils.logger import get_logger, log_agent_activity, log_api_call

logger = get_logger(__name__)


class RequirementAnalysisAgent:
    """Agent responsible for analyzing and structuring user requirements."""
    
    def __init__(self):
        """Initialize the Requirement Analysis Agent."""
        self.agent = ConversableAgent(
            name="requirement_analyst",
            system_message="""You are a Senior Requirements Analyst specializing in software engineering.
Your task is to analyze natural language requirements and convert them into structured, actionable software requirements.

When given user input, you must output a JSON object with the following structure:
{
    "functional_requirements": ["list of functional requirements"],
    "non_functional_requirements": ["list of non-functional requirements"],
    "assumptions": ["list of assumptions made"],
    "constraints": ["list of constraints identified"]
}

Be thorough, specific, and ensure all requirements are testable and implementable.
Focus on clarity and completeness.""",
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
    
    def analyze(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze user input and return structured requirements.
        
        Args:
            user_input: Natural language description of requirements
            
        Returns:
            Dictionary containing structured requirements
        """
        log_agent_activity(logger, "RequirementAnalysisAgent", "Starting analysis", {"input_length": len(user_input)})
        
        prompt = f"""Analyze the following user requirement and provide structured output:

User Requirement:
{user_input}

Provide your analysis as a JSON object with keys: functional_requirements, non_functional_requirements, assumptions, constraints."""
        
        log_api_call(logger, "RequirementAnalysisAgent", Config.MODEL, len(prompt))
        
        response = self.agent.generate_reply(
            messages=[{"role": "user", "content": prompt}]
        )
        
        if response is None:
            logger.error("❌ Agent returned None response")
            raise ValueError("Agent returned None response. Check API key and model configuration.")
        
        content = response.get("content", "") if isinstance(response, dict) else str(response)
        log_api_call(logger, "RequirementAnalysisAgent", Config.MODEL, len(prompt), len(content))
        logger.debug(f"✅ Response received | Length: {len(content)} characters")
        
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                requirements = json.loads(json_str)
            else:
                requirements = self._parse_fallback(content)
        except json.JSONDecodeError:
            requirements = self._parse_fallback(content)
        
        return {
            "functional_requirements": requirements.get("functional_requirements", []),
            "non_functional_requirements": requirements.get("non_functional_requirements", []),
            "assumptions": requirements.get("assumptions", []),
            "constraints": requirements.get("constraints", []),
        }
    
    def _parse_fallback(self, content: str) -> Dict[str, Any]:
        """Fallback parser if JSON extraction fails."""
        return {
            "functional_requirements": [content],
            "non_functional_requirements": [],
            "assumptions": [],
            "constraints": [],
        }

