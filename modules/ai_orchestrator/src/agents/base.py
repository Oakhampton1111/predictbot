"""
PredictBot AI Orchestrator - Base Agent Class
==============================================

This module provides the abstract base class for all specialized agents.
Each agent inherits from BaseAgent and implements the process() method.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime
import asyncio
import json
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

try:
    from shared.logging_config import get_logger, log_critical_junction, CriticalJunctions
    from shared.metrics import get_metrics_registry
except ImportError:
    # Fallback if shared module not available
    import logging
    def get_logger(name: str, **kwargs):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def log_critical_junction(logger, junction_name, message, **kwargs):
        logger.info(f"[{junction_name}] {message}")
    
    class CriticalJunctions:
        AI_DECISION = "ai_decision"
    
    def get_metrics_registry():
        return None


class AgentError(Exception):
    """Base exception for agent errors."""
    pass


class AgentTimeoutError(AgentError):
    """Raised when an agent operation times out."""
    pass


class AgentLLMError(AgentError):
    """Raised when LLM call fails."""
    pass


class BaseAgent(ABC):
    """
    Abstract base class for all trading agents.
    
    Each agent is responsible for a specific step in the trading pipeline:
    - MarketAnalyst: Analyzes market structure and quality
    - NewsSentiment: Processes news and social sentiment
    - Forecaster: Generates probability forecasts
    - Critic: Validates and challenges forecasts
    - RiskAssessor: Evaluates trade risk
    - TradeExecutor: Determines execution parameters
    
    Attributes:
        name: Agent name for logging and identification
        llm_router: Router for selecting appropriate LLM provider
        logger: Structured logger instance
        metrics: Prometheus metrics registry
        timeout: Maximum time for agent processing (seconds)
    """
    
    def __init__(
        self,
        name: str,
        llm_router: Any,
        timeout: float = 60.0,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Agent name (e.g., "market_analyst")
            llm_router: LLM provider router instance
            timeout: Maximum processing time in seconds
            config: Optional agent-specific configuration
        """
        self.name = name
        self.llm_router = llm_router
        self.timeout = timeout
        self.config = config or {}
        
        # Initialize logging and metrics
        self.logger = get_logger(f"agent.{name}")
        self.metrics = get_metrics_registry()
        
        # Track agent state
        self._is_processing = False
        self._last_run: Optional[datetime] = None
        self._run_count = 0
        self._error_count = 0
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the trading state and return updated state.
        
        This is the main method that each agent must implement.
        It receives the current trading state and returns the
        updated state with the agent's analysis/decisions.
        
        Args:
            state: Current TradingState dictionary
            
        Returns:
            Updated TradingState dictionary
            
        Raises:
            AgentError: If processing fails
        """
        pass
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent with timeout and error handling.
        
        This wrapper method handles:
        - Timeout enforcement
        - Error logging and metrics
        - State validation
        
        Args:
            state: Current TradingState dictionary
            
        Returns:
            Updated TradingState dictionary
        """
        self._is_processing = True
        start_time = datetime.utcnow()
        
        self.logger.info(
            f"Agent {self.name} starting processing",
            extra={
                "cycle_id": state.get("cycle_id"),
                "current_step": state.get("current_step")
            }
        )
        
        try:
            # Run with timeout
            result = await asyncio.wait_for(
                self.process(state),
                timeout=self.timeout
            )
            
            # Update metrics
            self._run_count += 1
            self._last_run = datetime.utcnow()
            
            elapsed = (self._last_run - start_time).total_seconds()
            self.logger.info(
                f"Agent {self.name} completed successfully",
                extra={
                    "cycle_id": state.get("cycle_id"),
                    "elapsed_seconds": elapsed
                }
            )
            
            if self.metrics:
                self.metrics.record_request(
                    endpoint=f"agent_{self.name}",
                    method="process",
                    status=200,
                    latency_seconds=elapsed
                )
            
            return result
            
        except asyncio.TimeoutError:
            self._error_count += 1
            error_msg = f"Agent {self.name} timed out after {self.timeout}s"
            self.logger.error(error_msg, extra={"cycle_id": state.get("cycle_id")})
            
            if self.metrics:
                self.metrics.record_error("timeout", service=f"agent_{self.name}")
            
            # Add error to state
            state["errors"] = state.get("errors", []) + [error_msg]
            return state
            
        except Exception as e:
            self._error_count += 1
            error_msg = f"Agent {self.name} failed: {str(e)}"
            self.logger.exception(error_msg, extra={"cycle_id": state.get("cycle_id")})
            
            if self.metrics:
                self.metrics.record_error(type(e).__name__, service=f"agent_{self.name}")
            
            # Add error to state
            state["errors"] = state.get("errors", []) + [error_msg]
            return state
            
        finally:
            self._is_processing = False
    
    def get_llm(self, task_type: str) -> Any:
        """
        Get the appropriate LLM for a specific task type.
        
        Args:
            task_type: Type of task (e.g., "analysis", "reasoning", "fast")
            
        Returns:
            LLM instance from the router
        """
        return self.llm_router.get_llm_for_task(task_type)
    
    async def call_llm(
        self,
        prompt: str,
        task_type: str = "default",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Call the LLM with the given prompt.
        
        Args:
            prompt: User prompt to send
            task_type: Task type for LLM routing
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            LLM response text
            
        Raises:
            AgentLLMError: If LLM call fails
        """
        try:
            llm = self.get_llm(task_type)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await llm.ainvoke(
                messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Track LLM usage
            if self.metrics and hasattr(response, 'usage'):
                self.metrics.record_llm_call(
                    model=llm.model_name if hasattr(llm, 'model_name') else "unknown",
                    endpoint="chat",
                    tokens_input=response.usage.get('prompt_tokens', 0),
                    tokens_output=response.usage.get('completion_tokens', 0)
                )
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            raise AgentLLMError(f"LLM call failed: {str(e)}") from e
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling common formatting issues.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Parsed JSON dictionary
        """
        # Try to extract JSON from markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            raise
    
    def log_decision(
        self,
        decision_type: str,
        details: Dict[str, Any],
        confidence: Optional[float] = None
    ) -> None:
        """
        Log an agent decision as a critical junction.
        
        Args:
            decision_type: Type of decision made
            details: Decision details
            confidence: Optional confidence score
        """
        log_critical_junction(
            self.logger,
            junction_name=CriticalJunctions.AI_DECISION,
            message=f"{self.name} made {decision_type} decision",
            extra={
                "agent": self.name,
                "decision_type": decision_type,
                "confidence": confidence,
                **details
            }
        )
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "name": self.name,
            "is_processing": self._is_processing,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "run_count": self._run_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._run_count, 1)
        }
