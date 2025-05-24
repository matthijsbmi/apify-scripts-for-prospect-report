"""
Cost management controller for API endpoints.

Provides API endpoints for cost management functionality.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

import structlog

from app.cost.manager import CostManager, OptimizationStrategy
from app.models.data import CostBreakdown

logger = structlog.get_logger(__name__)


class CostController:
    """
    Controller for cost management API endpoints.
    
    Provides a facade for cost management functionality.
    """
    
    def __init__(self, cost_manager: Optional[CostManager] = None):
        """
        Initialize the cost controller.
        
        Args:
            cost_manager: Cost manager instance. If None, create a new one.
        """
        self.cost_manager = cost_manager or CostManager(
            storage_dir="data/cost",  # Default storage directory
        )
    
    def get_budget_status(self) -> Dict[str, Any]:
        """
        Get current budget status.
        
        Returns:
            Dictionary with budget status information.
        """
        return self.cost_manager.get_budget_status()
    
    def set_budget(self, budget_limit: Optional[Union[Decimal, float, str]]) -> Dict[str, Any]:
        """
        Set budget limit.
        
        Args:
            budget_limit: Budget limit. If None, no limit.
            
        Returns:
            Updated budget status.
        """
        self.cost_manager.set_budget(budget_limit)
        return self.cost_manager.get_budget_status()
    
    def get_cost_breakdown(self, timeframe_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Get cost breakdown.
        
        Args:
            timeframe_days: Optional timeframe in days. If provided, only include
                           executions within the timeframe. If None, include all.
            
        Returns:
            Dictionary with cost breakdown information.
        """
        breakdown = self.cost_manager.get_cost_breakdown(timeframe_days)
        return {
            "total": float(breakdown.total),
            "per_actor": {
                actor_name: float(cost)
                for actor_name, cost in breakdown.per_actor.items()
            },
            "timeframe_days": timeframe_days,
        }
    
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
        return self.cost_manager.get_execution_history(
            timeframe_days=timeframe_days,
            actor_id=actor_id,
        )
    
    def set_optimization_strategy(
        self,
        strategy: Union[str, OptimizationStrategy],
    ) -> Dict[str, str]:
        """
        Set optimization strategy.
        
        Args:
            strategy: Optimization strategy name or enum value.
            
        Returns:
            Dictionary with strategy information.
            
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
        
        # Return info
        return {
            "strategy": strategy.value,
            "description": self._get_strategy_description(strategy),
        }
    
    def predict_cost(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Predict cost for actor execution.
        
        Args:
            actor_id: ID of the actor.
            input_data: Input data for the actor.
            
        Returns:
            Dictionary with cost prediction information.
            
        Raises:
            ValueError: If actor configuration is not found.
        """
        return self.cost_manager.predict_cost(actor_id, input_data)
    
    def optimize_input(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        strategy: Optional[Union[str, OptimizationStrategy]] = None,
        max_budget: Optional[Union[Decimal, float, str]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize input for actor execution.
        
        Args:
            actor_id: ID of the actor.
            input_data: Input data for the actor.
            strategy: Optional strategy to use for this optimization only.
            max_budget: Optional maximum budget for this execution.
            
        Returns:
            Dictionary with optimization information.
            
        Raises:
            ValueError: If actor configuration is not found.
        """
        # Convert max_budget to Decimal if provided
        if max_budget is not None:
            max_budget = Decimal(str(max_budget))
        
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
                max_budget=max_budget,
            )
            
            # Get estimates for both original and optimized input
            original_estimate = self.cost_manager.estimate_cost(actor_id, input_data)
            optimized_estimate = self.cost_manager.estimate_cost(actor_id, optimized_input)
            
            # Calculate savings
            original_cost = original_estimate.total_cost
            optimized_cost = optimized_estimate.total_cost
            savings_absolute = original_cost - optimized_cost
            savings_percent = (
                (savings_absolute / original_cost) * 100
                if original_cost > 0 else Decimal('0')
            )
            
            # Create result
            result = {
                "optimized_input": optimized_input,
                "original_cost": float(original_cost),
                "optimized_cost": float(optimized_cost),
                "savings_absolute": float(savings_absolute),
                "savings_percent": float(savings_percent),
                "strategy": self.cost_manager.optimization_strategy.value,
            }
        
        finally:
            # Restore strategy if we changed it
            if strategy is not None:
                self.cost_manager.set_optimization_strategy(current_strategy)
        
        return result
    
    def _get_strategy_description(self, strategy: OptimizationStrategy) -> str:
        """
        Get description for optimization strategy.
        
        Args:
            strategy: Optimization strategy.
            
        Returns:
            Description string.
        """
        descriptions = {
            OptimizationStrategy.COST: (
                "Optimize for lowest cost, reducing data collection and API calls "
                "to the minimum necessary."
            ),
            OptimizationStrategy.SPEED: (
                "Optimize for fastest execution time, using higher concurrency "
                "and limiting depth of data collection."
            ),
            OptimizationStrategy.QUALITY: (
                "Optimize for best data quality, enabling all data collection "
                "options regardless of cost or time impact."
            ),
            OptimizationStrategy.BALANCED: (
                "Balance between cost, speed, and quality, with moderate settings "
                "for data collection and parallel processing."
            ),
        }
        
        return descriptions.get(
            strategy,
            "Custom optimization strategy"
        ) 