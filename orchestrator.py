"""
Orchestrator - Central controller for the Multi-Agent Coding Framework.
Manages the pipeline execution and agent collaboration.
"""
from typing import Dict, Any, Optional, Tuple, List
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
    Controls execution flow and enforces iteration until code passes review.
    """
    
    def __init__(self):
        """Initialize the orchestrator with all agents."""
        self.requirement_agent = RequirementAnalysisAgent()
        self.coding_agent = CodingAgent()
        self.review_agent = CodeReviewAgent()
        self.documentation_agent = DocumentationAgent()
        self.test_agent = TestGenerationAgent()
        self.deployment_agent = DeploymentAgent()
        
        self.max_iterations = Config.MAX_ITERATIONS
    
    def execute_pipeline(self, user_input: str) -> Dict[str, Any]:
        """
        Execute the complete multi-agent pipeline.
        
        Args:
            user_input: Natural language requirement from user
            
        Returns:
            Dictionary containing all outputs from each agent
        """
        pipeline_start = time.time()
        logger.info("=" * 80)
        logger.info("🚀 Starting Multi-Agent Pipeline Execution")
        logger.info("=" * 80)
        logger.info(f"📝 User Input Length: {len(user_input)} characters")
        logger.debug(f"📝 User Input: {user_input[:200]}..." if len(user_input) > 200 else f"📝 User Input: {user_input}")
        
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
        
        try:
            # Step 1: Requirement Analysis (with input validation)
            if not user_input or not user_input.strip():
                raise ValueError("User input cannot be empty. Please provide software requirements.")
            
            if len(user_input.strip()) < 10:
                logger.warning("⚠️  User input is very short. Results may be limited.")
            
            with PerformanceLogger(logger, "Requirement Analysis"):
                log_agent_activity(logger, "RequirementAnalysisAgent", "Analyzing user requirements")
                try:
                    results["requirements"] = self.requirement_agent.analyze(user_input)
                except Exception as e:
                    logger.error(f"❌ Requirement analysis failed: {str(e)}")
                    # Provide fallback requirements
                    results["requirements"] = {
                        "functional_requirements": [user_input],
                        "non_functional_requirements": ["Code should be efficient, readable, and maintainable"],
                        "assumptions": ["Standard Python environment"],
                        "constraints": []
                    }
                    logger.warning("⚠️  Using fallback requirements structure")
                
                func_reqs = results["requirements"].get("functional_requirements", [])
                non_func_reqs = results["requirements"].get("non_functional_requirements", [])
                assumptions = results["requirements"].get("assumptions", [])
                constraints = results["requirements"].get("constraints", [])
                
                logger.info(
                    f"✅ Requirements Extracted | "
                    f"Functional: {len(func_reqs)} | "
                    f"Non-functional: {len(non_func_reqs)} | "
                    f"Assumptions: {len(assumptions)} | "
                    f"Constraints: {len(constraints)}"
                )
            
            # Step 2-3: Code Generation and Review (with iteration)
            with PerformanceLogger(logger, "Code Generation and Review"):
                code, review_feedbacks = self._generate_and_review_code(results["requirements"])
                results["code"] = code
                results["review_feedback"] = review_feedbacks
                results["iterations"] = len(review_feedbacks)
                
                if code:
                    if len(review_feedbacks) >= self.max_iterations:
                        logger.info(f"✅ Code Generated (Best Available) | Iterations: {len(review_feedbacks)} | Code Length: {len(code)} characters")
                        logger.info("ℹ️  Proceeding with best available code after maximum iterations")
                    else:
                        logger.info(f"✅ Code Generated | Iterations: {len(review_feedbacks)} | Code Length: {len(code)} characters")
                else:
                    logger.error("❌ Code generation failed - no code was generated")
                    results["status"] = "failed"
                    results["error"] = "Code generation failed - no code was generated after maximum iterations"
                    results["execution_time"] = time.time() - pipeline_start
                    return results
            
            # Step 4: Documentation Generation (with error handling)
            try:
                with PerformanceLogger(logger, "Documentation Generation"):
                    log_agent_activity(logger, "DocumentationAgent", "Generating documentation")
                    results["documentation"] = self.documentation_agent.generate_documentation(
                        code, results["requirements"]
                    )
                    logger.info(f"✅ Documentation Generated | Length: {len(results['documentation'])} characters")
            except Exception as e:
                logger.error(f"❌ Documentation generation failed: {str(e)}")
                logger.warning("⚠️  Continuing pipeline with placeholder documentation")
                results["documentation"] = f"# Documentation Generation Error\n\nAn error occurred during documentation generation: {str(e)}\n\nCode was successfully generated but documentation could not be created."
            
            # Step 5: Test Case Generation (with error handling)
            try:
                with PerformanceLogger(logger, "Test Case Generation"):
                    log_agent_activity(logger, "TestGenerationAgent", "Generating test cases")
                    results["test_cases"] = self.test_agent.generate_tests(
                        code, results["requirements"]
                    )
                    logger.info(f"✅ Test Cases Generated | Length: {len(results['test_cases'])} characters")
            except Exception as e:
                logger.error(f"❌ Test case generation failed: {str(e)}")
                logger.warning("⚠️  Continuing pipeline with placeholder test cases")
                results["test_cases"] = f"# Test Generation Error\n\n# An error occurred during test generation: {str(e)}\n# Code was successfully generated but test cases could not be created.\n\nimport pytest\n\n# Placeholder test - replace with actual tests\ndef test_placeholder():\n    assert True"
            
            # Step 6: Deployment Configuration (with error handling)
            try:
                with PerformanceLogger(logger, "Deployment Configuration"):
                    log_agent_activity(logger, "DeploymentAgent", "Generating deployment config")
                    results["deployment_config"] = self.deployment_agent.generate_deployment_config(
                        code, results["requirements"]
                    )
                    logger.info("✅ Deployment Configuration Generated")
            except Exception as e:
                logger.error(f"❌ Deployment configuration generation failed: {str(e)}")
                logger.warning("⚠️  Continuing pipeline with default deployment config")
                results["deployment_config"] = {
                    "requirements": "python-dotenv>=1.0.0\npyautogen==0.2.28\nopenai>=1.0.0\nstreamlit>=1.28.0\npytest>=7.4.0",
                    "setup_instructions": "1. Install Python 3.10+\n2. Create virtual environment: python -m venv venv\n3. Activate: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)\n4. Install: pip install -r requirements.txt\n5. Run: python app.py",
                    "run_script": "#!/bin/bash\nsource venv/bin/activate\npython app.py"
                }
            
            results["status"] = "completed"
            results["execution_time"] = time.time() - pipeline_start
            
            logger.info("=" * 80)
            logger.info(f"✅ Pipeline Execution Completed Successfully | Total Time: {results['execution_time']:.2f}s")
            logger.info("=" * 80)
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            results["execution_time"] = time.time() - pipeline_start
            
            logger.error("=" * 80)
            logger.error(f"❌ Pipeline Execution Failed | Error: {str(e)} | Time: {results['execution_time']:.2f}s")
            logger.exception("Full error traceback:")
            logger.error("=" * 80)
        
        return results
    
    def _generate_and_review_code(
        self, requirements: Dict[str, Any]
    ) -> Tuple[Optional[str], List[str]]:
        """
        Generate code and iterate with review until approved.
        
        Args:
            requirements: Structured requirements dictionary
            
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
            logger.info("-" * 80)
            logger.info(f"🔄 Code Generation Iteration {iteration + 1}/{self.max_iterations}")
            logger.info("-" * 80)
            
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
                        {"iteration": iteration + 1, "has_feedback": bool(feedback)}
                    )
                    code = self.coding_agent.generate_code(requirements, feedback)
                    gen_time = time.time() - iteration_start
                    logger.info(f"✅ Code Generated | Attempt: {retry + 1} | Time: {gen_time:.2f}s | Length: {len(code)} chars")
                    break  # Success, exit retry loop
                except (ValueError, Exception) as e:
                    if retry < max_retries - 1:
                        wait_time = 2 ** retry  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(
                            f"⚠️  Code generation failed (attempt {retry + 1}/{max_retries}) | "
                            f"Error: {str(e)[:100]} | Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ Code generation failed after {max_retries} attempts | Error: {str(e)}")
                        review_feedbacks.append(f"Code generation error: {str(e)}")
            
            if not code or not code.strip():
                logger.warning("⚠️  Empty code generated, skipping to next iteration")
                review_feedbacks.append("Code generation returned empty result")
                # Still try to use this as fallback if we have nothing better
                if best_code is None:
                    logger.debug("⚠️  No code available yet, will use first non-empty code as fallback")
                continue
            
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
                    review_time = time.time() - review_start
                    status = "✅ APPROVED" if is_approved else "⚠️  NEEDS REVISION"
                    logger.info(f"{status} | Attempt: {retry + 1} | Time: {review_time:.2f}s")
                    break  # Success, exit retry loop
                except (ValueError, Exception) as e:
                    if retry < max_retries - 1:
                        wait_time = 2 ** retry
                        logger.warning(
                            f"⚠️  Code review failed (attempt {retry + 1}/{max_retries}) | "
                            f"Error: {str(e)[:100]} | Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ Code review failed after {max_retries} attempts | Error: {str(e)}")
                        review_feedback = f"Review error: {str(e)}"
                        is_approved = False  # Assume not approved if review fails
            
            review_feedbacks.append(review_feedback)
            
            # CRITICAL: Always track code for fallback mechanism
            # Score the code quality based on feedback
            # Positive indicators in feedback suggest better code
            # Always track code even if not approved - we'll use best one as fallback
            score = self._score_code_quality(review_feedback, code)
            
            # Always update best_code if this is the first code or if score is better
            if best_code is None or score > best_code_score:
                best_code_score = score
                best_code = code
                best_iteration = iteration + 1
                logger.info(f"📊 Best code tracked | Score: {score:.2f} | Iteration: {iteration + 1} | Length: {len(code)} chars")
            else:
                logger.debug(f"📊 Code scored | Score: {score:.2f} | Current best: {best_code_score:.2f} (iteration {best_iteration})")
            
            if is_approved:
                total_iteration_time = time.time() - iteration_start
                logger.info(f"✅ Code Approved | Total Iteration Time: {total_iteration_time:.2f}s")
                return code, review_feedbacks
            
            feedback_preview = review_feedback[:150] + "..." if len(review_feedback) > 150 else review_feedback
            logger.info(f"📋 Review Feedback (iteration {iteration + 1}): {feedback_preview}")
            feedback = review_feedback
        
        # If we reach here, use the best code we generated (FALLBACK MECHANISM)
        # This ensures pipeline ALWAYS completes, even if code wasn't perfectly approved
        if best_code:
            logger.warning("=" * 80)
            logger.warning(f"⚠️  Max Iterations Reached ({self.max_iterations}) | Using Best Code from Iteration {best_iteration}")
            logger.warning(f"📊 Best Code Score: {best_code_score:.2f} | Code Length: {len(best_code)} chars | Total Feedbacks: {len(review_feedbacks)}")
            logger.warning("✅ Pipeline will continue with best available code - ALL STEPS WILL COMPLETE")
            logger.warning("=" * 80)
            # Add a note to feedbacks that we're using best available code
            review_feedbacks.append(
                f"[SYSTEM] Maximum iterations ({self.max_iterations}) reached. "
                f"Using best code generated (iteration {best_iteration}, score: {best_code_score:.2f}). "
                f"Code may not be perfect but represents the best effort after {self.max_iterations} iterations. "
                f"Pipeline will continue with all remaining steps."
            )
            return best_code, review_feedbacks
        else:
            # Emergency fallback: if somehow no code was tracked, use the last generated code
            logger.error("=" * 80)
            logger.error("❌ CRITICAL: No best code tracked - this should not happen!")
            logger.error("Attempting to recover using last iteration code...")
            logger.error("=" * 80)
            # This should never happen, but provides ultimate safety
            if review_feedbacks:
                review_feedbacks.append(
                    "[SYSTEM ERROR] No code was successfully tracked. Pipeline may be incomplete."
                )
            return None, review_feedbacks
        
        # This should never be reached now, but kept as safety fallback
        logger.error("=" * 80)
        logger.error(f"❌ Code Generation Failed Completely | No usable code generated")
        logger.error(f"📊 Total Review Feedbacks: {len(review_feedbacks)}")
        logger.error("=" * 80)
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

