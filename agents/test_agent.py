"""
Test Case Generation Agent - Generates executable pytest test cases.
"""
from typing import Dict
from autogen import ConversableAgent
from utils.config import Config
from utils.logger import get_logger, log_agent_activity, log_api_call

logger = get_logger(__name__)


class TestGenerationAgent:
    """Agent responsible for generating executable pytest test cases."""
    
    def __init__(self):
        """Initialize the Test Generation Agent."""
        self.agent = ConversableAgent(
            name="test_generator",
            system_message="""You are a Senior Test Engineer specializing in Python testing with pytest.

Your responsibilities:
1. Generate comprehensive, executable pytest test cases
2. Create at least one functional test per module/function
3. Ensure tests are complete and runnable without modification
4. Cover normal cases, edge cases, and error scenarios
5. Use pytest best practices (fixtures, parametrization where appropriate)
6. Include test execution results in comments showing expected outputs

Test Requirements:
- All tests must be executable immediately
- Use proper pytest syntax and assertions
- Include descriptive test names
- Test both success and failure scenarios
- No placeholders or incomplete tests
- Import statements must be correct
- For each test, include a comment showing expected execution result
- Test actual code execution, not just imports

Output Format:
- Python test code with pytest
- Include execution results as comments after each test
- Show both passing and expected failure scenarios
- Format: # Expected Result: [description of what should happen]

Example:
```python
def test_addition():
    result = add(2, 3)
    assert result == 5
    # Expected Result: Test passes, returns 5
```

Output only the Python test code, properly formatted and ready for execution.""",
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
    
    def generate_tests(self, code: str, requirements: Dict) -> str:
        """
        Generate pytest test cases for the given code.
        
        Args:
            code: Python code to test
            requirements: Original requirements dictionary
            
        Returns:
            Generated pytest test code as string
        """
        req_text = self._format_requirements(requirements)
        
        log_agent_activity(logger, "TestGenerationAgent", "Generating test cases", {"code_length": len(code)})
        
        prompt = f"""Generate comprehensive pytest test cases for the following Python code.

ORIGINAL REQUIREMENTS:
{req_text}

CODE TO TEST:
```python
{code}
```

Generate complete, executable pytest test cases that:
1. Test all major functions and classes
2. Cover normal cases, edge cases, and error scenarios
3. Are immediately runnable without modification
4. Use proper pytest syntax and assertions
5. Include descriptive test names
6. Include execution results as comments showing what each test should produce

For each test function, add a comment showing the expected execution result, for example:
# Expected Result: Test passes, function returns correct value
# Expected Result: Test passes, exception is raised correctly

IMPORTANT: 
- Test the actual execution of the code, not just imports
- Show what happens when tests run (pass/fail and why)
- Include both positive and negative test cases
- Make tests comprehensive and realistic

Output only the Python test code with execution result comments."""
        
        log_api_call(logger, "TestGenerationAgent", Config.MODEL, len(prompt))
        
        response = self.agent.generate_reply(
            messages=[{"role": "user", "content": prompt}]
        )
        
        if response is None:
            raise ValueError("Agent returned None response. Check API key and model configuration.")
        
        test_code = response.get("content", "") if isinstance(response, dict) else str(response)
        test_code = self._extract_code_blocks(test_code)
        
        return test_code
    
    def _format_requirements(self, requirements: Dict) -> str:
        """Format requirements for test generation context."""
        text = "FUNCTIONAL REQUIREMENTS:\n"
        for req in requirements.get("functional_requirements", []):
            text += f"- {req}\n"
        
        text += "\nNON-FUNCTIONAL REQUIREMENTS:\n"
        for req in requirements.get("non_functional_requirements", []):
            text += f"- {req}\n"
        
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

