"""
Cost management system for Apify actors.

Implements cost tracking, estimation, and budget controls for Apify actors.
"""

import json
import os
import time
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import structlog

from app.actors.config import ActorConfig, CostModel, get_actor_configurations
from app.models.data import CostBreakdown


logger = structlog.get_logger(__name__)


class OptimizationStrategy(str, Enum):
    """Optimization strategy for cost management."""
    
    SPEED = "speed"  # Optimize for speed, cost is secondary
    COST = "cost"    # Optimize for cost, speed is secondary
    QUALITY = "quality"  # Optimize for data quality, cost and speed secondary
    BALANCED = "balanced"  # Balance between cost, speed, and quality


class CostExceededError(Exception):
    """Error raised when a cost budget is exceeded."""
    
    def __init__(
        self, 
        total_cost: Decimal, 
        budget: Decimal, 
        actor_id: Optional[str] = None
    ):
        """
        Initialize error.
        
        Args:
            total_cost: Current total cost.
            budget: Budget limit.
            actor_id: Optional actor ID that triggered the error.
        """
        self.total_cost = total_cost
        self.budget = budget
        self.actor_id = actor_id
        
        message = f"Budget exceeded: {total_cost} > {budget}"
        if actor_id:
            message = f"{message} (triggered by actor {actor_id})"
        
        super().__init__(message)


class ActorCostEstimate:
    """Cost estimate for a single actor execution."""
    
    def __init__(
        self,
        actor_id: str,
        actor_name: str,
        fixed_cost: Decimal,
        variable_cost: Decimal,
        total_cost: Decimal,
        input_summary: Dict[str, Any],
    ):
        """
        Initialize cost estimate.
        
        Args:
            actor_id: ID of the actor.
            actor_name: Name of the actor.
            fixed_cost: Fixed cost component.
            variable_cost: Variable cost component.
            total_cost: Total estimated cost.
            input_summary: Summary of input parameters affecting cost.
        """
        self.actor_id = actor_id
        self.actor_name = actor_name
        self.fixed_cost = fixed_cost
        self.variable_cost = variable_cost
        self.total_cost = total_cost
        self.input_summary = input_summary
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "fixed_cost": float(self.fixed_cost),
            "variable_cost": float(self.variable_cost),
            "total_cost": float(self.total_cost),
            "input_summary": self.input_summary,
        }


class ExecutionCostRecord:
    """Record of an actor execution cost."""
    
    def __init__(
        self,
        actor_id: str,
        actor_name: str,
        actual_cost: Decimal,
        estimated_cost: Optional[Decimal] = None,
        run_id: Optional[str] = None,
        execution_time_secs: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize execution cost record.
        
        Args:
            actor_id: ID of the actor.
            actor_name: Name of the actor.
            actual_cost: Actual execution cost.
            estimated_cost: Estimated cost before execution.
            run_id: Actor run ID.
            execution_time_secs: Execution time in seconds.
            metadata: Additional metadata.
        """
        self.actor_id = actor_id
        self.actor_name = actor_name
        self.actual_cost = actual_cost
        self.estimated_cost = estimated_cost
        self.run_id = run_id
        self.execution_time_secs = execution_time_secs
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "actual_cost": float(self.actual_cost),
            "estimated_cost": float(self.estimated_cost) if self.estimated_cost is not None else None,
            "run_id": self.run_id,
            "execution_time_secs": self.execution_time_secs,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionCostRecord":
        """
        Create from dictionary.
        
        Args:
            data: Dictionary representation.
            
        Returns:
            ExecutionCostRecord instance.
        """
        record = cls(
            actor_id=data["actor_id"],
            actor_name=data["actor_name"],
            actual_cost=Decimal(str(data["actual_cost"])),
            run_id=data.get("run_id"),
            metadata=data.get("metadata", {}),
        )
        
        if "estimated_cost" in data and data["estimated_cost"] is not None:
            record.estimated_cost = Decimal(str(data["estimated_cost"]))
        
        if "execution_time_secs" in data and data["execution_time_secs"] is not None:
            record.execution_time_secs = data["execution_time_secs"]
        
        if "timestamp" in data:
            try:
                record.timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                pass
        
        return record


class CostOptimizer:
    """Optimizer for actor execution costs."""
    
    def __init__(
        self,
        actor_configurations=None,
        strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
    ):
        """
        Initialize cost optimizer.
        
        Args:
            actor_configurations: Actor configurations. If None, use default.
            strategy: Optimization strategy.
        """
        self.actor_configurations = actor_configurations or get_actor_configurations()
        self.strategy = strategy
    
    def optimize_actor_input(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        max_budget: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """
        Optimize actor input parameters for cost-efficiency.
        
        Args:
            actor_id: ID of the actor.
            input_data: Original input data.
            max_budget: Maximum budget for this execution.
            
        Returns:
            Optimized input data.
        """
        # Get actor configuration
        actor_config = self.actor_configurations.get_actor_config(actor_id)
        if not actor_config:
            # Can't optimize without configuration
            return input_data
        
        # Make a copy of the input data
        optimized_input = input_data.copy()
        
        # Apply strategy-specific optimizations
        if self.strategy == OptimizationStrategy.COST:
            optimized_input = self._optimize_for_cost(actor_config, optimized_input, max_budget)
        elif self.strategy == OptimizationStrategy.SPEED:
            optimized_input = self._optimize_for_speed(actor_config, optimized_input)
        elif self.strategy == OptimizationStrategy.QUALITY:
            optimized_input = self._optimize_for_quality(actor_config, optimized_input)
        else:  # BALANCED or unknown
            optimized_input = self._optimize_balanced(actor_config, optimized_input, max_budget)
        
        return optimized_input
    
    def _optimize_for_cost(
        self,
        actor_config: ActorConfig,
        input_data: Dict[str, Any],
        max_budget: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """
        Optimize input for lowest cost.
        
        Args:
            actor_config: Actor configuration.
            input_data: Original input data.
            max_budget: Maximum budget.
            
        Returns:
            Optimized input data.
        """
        optimized = input_data.copy()
        
        # Apply actor-specific optimizations
        if actor_config.id == "LpVuK3Zozwuipa5bp":  # LinkedIn Profile Bulk Scraper
            # Minimize data collection, disable expensive options
            optimized["includeSkills"] = False
            optimized["includeEducation"] = False
            optimized["includeExperience"] = True  # Keep this for basic info
            
        elif actor_config.id == "A3cAPGpwBEG8RJwse":  # LinkedIn Posts Bulk Scraper
            # Limit posts per profile and disable comments
            optimized["maxPostsPerProfile"] = min(optimized.get("maxPostsPerProfile", 10), 5)
            optimized["includeComments"] = False
            
        elif actor_config.id == "3rgDeYgLhr6XrVnjs":  # LinkedIn Company Profile Scraper
            # Disable expensive options
            optimized["includeJobs"] = False
            optimized["includePeople"] = False
            
        elif actor_config.id == "KoJrdxJCTtpon81KY":  # Facebook Posts Scraper
            # Limit posts and disable comments
            optimized["maxPostsPerPage"] = min(optimized.get("maxPostsPerPage", 10), 5)
            optimized["includeComments"] = False
            
        elif actor_config.id == "61RPP7dywgiy0JPD0":  # Twitter/X Scraper
            # Limit tweets and disable replies/retweets
            optimized["maxTweetsPerUser"] = min(optimized.get("maxTweetsPerUser", 20), 10)
            optimized["includeReplies"] = False
            optimized["includeRetweets"] = False
        
        # Ensure limits for array inputs
        for field_name, field_schema in actor_config.input_schema.items():
            if (field_schema.get("type") == "array" and 
                field_name in optimized and 
                isinstance(optimized[field_name], list)):
                
                # If we have a very tight budget, severely limit array inputs
                if max_budget and max_budget < Decimal('1.0'):
                    optimized[field_name] = optimized[field_name][:1]
                # Otherwise apply more moderate limits
                elif len(optimized[field_name]) > 5:
                    optimized[field_name] = optimized[field_name][:5]
        
        return optimized
    
    def _optimize_for_speed(
        self,
        actor_config: ActorConfig,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Optimize input for fastest execution.
        
        Args:
            actor_config: Actor configuration.
            input_data: Original input data.
            
        Returns:
            Optimized input data.
        """
        optimized = input_data.copy()
        
        # Common optimizations for speed
        
        # Increase concurrency for most actors
        if "maxConcurrency" in optimized:
            optimized["maxConcurrency"] = max(optimized.get("maxConcurrency", 2), 10)
        else:
            optimized["maxConcurrency"] = 10
        
        # Actor-specific optimizations
        if actor_config.id == "A3cAPGpwBEG8RJwse":  # LinkedIn Posts Bulk Scraper
            # Limit depth to speed up
            optimized["maxPostsPerProfile"] = min(optimized.get("maxPostsPerProfile", 20), 10)
            
        elif actor_config.id == "KoJrdxJCTtpon81KY":  # Facebook Posts Scraper
            # Limit depth to speed up
            optimized["maxPostsPerPage"] = min(optimized.get("maxPostsPerPage", 20), 10)
            
        elif actor_config.id == "61RPP7dywgiy0JPD0":  # Twitter/X Scraper
            # Limit depth to speed up
            optimized["maxTweetsPerUser"] = min(optimized.get("maxTweetsPerUser", 50), 20)
        
        return optimized
    
    def _optimize_for_quality(
        self,
        actor_config: ActorConfig,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Optimize input for best data quality.
        
        Args:
            actor_config: Actor configuration.
            input_data: Original input data.
            
        Returns:
            Optimized input data.
        """
        optimized = input_data.copy()
        
        # Actor-specific optimizations
        if actor_config.id == "LpVuK3Zozwuipa5bp":  # LinkedIn Profile Bulk Scraper
            # Enable all data collection
            optimized["includeSkills"] = True
            optimized["includeEducation"] = True
            optimized["includeExperience"] = True
            
        elif actor_config.id == "A3cAPGpwBEG8RJwse":  # LinkedIn Posts Bulk Scraper
            # Get more posts and include comments
            optimized["maxPostsPerProfile"] = max(optimized.get("maxPostsPerProfile", 10), 20)
            optimized["includeComments"] = True
            
        elif actor_config.id == "3rgDeYgLhr6XrVnjs":  # LinkedIn Company Profile Scraper
            # Include all data
            optimized["includeJobs"] = True
            optimized["includePeople"] = True
            
        elif actor_config.id == "KoJrdxJCTtpon81KY":  # Facebook Posts Scraper
            # Get more posts and include comments
            optimized["maxPostsPerPage"] = max(optimized.get("maxPostsPerPage", 10), 20)
            optimized["includeComments"] = True
            
        elif actor_config.id == "61RPP7dywgiy0JPD0":  # Twitter/X Scraper
            # Get more tweets and include replies/retweets
            optimized["maxTweetsPerUser"] = max(optimized.get("maxTweetsPerUser", 20), 50)
            optimized["includeReplies"] = True
            optimized["includeRetweets"] = True
        
        return optimized
    
    def _optimize_balanced(
        self,
        actor_config: ActorConfig,
        input_data: Dict[str, Any],
        max_budget: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """
        Apply balanced optimizations.
        
        Args:
            actor_config: Actor configuration.
            input_data: Original input data.
            max_budget: Maximum budget.
            
        Returns:
            Optimized input data.
        """
        # Start with moderate settings
        optimized = input_data.copy()
        
        # Apply some cost optimizations if budget is tight
        if max_budget and max_budget < Decimal('5.0'):
            # Limit array inputs moderately
            for field_name, field_schema in actor_config.input_schema.items():
                if (field_schema.get("type") == "array" and 
                    field_name in optimized and 
                    isinstance(optimized[field_name], list) and
                    len(optimized[field_name]) > 10):
                    
                    optimized[field_name] = optimized[field_name][:10]
        
        # Actor-specific balanced optimizations
        if actor_config.id == "LpVuK3Zozwuipa5bp":  # LinkedIn Profile Bulk Scraper
            # Include most important data
            optimized["includeExperience"] = True
            optimized["includeEducation"] = True
            optimized["includeSkills"] = max_budget is None or max_budget > Decimal('2.0')
            
        elif actor_config.id == "A3cAPGpwBEG8RJwse":  # LinkedIn Posts Bulk Scraper
            # Moderate posts, no comments unless budget allows
            optimized["maxPostsPerProfile"] = min(optimized.get("maxPostsPerProfile", 10), 10)
            optimized["includeComments"] = (max_budget is None or max_budget > Decimal('3.0'))
            
        elif actor_config.id == "KoJrdxJCTtpon81KY":  # Facebook Posts Scraper
            # Moderate posts, no comments unless budget allows
            optimized["maxPostsPerPage"] = min(optimized.get("maxPostsPerPage", 10), 10)
            optimized["includeComments"] = (max_budget is None or max_budget > Decimal('40.0'))
        
        # Set a reasonable concurrency
        if "maxConcurrency" not in optimized:
            optimized["maxConcurrency"] = 5
        
        return optimized


class CostManager:
    """
    Manager for actor execution costs.
    
    Tracks, estimates, and optimizes costs for actor executions.
    """
    
    def __init__(
        self,
        actor_configurations=None,
        budget_limit: Optional[Decimal] = None,
        alert_threshold: Optional[Decimal] = None,
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
        storage_dir: Optional[str] = None,
    ):
        """
        Initialize cost manager.
        
        Args:
            actor_configurations: Actor configurations. If None, use default.
            budget_limit: Overall budget limit. If None, no limit.
            alert_threshold: Threshold for budget alerts, as percentage (0-100).
            optimization_strategy: Strategy for cost optimization.
            storage_dir: Directory for history storage. If None, no persistence.
        """
        self.actor_configurations = actor_configurations or get_actor_configurations()
        self.budget_limit = budget_limit
        self.alert_threshold = alert_threshold or 80  # Default to 80%
        self.optimization_strategy = optimization_strategy
        self.storage_dir = storage_dir
        
        # Initialize optimizer
        self.optimizer = CostOptimizer(
            actor_configurations=self.actor_configurations,
            strategy=self.optimization_strategy,
        )
        
        # Initialize execution history
        self.execution_history: List[ExecutionCostRecord] = []
        self.current_executions: Dict[str, ActorCostEstimate] = {}
        self.total_cost: Decimal = Decimal('0')
        
        # Load history from storage if available
        if self.storage_dir:
            self._load_history()
    
    def set_budget(self, budget_limit: Optional[Union[Decimal, float, str]] = None) -> None:
        """
        Set overall budget limit.
        
        Args:
            budget_limit: Budget limit. If None, no limit.
        """
        if budget_limit is None:
            self.budget_limit = None
        else:
            self.budget_limit = Decimal(str(budget_limit))
    
    def set_optimization_strategy(self, strategy: OptimizationStrategy) -> None:
        """
        Set optimization strategy.
        
        Args:
            strategy: Optimization strategy.
        """
        self.optimization_strategy = strategy
        self.optimizer.strategy = strategy
    
    def estimate_cost(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
    ) -> ActorCostEstimate:
        """
        Estimate cost for actor execution.
        
        Args:
            actor_id: ID of the actor.
            input_data: Input data for the actor.
            
        Returns:
            Cost estimate.
            
        Raises:
            ValueError: If actor configuration is not found.
        """
        # Get actor configuration
        actor_config = self.actor_configurations.get_actor_config(actor_id)
        if not actor_config:
            raise ValueError(f"Actor configuration not found: {actor_id}")
        
        # Calculate fixed and variable costs
        fixed_cost = actor_config.cost_fixed
        variable_cost = Decimal('0')
        
        # Calculate variable cost based on cost model
        if actor_config.cost_model in (CostModel.PER_UNIT, CostModel.BASE_PLUS_UNIT):
            # Find appropriate field to count units
            unit_count = 0
            
            # First check required fields
            for field in actor_config.required_fields:
                if field in input_data and isinstance(input_data[field], list):
                    unit_count = len(input_data[field])
                    break
            
            # Calculate variable cost
            variable_cost = (
                actor_config.cost_variable * 
                Decimal(unit_count) / 
                Decimal(actor_config.cost_unit_size)
            )
        
        # Total cost
        total_cost = fixed_cost + variable_cost
        
        # Create input summary for tracking
        input_summary = {}
        for field, schema in actor_config.input_schema.items():
            if field in input_data:
                if isinstance(input_data[field], list):
                    # For lists, just store the count
                    input_summary[field] = f"{len(input_data[field])} items"
                else:
                    # For other types, store the value directly
                    input_summary[field] = input_data[field]
        
        # Create and return estimate
        estimate = ActorCostEstimate(
            actor_id=actor_id,
            actor_name=actor_config.name,
            fixed_cost=fixed_cost,
            variable_cost=variable_cost,
            total_cost=total_cost,
            input_summary=input_summary,
        )
        
        return estimate
    
    def check_budget(
        self,
        actor_id: str,
        estimated_cost: Decimal,
        run_id: Optional[str] = None,
    ) -> bool:
        """
        Check if execution is within budget.
        
        Args:
            actor_id: ID of the actor.
            estimated_cost: Estimated cost of execution.
            run_id: Optional run ID for tracking.
            
        Returns:
            True if within budget, False if budget would be exceeded.
        """
        # If no budget limit, always within budget
        if self.budget_limit is None:
            return True
        
        # Check if this execution would exceed the budget
        projected_cost = self.total_cost + estimated_cost
        
        # Check alert threshold
        if (projected_cost / self.budget_limit * 100) >= self.alert_threshold:
            logger.warning(
                "Budget alert threshold reached",
                current_cost=float(self.total_cost),
                new_cost=float(estimated_cost),
                projected=float(projected_cost),
                budget=float(self.budget_limit),
                threshold=self.alert_threshold,
                actor_id=actor_id,
                run_id=run_id,
            )
        
        # Check hard limit
        if projected_cost > self.budget_limit:
            logger.error(
                "Budget limit would be exceeded",
                current_cost=float(self.total_cost),
                new_cost=float(estimated_cost),
                projected=float(projected_cost),
                budget=float(self.budget_limit),
                actor_id=actor_id,
                run_id=run_id,
            )
            return False
        
        return True
    
    def start_execution(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        run_id: str,
        check_budget: bool = True,
        optimize: bool = True,
    ) -> Dict[str, Any]:
        """
        Start tracking an actor execution.
        
        Args:
            actor_id: ID of the actor.
            input_data: Input data for the actor.
            run_id: Run ID for tracking.
            check_budget: Whether to check budget limits.
            optimize: Whether to optimize input.
            
        Returns:
            Optimized input data (if optimize=True) or original input.
            
        Raises:
            CostExceededError: If budget would be exceeded.
            ValueError: If actor configuration is not found.
        """
        actor_config = self.actor_configurations.get_actor_config(actor_id)
        if not actor_config:
            raise ValueError(f"Actor configuration not found: {actor_id}")
        
        # Optimize input if requested
        if optimize:
            # Calculate per-actor budget if overall budget is set
            actor_budget = None
            if self.budget_limit is not None:
                remaining_budget = self.budget_limit - self.total_cost
                actor_budget = remaining_budget * Decimal('0.7')  # Leave 30% for other actors
            
            input_data = self.optimizer.optimize_actor_input(
                actor_id=actor_id,
                input_data=input_data,
                max_budget=actor_budget,
            )
        
        # Estimate cost
        estimate = self.estimate_cost(actor_id, input_data)
        
        # Check budget if requested
        if check_budget:
            within_budget = self.check_budget(
                actor_id=actor_id,
                estimated_cost=estimate.total_cost,
                run_id=run_id,
            )
            
            if not within_budget:
                raise CostExceededError(
                    total_cost=self.total_cost + estimate.total_cost,
                    budget=self.budget_limit,
                    actor_id=actor_id,
                )
        
        # Store execution
        self.current_executions[run_id] = estimate
        
        return input_data
    
    def record_execution(
        self,
        actor_id: str,
        run_id: str,
        actual_cost: Decimal,
        execution_time_secs: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Record completed actor execution.
        
        Args:
            actor_id: ID of the actor.
            run_id: Run ID for tracking.
            actual_cost: Actual cost of execution.
            execution_time_secs: Execution time in seconds.
            metadata: Additional metadata.
            
        Returns:
            True if within budget, False if budget has been exceeded.
            
        Raises:
            CostExceededError: If budget has been exceeded and raise_on_exceed=True.
        """
        actor_config = self.actor_configurations.get_actor_config(actor_id)
        if not actor_config:
            logger.error(f"Actor configuration not found: {actor_id}")
            actor_name = "Unknown Actor"
        else:
            actor_name = actor_config.name
        
        # Find estimate if available
        estimated_cost = None
        if run_id in self.current_executions:
            estimate = self.current_executions[run_id]
            estimated_cost = estimate.total_cost
            # Remove from current executions
            del self.current_executions[run_id]
        
        # Create execution record
        record = ExecutionCostRecord(
            actor_id=actor_id,
            actor_name=actor_name,
            actual_cost=actual_cost,
            estimated_cost=estimated_cost,
            run_id=run_id,
            execution_time_secs=execution_time_secs,
            metadata=metadata,
        )
        
        # Add to history
        self.execution_history.append(record)
        
        # Update total cost
        self.total_cost += actual_cost
        
        # Save history if storage is enabled
        if self.storage_dir:
            self._save_history()
        
        # Check if budget has been exceeded
        if self.budget_limit is not None and self.total_cost > self.budget_limit:
            logger.error(
                "Budget exceeded after execution",
                actor_id=actor_id,
                run_id=run_id,
                actual_cost=float(actual_cost),
                total_cost=float(self.total_cost),
                budget=float(self.budget_limit),
            )
            return False
        
        return True
    
    def get_cost_breakdown(
        self, 
        timeframe_days: Optional[int] = None
    ) -> CostBreakdown:
        """
        Get cost breakdown.
        
        Args:
            timeframe_days: Optional timeframe in days. If provided, only include
                           executions within the timeframe. If None, include all.
            
        Returns:
            Cost breakdown.
        """
        # Filter executions by timeframe if requested
        if timeframe_days is not None:
            cutoff = datetime.now() - timedelta(days=timeframe_days)
            executions = [
                rec for rec in self.execution_history 
                if rec.timestamp >= cutoff
            ]
        else:
            executions = self.execution_history
        
        # Calculate total cost
        total_cost = sum(rec.actual_cost for rec in executions)
        
        # Calculate cost per actor
        per_actor = {}
        for rec in executions:
            actor_name = rec.actor_name
            if actor_name not in per_actor:
                per_actor[actor_name] = Decimal('0')
            per_actor[actor_name] += rec.actual_cost
        
        # Return breakdown
        return CostBreakdown(
            total=total_cost,
            per_actor=per_actor,
        )
    
    def get_execution_history(
        self, 
        timeframe_days: Optional[int] = None,
        actor_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get execution history.
        
        Args:
            timeframe_days: Optional timeframe in days. If provided, only include
                           executions within the timeframe. If None, include all.
            actor_id: Optional actor ID to filter by.
            
        Returns:
            List of execution records as dictionaries.
        """
        # Filter executions
        executions = self.execution_history
        
        if timeframe_days is not None:
            cutoff = datetime.now() - timedelta(days=timeframe_days)
            executions = [rec for rec in executions if rec.timestamp >= cutoff]
        
        if actor_id is not None:
            executions = [rec for rec in executions if rec.actor_id == actor_id]
        
        # Convert to dictionaries
        return [rec.to_dict() for rec in executions]
    
    def _load_history(self) -> None:
        """Load execution history from storage."""
        if not self.storage_dir:
            return
        
        # Ensure directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Load history file
        history_file = os.path.join(self.storage_dir, "cost_history.json")
        if not os.path.exists(history_file):
            return
        
        try:
            with open(history_file, "r") as f:
                data = json.load(f)
            
            # Load records
            self.execution_history = [
                ExecutionCostRecord.from_dict(record_data)
                for record_data in data.get("records", [])
            ]
            
            # Calculate total cost
            self.total_cost = sum(
                record.actual_cost for record in self.execution_history
            )
            
            logger.info(
                "Loaded cost history",
                records_count=len(self.execution_history),
                total_cost=float(self.total_cost),
            )
        
        except Exception as e:
            logger.error("Error loading cost history", error=str(e))
    
    def _save_history(self) -> None:
        """Save execution history to storage."""
        if not self.storage_dir:
            return
        
        # Ensure directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        
        try:
            # Convert records to dictionaries
            records_data = [rec.to_dict() for rec in self.execution_history]
            
            # Create history data
            history_data = {
                "records": records_data,
                "total_cost": float(self.total_cost),
                "updated_at": datetime.now().isoformat(),
            }
            
            # Save to file
            history_file = os.path.join(self.storage_dir, "cost_history.json")
            with open(history_file, "w") as f:
                json.dump(history_data, f, indent=2)
            
        except Exception as e:
            logger.error("Error saving cost history", error=str(e))
    
    def get_budget_status(self) -> Dict[str, Any]:
        """
        Get current budget status.
        
        Returns:
            Dictionary with budget status information.
        """
        status = {
            "total_cost": float(self.total_cost),
            "budget_limit": float(self.budget_limit) if self.budget_limit else None,
            "alert_threshold": self.alert_threshold,
        }
        
        if self.budget_limit:
            status["budget_remaining"] = float(max(Decimal('0'), self.budget_limit - self.total_cost))
            status["budget_used_percent"] = float(min(Decimal('100'), self.total_cost / self.budget_limit * 100))
            status["budget_remaining_percent"] = float(max(Decimal('0'), 100 - (self.total_cost / self.budget_limit * 100)))
        
        return status
    
    def predict_cost(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Predict cost and execution time based on historical data.
        
        Args:
            actor_id: ID of the actor.
            input_data: Input data for the actor.
            
        Returns:
            Dictionary with cost and time predictions.
        """
        # Get basic estimate
        estimate = self.estimate_cost(actor_id, input_data)
        
        # Find similar executions in history
        similar_executions = []
        for rec in self.execution_history:
            if rec.actor_id == actor_id:
                similar_executions.append(rec)
        
        # Calculate prediction
        prediction = {
            "estimated_cost": float(estimate.total_cost),
            "fixed_cost": float(estimate.fixed_cost),
            "variable_cost": float(estimate.variable_cost),
        }
        
        # If we have historical data, refine the prediction
        if similar_executions:
            # Calculate average estimation error
            errors = []
            for rec in similar_executions:
                if rec.estimated_cost is not None:
                    error_ratio = rec.actual_cost / rec.estimated_cost
                    errors.append(error_ratio)
            
            if errors:
                avg_error = sum(errors) / len(errors)
                prediction["adjusted_cost"] = float(estimate.total_cost * avg_error)
                prediction["confidence"] = min(1.0, 1.0 / (sum((e - avg_error) ** 2 for e in errors) / len(errors) + 0.1))
            
            # Calculate predicted execution time
            if any(rec.execution_time_secs for rec in similar_executions):
                times = [rec.execution_time_secs for rec in similar_executions if rec.execution_time_secs]
                if times:
                    prediction["estimated_time_secs"] = sum(times) / len(times)
        
        return prediction 