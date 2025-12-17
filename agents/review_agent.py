"""
Code Review Agent - Reviews code and enforces quality standards.
"""
from typing import Dict, Tuple
from autogen import ConversableAgent
from utils.config import Config
from utils.logger import get_logger, log_agent_activity, log_api_call

logger = get_logger(__name__)


class CodeReviewAgent:
    """Agent responsible for reviewing code and providing feedback."""
    
    def __init__(self):
        """Initialize the Code Review Agent."""
        self.agent = ConversableAgent(
            name="code_reviewer",
            system_message="""You are a Senior Code Reviewer with expertise in Python, software engineering best practices, security, and code quality.

PRIMARY MISSION:
Review code for correctness, efficiency, security, and edge cases. If issues are found, generate explicit improvement feedback to send back to the Coding Agent.

CORE RESPONSIBILITIES:
1. **Review Code Thoroughly**: Examine code for correctness, efficiency, security, and edge cases
2. **Generate Explicit Feedback**: If issues are found, provide clear, actionable improvement feedback
3. **Send Code Back**: When issues are found, code must be sent back to Coding Agent for fixes

MANDATORY REVIEW AREAS:

1. **CORRECTNESS**:
   - Does the code correctly implement all requirements?
   - Are there logical errors or bugs?
   - Does the code produce expected outputs?
   - Are algorithms and data structures used correctly?
   - Are calculations and operations accurate?

2. **EFFICIENCY**:
   - Are there performance bottlenecks?
   - Are algorithms optimal for the use case?
   - Are there unnecessary computations or loops?
   - Is memory usage reasonable?
   - Are data structures chosen appropriately?
   - Are there opportunities for optimization?

3. **SECURITY**:
   - Are there security vulnerabilities (SQL injection, XSS, etc.)?
   - Is input validation and sanitization proper?
   - Are sensitive data handled securely?
   - Are authentication/authorization checks in place if needed?
   - Are file operations secure?
   - Are there potential code injection risks?
   - Is error handling secure (no information leakage)?

4. **EDGE CASES**:
   - Are null/None values handled?
   - Are empty inputs handled?
   - Are boundary conditions tested?
   - Are error conditions handled gracefully?
   - Are edge cases in algorithms covered?
   - Are division by zero, index out of bounds, etc. handled?

ADDITIONAL REVIEW CRITERIA:
- Code Quality: Is the code clean, readable, and maintainable?
- Completeness: Is the code complete with no placeholders, TODOs, or incomplete logic?
- Best Practices: Does it follow Python best practices (PEP 8, type hints, docstrings)?

APPROVAL GUIDELINES:
- **APPROVE** code ONLY if it passes all four mandatory review areas (Correctness, Efficiency, Security, Edge Cases)
- **APPROVE** if code is correct, efficient, secure, and handles edge cases properly
- **DO NOT APPROVE** if any significant issues are found in the four mandatory areas
- Be thorough but practical: code should be production-ready

OUTPUT FORMAT:
- If code is APPROVED: Respond with "APPROVED" at the start of your response
- If issues are found: Provide explicit, detailed feedback organized by:
  1. CORRECTNESS ISSUES: [list specific issues]
  2. EFFICIENCY ISSUES: [list specific issues]
  3. SECURITY ISSUES: [list specific issues]
  4. EDGE CASE ISSUES: [list specific issues]
  
  For each issue, provide:
  - What the problem is
  - Where it occurs (line/function/class)
  - How to fix it
  - Why it matters

The feedback must be explicit and actionable so the Coding Agent can fix the issues.""",
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
    
    def review(self, code: str, requirements: Dict) -> Tuple[bool, str]:
        """
        Review code and determine if it passes or needs revision.
        
        Args:
            code: Python code to review
            requirements: Original requirements dictionary
            
        Returns:
            Tuple of (is_approved: bool, feedback: str)
        """
        req_text = self._format_requirements(requirements)
        
        log_agent_activity(
            logger,
            "CodeReviewAgent",
            "Reviewing code",
            {"code_length": len(code), "requirements_count": len(requirements.get("functional_requirements", []))}
        )
        
        prompt = f"""Review the following Python code for correctness, efficiency, security, and edge cases.

REQUIREMENTS:
{req_text}

CODE TO REVIEW:
```python
{code}
```

MANDATORY REVIEW CHECKLIST:

1. **CORRECTNESS**:
   - Does the code correctly implement all requirements?
   - Are there logical errors or bugs?
   - Does the code produce expected outputs?
   - Are algorithms and data structures used correctly?

2. **EFFICIENCY**:
   - Are there performance bottlenecks?
   - Are algorithms optimal?
   - Are there unnecessary computations?
   - Is memory usage reasonable?

3. **SECURITY**:
   - Are there security vulnerabilities?
   - Is input validation proper?
   - Are sensitive operations secure?
   - Is error handling secure?

4. **EDGE CASES**:
   - Are null/None values handled?
   - Are empty inputs handled?
   - Are boundary conditions tested?
   - Are error conditions handled gracefully?

REVIEW PROCESS:
1. Check each of the four mandatory areas (Correctness, Efficiency, Security, Edge Cases)
2. If ALL areas pass: Respond with "APPROVED"
3. If ANY issues are found: Generate explicit improvement feedback organized by category

FEEDBACK FORMAT (if issues found):
Provide explicit, actionable feedback in this format:

CORRECTNESS ISSUES:
- [Issue 1]: [Description] - [Location] - [How to fix] - [Why it matters]
- [Issue 2]: [Description] - [Location] - [How to fix] - [Why it matters]

EFFICIENCY ISSUES:
- [Issue 1]: [Description] - [Location] - [How to fix] - [Why it matters]

SECURITY ISSUES:
- [Issue 1]: [Description] - [Location] - [How to fix] - [Why it matters]

EDGE CASE ISSUES:
- [Issue 1]: [Description] - [Location] - [How to fix] - [Why it matters]

The feedback must be explicit and actionable so the Coding Agent can address each issue."""
        
        log_api_call(logger, "CodeReviewAgent", Config.MODEL, len(prompt))
        
        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.agent.generate_reply(
                    messages=[{"role": "user", "content": prompt}]
                )
                
                if response is None:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise ValueError("Agent returned None response after retries.")
                
                feedback = response.get("content", "") if isinstance(response, dict) else str(response)
                break  # Success
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise ValueError(f"Review API call failed after {max_retries} attempts: {str(e)}")
        feedback = feedback.strip()
        
        is_approved = feedback.upper().startswith("APPROVED")
        
        return is_approved, feedback
    
    def _format_requirements(self, requirements: Dict) -> str:
        """Format requirements for review context."""
        text = "FUNCTIONAL REQUIREMENTS:\n"
        for req in requirements.get("functional_requirements", []):
            text += f"- {req}\n"
        
        text += "\nNON-FUNCTIONAL REQUIREMENTS:\n"
        for req in requirements.get("non_functional_requirements", []):
            text += f"- {req}\n"
        
        return text

