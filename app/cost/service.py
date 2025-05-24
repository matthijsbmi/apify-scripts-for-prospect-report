"""
Cost management service for application integration.

Provides cost management functionality for use in other services.
"""

import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

import structlog

from app.actors.base import ActorRunOptions, ActorRunResult
from app.cost.manager import CostManager, OptimizationStrategy, CostExceededError

logger = structlog.get_logger(__name__)


class CostService:
    """
    Service for cost management functionality.
    
    Provides cost management for use in other services.
    """
    
    _instance = None  # Singleton instance
    
    @classmethod
    def get_instance(cls) -> "CostService":
        """
        Get singleton instance.
        
        Returns:
            Singleton instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize the cost service."""
        # Create storage directory
        storage_dir = "data/cost"
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize cost manager
        self.cost_manager = CostManager(
            storage_dir=storage_dir,
            optimization_strategy=OptimizationStrategy.BALANCED,
        )
    
    def apply_budget_to_options(
        self,
        options: ActorRunOptions,
        max_budget: Optional[float],
    ) -> ActorRunOptions:
        """
        Apply budget to actor run options.
        
        Args:
            options: Actor run options.
            max_budget: Maximum budget for the execution.
            
        Returns:
            Updated options with budget.
        """
        if max_budget is not None:
            # Clone options
            if options is None:
                options = ActorRunOptions()
            else:
                options = options.copy()
            
            # Apply memory optimization for budget
            if max_budget < 5.0:
                # For small budgets, use minimal memory
                options.memory_mbytes = min(
                    options.memory_mbytes or 1024,
                    512,  # Limit to 512 MB for small budgets
                )
            elif max_budget < 10.0:
                # For medium budgets, use moderate memory
                options.memory_mbytes = min(
                    options.memory_mbytes or 1024,
                    1024,  # Limit to 1 GB for medium budgets
                )
        
        return options
    
    def optimize_actor_input(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        max_budget: Optional[float] = None,
        strategy: Optional[Union[str, OptimizationStrategy]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize actor input.
        
        Args:
            actor_id: ID of the actor.
            input_data: Input data for the actor.
            max_budget: Maximum budget for the execution.
            strategy: Optional strategy to use for this optimization only.
            
        Returns:
            Optimized input data.
        """
        # Convert max_budget to Decimal if provided
        max_budget_decimal = None
        if max_budget is not None:
            max_budget_decimal = Decimal(str(max_budget))
        
        # Use current strategy if not provided
        current_strategy = self.cost_manager.optimization_strategy
        
        # Set temporary strategy if provided
        if strategy is not None:
            if isinstance(strategy, str):
                strategy = OptimizationStrategy(strategy.lower())
            self.cost_manager.set_optimization_strategy(strategy)
        
        try:
            # Optimize input
            optimized_input = self.cost_manager.optimizer.optimize_actor_input(
                actor_id=actor_id,
                input_data=input_data,
                max_budget=max_budget_decimal,
            )
            return optimized_input
        
        finally:
            # Restore strategy if we changed it
            if strategy is not None:
                self.cost_manager.set_optimization_strategy(current_strategy)
    
    def start_actor_execution(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        run_id: str,
        max_budget: Optional[float] = None,
        optimize: bool = True,
    ) -> Dict[str, Any]:
        """
        Start tracking an actor execution.
        
        Args:
            actor_id: ID of the actor.
            input_data: Input data for the actor.
            run_id: Run ID for tracking.
            max_budget: Maximum budget for the execution.
            optimize: Whether to optimize input.
            
        Returns:
            Optimized input data (if optimize=True) or original input.
            
        Raises:
            CostExceededError: If budget would be exceeded.
        """
        # Convert max_budget to Decimal if provided
        max_budget_decimal = None
        if max_budget is not None:
            max_budget_decimal = Decimal(str(max_budget))
        
        # Consider both execution budget and overall budget
        if max_budget_decimal is not None and self.cost_manager.budget_limit is not None:
            # Use the lower of the two budgets
            effective_budget = min(max_budget_decimal, self.cost_manager.budget_limit)
        else:
            # Use whichever budget is set
            effective_budget = max_budget_decimal or self.cost_manager.budget_limit
        
        # Start execution
        optimized_input = self.cost_manager.start_execution(
            actor_id=actor_id,
            input_data=input_data,
            run_id=run_id,
            check_budget=True,  # Always check budget
            optimize=optimize,
        )
        
        return optimized_input
    
    def record_actor_result(
        self,
        actor_id: str,
        result: ActorRunResult,
    ) -> bool:
        """
        Record actor execution result.
        
        Args:
            actor_id: ID of the actor.
            result: Actor execution result.
            
        Returns:
            True if within budget, False if budget has been exceeded.
        """
        return self.cost_manager.record_execution(
            actor_id=actor_id,
            run_id=result.run_id,
            actual_cost=result.cost,
            execution_time_secs=result.duration_secs,
            metadata={
                "status": result.status,
                "items_count": result.items_count,
            },
        )
    
    def estimate_cost(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
    ) -> float:
        """
        Estimate cost for actor execution.
        
        Args:
            actor_id: ID of the actor.
            input_data: Input data for the actor.
            
        Returns:
            Estimated cost.
            
        Raises:
            ValueError: If actor configuration is not found.
        """
        estimate = self.cost_manager.estimate_cost(actor_id, input_data)
        return float(estimate.total_cost)
    
    def set_budget(self, budget_limit: Optional[float] = None) -> None:
        """
        Set budget limit.
        
        Args:
            budget_limit: Budget limit. If None, no limit.
        """
        self.cost_manager.set_budget(budget_limit)
    
    def set_optimization_strategy(
        self,
        strategy: Union[str, OptimizationStrategy],
    ) -> None:
        """
        Set optimization strategy.
        
        Args:
            strategy: Optimization strategy name or enum value.
            
        Raises:
            ValueError: If strategy is invalid.
        """
        # Convert string to enum value if needed
        if isinstance(strategy, str):
            try:
                strategy = OptimizationStrategy(strategy.lower())
            except ValueError:
                valid_strategies = [s.value for s in OptimizationStrategy]
                raise ValueError(
                    f"Invalid optimization strategy: {strategy}. "
                    f"Valid options are: {', '.join(valid_strategies)}"
                )
        
        # Set strategy
        self.cost_manager.set_optimization_strategy(strategy)
    
    def get_budget_status(self) -> Dict[str, Any]:
        """
        Get current budget status.
        
        Returns:
            Dictionary with budget status information.
        """
        return self.cost_manager.get_budget_status()
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get cost summary.
        
        Returns:
            Dictionary with cost summary information.
        """
        # Get recent and all-time breakdowns
        recent_breakdown = self.cost_manager.get_cost_breakdown(timeframe_days=30)
        all_breakdown = self.cost_manager.get_cost_breakdown()
        
        # Create summary
        summary = {
            "recent": {
                "total": float(recent_breakdown.total),
                "actors": len(recent_breakdown.per_actor),
            },
            "all_time": {
                "total": float(all_breakdown.total),
                "actors": len(all_breakdown.per_actor),
            },
            "budget": self.get_budget_status(),
        }
        
        # Get top actors
        if all_breakdown.per_actor:
            top_actors = sorted(
                all_breakdown.per_actor.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5]
            
            summary["top_actors"] = {
                name: float(cost) for name, cost in top_actors
            }
        
        return summary


def get_cost_service() -> CostService:
    """
    Get singleton cost service instance.
    
    Returns:
        Singleton cost service instance.
    """
    return CostService.get_instance() 