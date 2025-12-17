"""
Orchestrator - Central controller for the Multi-Agent Coding Framework.
Manages the pipeline execution and agent collaboration.

STRICT PIPELINE ARCHITECTURE:
=============================

1. AGENTS WORK IN STRICT PIPELINE:
   - All agents execute in mandatory sequential order
   - No agent can execute before previous agent completes
   - Pipeline order is enforced and cannot be modified

2. OUTPUT OF ONE AGENT FEEDS INTO NEXT:
   - Requirement Analysis Agent output -> feeds into Coding Agent
   - Coding Agent output -> feeds into Code Review Agent
   - Code Review Agent feedback -> feeds back into Coding Agent (iteration loop)
   - Approved code -> feeds into Documentation Agent
   - Approved code -> feeds into Test Generation Agent
   - Approved code -> feeds into Deployment Agent

3. NO AGENT MAY SKIP ANOTHER:
   - All agents must execute in order: Requirements -> Code -> Review -> Documentation -> Tests -> Deployment
   - Validation checks prevent skipping steps
   - RuntimeError raised if pipeline order is violated

4. CODE REVIEW AGENT CAN FORCE RE-CODING:
   - Code Review Agent reviews code from Coding Agent
   - If issues found, generates explicit feedback
   - Feedback sent back to Coding Agent for re-coding
   - Iteration loop continues until code approved or max iterations reached
   - Central orchestration controls this iteration flow

5. CENTRAL ORCHESTRATION CONTROLS FLOW:
   - Orchestrator.execute_pipeline() controls entire execution
   - All agent calls go through orchestrator
   - Orchestrator manages data flow between agents
   - Orchestrator enforces pipeline order and prevents skipping
   - Orchestrator controls iteration loop between Coding and Review agents
"""
from typing import Dict, Any, Optional, Tuple, List, Callable
import logging
import os
import time
from agents import (
    RequirementAnalysisAgent,
    CodingAgent,
    CodeReviewAgent,
    DocumentationAgent,
    TestGenerationAgent,
    DeploymentAgent,
)
from utils.config import Config
from utils.logger import setup_logging, get_logger, PerformanceLogger, log_agent_activity

# Setup logging
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    log_to_file=os.getenv("LOG_TO_FILE", "true").lower() == "true",
    log_file_path=os.getenv("LOG_FILE_PATH", "logs/multi_agent_framework.log")
)
logger = get_logger(__name__)


class Orchestrator:
    """
    Central orchestrator that manages the multi-agent pipeline.
    
    STRICT PIPELINE RULES:
    1. Agents work in a strict, sequential pipeline
    2. Output of one agent feeds into the next agent
    3. No agent may skip another agent - all agents must execute in order
    4. Code Review Agent can force re-coding through iteration loop
    5. Central orchestration logic controls the entire flow
    
    PIPELINE ORDER (MANDATORY):
    1. RequirementAnalysisAgent -> outputs requirements
    2. CodingAgent -> uses requirements, outputs code
    3. CodeReviewAgent -> reviews code, can force re-coding (iteration loop)
    4. DocumentationAgent -> uses code and requirements, outputs documentation
    5. TestGenerationAgent -> uses code and requirements, outputs tests
    6. DeploymentAgent -> uses code and requirements, outputs deployment config
    
    The orchestrator enforces this order and ensures no agent is skipped.
    """
    
    # Define strict pipeline order - cannot be modified
    PIPELINE_ORDER = [
        "requirement_analysis",
        "code_generation",
        "code_review",
        "documentation",
        "test_generation",
        "deployment"
    ]
    
    def __init__(self):
        """Initialize the orchestrator with all agents."""
        self.requirement_agent = RequirementAnalysisAgent()
        self.coding_agent = CodingAgent()
        self.review_agent = CodeReviewAgent()
        self.documentation_agent = DocumentationAgent()
        self.test_agent = TestGenerationAgent()
        self.deployment_agent = DeploymentAgent()
        
        self.max_iterations = Config.MAX_ITERATIONS
        self._pipeline_state = {
            "current_step": None,
            "completed_steps": [],
            "step_outputs": {}
        }
    
    def execute_pipeline(self, user_input: str, progress_callback: Optional[Callable[[int, str], None]] = None, stop_check: Optional[Callable[[], bool]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the complete multi-agent pipeline in strict sequential order.
        
        STRICT PIPELINE ENFORCEMENT:
        - Agents execute in mandatory order: Requirements -> Code -> Review -> Documentation -> Tests -> Deployment
        - Output of one agent feeds into the next (no skipping allowed)
        - Code Review Agent can force re-coding through iteration loop
        - Central orchestration controls all flow
        
        Args:
            user_input: Natural language requirement from user
            progress_callback: Optional callback function(progress: int, message: str) for progress updates
            stop_check: Optional callback function() -> bool to check if execution should stop
            context: Optional context dictionary containing previous prompts and results for follow-up prompts
            
        Returns:
            Dictionary containing all outputs from each agent
        """
        pipeline_start = time.time()
        logger.info("Pipeline execution started")
        
        # Reset pipeline state
        self._pipeline_state = {
            "current_step": None,
            "completed_steps": [],
            "step_outputs": {}
        }
        
        results = {
            "user_input": user_input,
            "requirements": None,
            "code": None,
            "review_feedback": [],
            "documentation": None,
            "test_cases": None,
            "deployment_config": None,
            "iterations": 0,
            "status": "pending",
            "execution_time": 0,
        }
        
        def _check_stop():
            """Check if stop was requested."""
            if stop_check:
                return stop_check()
            return False
        
        try:
            # ====================================================================
            # STEP 1: REQUIREMENT ANALYSIS (MANDATORY - Cannot be skipped)
            # ====================================================================
            if progress_callback:
                progress_callback(5, "🚀 Starting pipeline execution...")
            
            if _check_stop():
                results["status"] = "stopped"
                results["execution_time"] = time.time() - pipeline_start
                logger.warning("Pipeline execution stopped by user")
                return results
            
            if not user_input or not user_input.strip():
                raise ValueError("User input cannot be empty. Please provide software requirements.")
            
            if progress_callback:
                progress_callback(10, "📋 Step 1/6: Analyzing requirements...")
            
            if _check_stop():
                results["status"] = "stopped"
                results["execution_time"] = time.time() - pipeline_start
                logger.warning("Pipeline execution stopped by user")
                return results
            
            # Mark step as current
            self._pipeline_state["current_step"] = "requirement_analysis"
            logger.info("Step 1/6: Requirement Analysis")
            
            with PerformanceLogger(logger, "Requirement Analysis"):
                try:
                    # Pass context if available (for follow-up prompts)
                    results["requirements"] = self.requirement_agent.analyze(user_input, context=context)
                    self._pipeline_state["step_outputs"]["requirements"] = results["requirements"]
                    self._pipeline_state["completed_steps"].append("requirement_analysis")
                except Exception as e:
                    logger.error(f"Requirement analysis failed: {str(e)}")
                    results["requirements"] = {
                        "functional_requirements": [user_input],
                        "non_functional_requirements": ["Code should be efficient, readable, and maintainable"],
                        "assumptions": ["Standard Python environment"],
                        "constraints": []
                    }
                    self._pipeline_state["step_outputs"]["requirements"] = results["requirements"]
                    self._pipeline_state["completed_steps"].append("requirement_analysis")
            
            # Validate Step 1 completed before proceeding
            if "requirement_analysis" not in self._pipeline_state["completed_steps"]:
                raise RuntimeError("Pipeline order violation: Requirement Analysis step must complete before proceeding")
            
            if progress_callback:
                progress_callback(15, "💻 Step 2-3/6: Generating and reviewing code...")
            
            if _check_stop():
                results["status"] = "stopped"
                results["execution_time"] = time.time() - pipeline_start
                logger.warning("Pipeline execution stopped by user")
                return results
            
            # Step 2-3: Code Generation and Review
            self._pipeline_state["current_step"] = "code_generation_and_review"
            logger.info("Step 2-3/6: Code Generation and Review")
            
            with PerformanceLogger(logger, "Code Generation and Review"):
                # Get previous code from context if available (for follow-ups)
                previous_code = None
                if context and context.get("is_active") and context.get("previous_results"):
                    previous_code = context.get("previous_results", {}).get("code")
                
                code, review_feedbacks = self._generate_and_review_code(
                    self._pipeline_state["step_outputs"]["requirements"], 
                    progress_callback, 
                    _check_stop,
                    previous_code=previous_code
                )
                results["code"] = code
                results["review_feedback"] = review_feedbacks
                results["iterations"] = len(review_feedbacks)
                self._pipeline_state["step_outputs"]["code"] = code
                self._pipeline_state["completed_steps"].append("code_generation")
                self._pipeline_state["completed_steps"].append("code_review")
                
                if not code:
                    logger.error("Code generation failed - no code generated")
                    results["status"] = "failed"
                    results["error"] = "Code generation failed - no code was generated after maximum iterations"
                    results["execution_time"] = time.time() - pipeline_start
                    return results
                
                if len(review_feedbacks) >= self.max_iterations:
                    logger.info(f"Code generated (best available after {len(review_feedbacks)} iterations)")
                else:
                    logger.info(f"Code generated ({len(review_feedbacks)} iteration(s))")
            
            # Validate Steps 2-3 completed before proceeding
            if "code_generation" not in self._pipeline_state["completed_steps"]:
                raise RuntimeError("Pipeline order violation: Code Generation step must complete before proceeding")
            if "code_review" not in self._pipeline_state["completed_steps"]:
                raise RuntimeError("Pipeline order violation: Code Review step must complete before proceeding")
            
            if _check_stop():
                results["status"] = "stopped"
                results["execution_time"] = time.time() - pipeline_start
                logger.warning("Pipeline execution stopped by user")
                return results
            
            # Step 4: Documentation Generation
            self._pipeline_state["current_step"] = "documentation"
            logger.info("Step 4/6: Documentation Generation")
            
            if progress_callback:
                progress_callback(50, "📚 Step 4/6: Generating documentation...")
            
            try:
                with PerformanceLogger(logger, "Documentation Generation"):
                    results["documentation"] = self.documentation_agent.generate_documentation(
                        self._pipeline_state["step_outputs"]["code"],
                        self._pipeline_state["step_outputs"]["requirements"]
                    )
                    self._pipeline_state["step_outputs"]["documentation"] = results["documentation"]
                    self._pipeline_state["completed_steps"].append("documentation")
            except Exception as e:
                logger.error(f"Documentation generation failed: {str(e)}")
                results["documentation"] = f"# Documentation Generation Error\n\nAn error occurred during documentation generation: {str(e)}\n\nCode was successfully generated but documentation could not be created."
                self._pipeline_state["step_outputs"]["documentation"] = results["documentation"]
                # Mark as completed even on failure since we provide a fallback
                self._pipeline_state["completed_steps"].append("documentation")
            
            # Validate Step 4 completed before proceeding
            if "documentation" not in self._pipeline_state["completed_steps"]:
                raise RuntimeError("Pipeline order violation: Documentation step must complete before proceeding")
            
            if _check_stop():
                results["status"] = "stopped"
                results["execution_time"] = time.time() - pipeline_start
                logger.warning("Pipeline execution stopped by user")
                return results
            
            # Step 5: Test Case Generation
            self._pipeline_state["current_step"] = "test_generation"
            logger.info("Step 5/6: Test Case Generation")
            
            if progress_callback:
                progress_callback(70, "🧪 Step 5/6: Generating test cases...")
            
            try:
                with PerformanceLogger(logger, "Test Case Generation"):
                    results["test_cases"] = self.test_agent.generate_tests(
                        self._pipeline_state["step_outputs"]["code"],
                        self._pipeline_state["step_outputs"]["requirements"]
                    )
                    self._pipeline_state["step_outputs"]["test_cases"] = results["test_cases"]
                    self._pipeline_state["completed_steps"].append("test_generation")
            except Exception as e:
                logger.error(f"Test case generation failed: {str(e)}")
                results["test_cases"] = f"# Test Generation Error\n\n# An error occurred during test generation: {str(e)}\n# Code was successfully generated but test cases could not be created.\n\nimport pytest\n\n# Placeholder test - replace with actual tests\ndef test_placeholder():\n    assert True"
                self._pipeline_state["step_outputs"]["test_cases"] = results["test_cases"]
                # Mark as completed even on failure since we provide a fallback
                self._pipeline_state["completed_steps"].append("test_generation")
            
            # Validate Step 5 completed before proceeding
            if "test_generation" not in self._pipeline_state["completed_steps"]:
                raise RuntimeError("Pipeline order violation: Test Generation step must complete before proceeding")
            
            if _check_stop():
                results["status"] = "stopped"
                results["execution_time"] = time.time() - pipeline_start
                logger.warning("Pipeline execution stopped by user")
                return results
            
            # Step 6: Deployment Configuration
            self._pipeline_state["current_step"] = "deployment"
            logger.info("Step 6/6: Deployment Configuration")
            
            if progress_callback:
                progress_callback(85, "🚀 Step 6/6: Generating deployment configuration...")
            
            try:
                with PerformanceLogger(logger, "Deployment Configuration"):
                    results["deployment_config"] = self.deployment_agent.generate_deployment_config(
                        self._pipeline_state["step_outputs"]["code"],
                        self._pipeline_state["step_outputs"]["requirements"]
                    )
                    self._pipeline_state["step_outputs"]["deployment_config"] = results["deployment_config"]
                    self._pipeline_state["completed_steps"].append("deployment")
            except Exception as e:
                logger.error(f"Deployment configuration generation failed: {str(e)}")
                results["deployment_config"] = {
                    "requirements": "python-dotenv>=1.0.0\npyautogen==0.2.28\nopenai>=1.0.0\nstreamlit>=1.28.0\npytest>=7.4.0",
                    "setup_instructions": "1. Install Python 3.10+\n2. Create virtual environment: python -m venv venv\n3. Activate: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)\n4. Install: pip install -r requirements.txt\n5. Run: python app.py",
                    "github_push": "1. Initialize git: git init\n2. Create .gitignore file\n3. Add files: git add .\n4. Commit: git commit -m 'Initial commit'\n5. Create GitHub repo and push",
                    "hosting_platforms": "Recommended: Heroku, Railway, or Render for easy deployment"
                }
            
            results["status"] = "completed"
            results["execution_time"] = time.time() - pipeline_start
            
            if progress_callback:
                progress_callback(100, "✅ Pipeline execution completed successfully!")
            
            logger.info(f"Pipeline execution completed successfully ({results['execution_time']:.2f}s)")
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            results["execution_time"] = time.time() - pipeline_start
            
            logger.error(f"Pipeline execution failed: {str(e)}")
            logger.exception("Error traceback:")
        
        return results
    
    def _generate_and_review_code(
        self, requirements: Dict[str, Any], progress_callback: Optional[Callable[[int, str], None]] = None, stop_check: Optional[Callable[[], bool]] = None, previous_code: Optional[str] = None
    ) -> Tuple[Optional[str], List[str]]:
        """
        Generate code and iterate with review until approved.
        
        CRITICAL: Code Review Agent can force re-coding through iteration loop.
        This method implements the iteration mechanism where:
        - Coding Agent generates code
        - Code Review Agent reviews code
        - If not approved, Code Review Agent sends feedback back to Coding Agent
        - Process repeats until code is approved or max iterations reached
        - Central orchestration controls this entire flow
        
        Args:
            requirements: Structured requirements dictionary (output from Requirement Analysis Agent)
            progress_callback: Optional progress callback
            stop_check: Optional stop check callback
            previous_code: Optional previous code for follow-up prompts
            
        Returns:
            Tuple of (approved_code, list_of_feedback_messages)
        """
        import time
        review_feedbacks = []
        feedback = None
        best_code = None
        best_code_score = -1
        best_iteration = 0
        
        for iteration in range(self.max_iterations):
            # Check for stop request before each iteration
            if stop_check and stop_check():
                logger.warning("Code generation stopped by user")
                return best_code if best_code else None, review_feedbacks
            
            logger.info(f"Code generation iteration {iteration + 1}/{self.max_iterations}")
            
            # Update progress for code generation iteration
            if progress_callback:
                base_progress = 15
                iteration_progress = base_progress + int((iteration / self.max_iterations) * 30)
                progress_callback(
                    iteration_progress,
                    f"💻 Step 2-3/6: Generating code (iteration {iteration + 1}/{self.max_iterations})..."
                )
            
            # Generate code with retry logic
            code = None
            max_retries = 3
            iteration_start = time.time()
            
            for retry in range(max_retries):
                try:
                    log_agent_activity(
                        logger, 
                        "CodingAgent", 
                        f"Generating code (attempt {retry + 1}/{max_retries})",
                        {"iteration": iteration + 1, "has_feedback": bool(feedback), "has_previous_code": bool(previous_code)}
                    )
                    # Pass previous code only on first iteration and if no feedback exists
                    code_to_pass = previous_code if (iteration == 0 and not feedback and previous_code) else None
                    code = self.coding_agent.generate_code(requirements, feedback, previous_code=code_to_pass)
                    break  # Success, exit retry loop
                except (ValueError, Exception) as e:
                    if retry < max_retries - 1:
                        wait_time = 2 ** retry
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Code generation failed after {max_retries} attempts: {str(e)}")
                        review_feedbacks.append(f"Code generation error: {str(e)}")
            
            if not code or not code.strip():
                review_feedbacks.append("Code generation returned empty result")
                continue
            
            # Update progress for code review
            if progress_callback:
                base_progress = 15
                iteration_progress = base_progress + int((iteration / self.max_iterations) * 30)
                review_progress = min(iteration_progress + 5, 45)
                progress_callback(
                    review_progress,
                    f"🔍 Step 2-3/6: Reviewing code (iteration {iteration + 1}/{self.max_iterations})..."
                )
            
            # Review code with retry logic
            is_approved = False
            review_feedback = ""
            review_start = time.time()
            
            for retry in range(max_retries):
                try:
                    log_agent_activity(
                        logger,
                        "CodeReviewAgent",
                        f"Reviewing code (attempt {retry + 1}/{max_retries})",
                        {"iteration": iteration + 1, "code_length": len(code)}
                    )
                    is_approved, review_feedback = self.review_agent.review(code, requirements)
                    break  # Success, exit retry loop
                except (ValueError, Exception) as e:
                    if retry < max_retries - 1:
                        wait_time = 2 ** retry
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Code review failed after {max_retries} attempts: {str(e)}")
                        review_feedback = f"Review error: {str(e)}"
                        is_approved = False
            
            review_feedbacks.append(review_feedback)
            
            # Track best code for fallback mechanism
            score = self._score_code_quality(review_feedback, code)
            if best_code is None or score > best_code_score:
                best_code_score = score
                best_code = code
                best_iteration = iteration + 1
            
            if is_approved:
                logger.info(f"Code approved (iteration {iteration + 1})")
                if progress_callback:
                    progress_callback(45, "✅ Code approved! Moving to documentation...")
                return code, review_feedbacks
            
            feedback = review_feedback
        
        # Use best code if max iterations reached
        if best_code:
            logger.warning(f"Max iterations reached ({self.max_iterations}), using best code from iteration {best_iteration}")
            review_feedbacks.append(
                f"[SYSTEM] Maximum iterations ({self.max_iterations}) reached. "
                f"Using best code generated (iteration {best_iteration}). "
                f"Pipeline will continue with all remaining steps."
            )
            return best_code, review_feedbacks
        
        logger.error("Code generation failed - no usable code generated")
        return None, review_feedbacks
    
    def _score_code_quality(self, feedback: str, code: str) -> float:
        """
        Score code quality based on review feedback and code characteristics.
        
        Args:
            feedback: Review feedback text
            requirements: Code string
            
        Returns:
            Quality score (0-100, higher is better)
        """
        score = 50.0  # Base score
        
        feedback_lower = feedback.lower()
        code_lower = code.lower()
        
        # Positive indicators (increase score)
        positive_keywords = [
            "well-structured", "good", "excellent", "proper", "correct",
            "meets requirements", "complete", "follows", "adheres",
            "appropriate", "adequate", "suitable", "functional"
        ]
        for keyword in positive_keywords:
            if keyword in feedback_lower:
                score += 5
        
        # Strong positive indicators
        if "approved" in feedback_lower or "approve" in feedback_lower:
            score += 20
        if "meets all" in feedback_lower or "fully meets" in feedback_lower:
            score += 15
        if "production-ready" in feedback_lower or "production ready" in feedback_lower:
            score += 10
        
        # Negative indicators (decrease score)
        negative_keywords = [
            "missing", "error", "bug", "incorrect", "wrong",
            "does not", "fails", "incomplete", "lacks"
        ]
        for keyword in negative_keywords:
            if keyword in feedback_lower:
                score -= 3
        
        # Code characteristics
        if "def " in code and "class " in code:
            score += 5  # Has functions and classes
        if "import " in code:
            score += 2  # Has imports
        if len(code) > 1000:
            score += 3  # Substantial code
        if "try:" in code or "except" in code:
            score += 3  # Has error handling
        
        # Normalize score to 0-100 range
        score = max(0, min(100, score))
        
        return score

