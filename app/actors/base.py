"""
Base Apify actor implementation with common functionality.

This module provides a base class for all Apify actor integrations,
including retry logic, error handling, and standardized response processing.
"""

import asyncio
import time
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

import structlog
from pydantic import BaseModel, Field

# Import Apify client components with error handling
try:
    from apify_client import ApifyClient
    from apify_client import ApifyClientAsync
    APIFY_CLIENT_AVAILABLE = True
except ImportError:
    APIFY_CLIENT_AVAILABLE = False
    ApifyClient = None
    ApifyClientAsync = None

from app.core.config import settings
from app.core.exceptions import ApifyActorException, CostExceededException


logger = structlog.get_logger(__name__)
T = TypeVar('T', bound=BaseModel)


class ActorJobStatus(str, Enum):
    """Enum for actor job statuses."""
    READY = "READY"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMING_OUT = "TIMING-OUT"
    TIMED_OUT = "TIMED-OUT"
    ABORTING = "ABORTING"
    ABORTED = "ABORTED"


class ActorRunOptions(BaseModel):
    """Options for running an Apify actor."""
    
    build: Optional[str] = Field(default=None, description="Actor build to run.")
    memory_mbytes: Optional[int] = Field(default=None, description="Memory limit for the actor run in megabytes.")
    timeout_secs: Optional[int] = Field(default=None, description="Timeout for the actor run in seconds.")
    wait_for_finish: Optional[int] = Field(default=None, 
                                         description="Number of seconds to wait for the actor run to finish. None means wait indefinitely.")
    webhook_id: Optional[str] = Field(default=None, description="ID of a webhook to associate with the actor run.")


class ActorRunResult(BaseModel):
    """Result of an Apify actor run."""
    
    run_id: str = Field(..., description="ID of the actor run.")
    actor_id: str = Field(..., description="ID of the actor that was run.")
    status: str = Field(..., description="Status of the actor run.")
    started_at: datetime = Field(..., description="Time when the actor run started.")
    finished_at: Optional[datetime] = Field(default=None, description="Time when the actor run finished.")
    items: List[Dict[str, Any]] = Field(default_factory=list, description="Dataset items produced by the actor run.")
    items_count: int = Field(default=0, description="Number of items in the dataset.")
    duration_secs: Optional[float] = Field(default=None, description="Duration of the actor run in seconds.")
    cost: Decimal = Field(default=Decimal('0.00'), description="Cost of the actor run.")
    error_message: Optional[str] = Field(default=None, description="Error message if the actor run failed.")
    success: bool = Field(default=True, description="Whether the actor run was successful.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the actor run.")


class BaseActor:
    """
    Base class for Apify actor integrations.
    
    Handles authentication, retries, error handling, and standardized response processing.
    """
    
    def __init__(
        self,
        actor_id: str,
        api_token: Optional[str] = None,
        max_retries: Optional[int] = None,
        retry_delay_ms: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
    ) -> None:
        """
        Initialize the base actor.
        
        Args:
            actor_id: ID of the Apify actor.
            api_token: Apify API token. If not provided, it will be loaded from settings.
            max_retries: Maximum number of retries for failed requests.
            retry_delay_ms: Delay between retries in milliseconds.
            timeout_seconds: Default timeout for actor runs in seconds.
        """
        
        self.actor_id = actor_id
        self.api_token = api_token or settings.apify_api_token
        self.max_retries = max_retries or 3  # Default to 3 retries
        self.retry_delay_ms = retry_delay_ms or 1000  # Default to 1 second
        self.timeout_seconds = timeout_seconds or settings.default_timeout
        
        # Initialize clients if available
        self.client = None
        self.async_client = None
        self.actor = None
        self.async_actor = None
        
        if APIFY_CLIENT_AVAILABLE and self.api_token:
            try:
                self.client = ApifyClient(token=self.api_token, max_retries=self.max_retries)
                self.async_client = ApifyClientAsync(token=self.api_token, max_retries=self.max_retries)
                
                # Get actor client
                self.actor = self.client.actor(actor_id)
                self.async_actor = self.async_client.actor(actor_id)
            except Exception as e:
                logger.warning("Failed to initialize Apify clients", error=str(e))
        else:
            logger.warning("Apify client not available or no API token provided")
        
        # Logger setup with actor context
        self.logger = logger.bind(actor_id=actor_id)
    
    def _log_actor_call(self, input_data: Dict[str, Any], options: Optional[ActorRunOptions] = None) -> None:
        """Log actor call details."""
        log_data = {
            "actor_id": self.actor_id,
            "input_data_keys": list(input_data.keys()),
        }
        
        if options:
            log_data["timeout_secs"] = options.timeout_secs
            log_data["memory_mbytes"] = options.memory_mbytes
        
        self.logger.info("Starting actor run", **log_data)
    
    def _calculate_cost(self, run: Dict[str, Any]) -> Decimal:
        """
        Calculate the cost of an actor run.
        
        Args:
            run: Actor run data.
            
        Returns:
            Calculated cost as a Decimal.
        """
        # Extract compute units used or estimate
        compute_units = Decimal(str(run.get("computeUnits", 0) or 0))
        
        # Simple cost calculation (can be extended for more complex cost models)
        # Using 0.001 USD per compute unit as a default
        cost_per_unit = Decimal('0.001')
        return compute_units * cost_per_unit
    
    def _process_run_result(self, run: Dict[str, Any], items: List[Dict[str, Any]]) -> ActorRunResult:
        """
        Process the raw actor run result and dataset items into a standardized format.
        
        Args:
            run: Raw actor run data from Apify.
            items: Dataset items from the actor run.
            
        Returns:
            Standardized actor run result.
        """
        # Helper function to parse datetime from various formats
        def parse_datetime(dt_value):
            if not dt_value:
                return datetime.now()
            
            # If it's already a datetime object, return it
            if isinstance(dt_value, datetime):
                return dt_value
            
            # If it's a string, parse it
            if isinstance(dt_value, str):
                # Handle ISO format with Z timezone
                if dt_value.endswith('Z'):
                    dt_value = dt_value.replace('Z', '+00:00')
                return datetime.fromisoformat(dt_value)
            
            # If it's a number (timestamp), convert it
            if isinstance(dt_value, (int, float)):
                # Apify timestamps are typically in milliseconds
                if dt_value > 1e10:  # If it's a large number, assume milliseconds
                    return datetime.fromtimestamp(dt_value / 1000)
                else:  # Otherwise assume seconds
                    return datetime.fromtimestamp(dt_value)
            
            # Fallback to current time
            return datetime.now()
        
        # Calculate duration if both start and end times are available
        started_at = parse_datetime(run.get("startedAt"))
        finished_at = parse_datetime(run.get("finishedAt")) if run.get("finishedAt") else None
        
        duration_secs = None
        if finished_at:
            duration_secs = (finished_at - started_at).total_seconds()
        
        # Calculate cost
        cost = self._calculate_cost(run)
        
        # Check for errors
        error_message = None
        success = True
        status = run.get("status", "UNKNOWN")
        if status == "FAILED":
            error_message = run.get("statusMessage", "Actor run failed without a specific error message.")
            success = False
        
        # Build the result
        return ActorRunResult(
            run_id=run["id"],
            actor_id=self.actor_id,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            items=items,
            items_count=len(items),
            duration_secs=duration_secs,
            cost=cost,
            error_message=error_message,
            success=success,
            metadata={
                "build_id": run.get("buildId"),
                "compute_units": run.get("computeUnits"),
                "usage_bytes": run.get("statsUsageBytes"),
                "platform": run.get("platform"),
            },
        )

    async def run_async(
        self,
        input_data: Dict[str, Any],
        options: Optional[ActorRunOptions] = None,
        max_budget: Optional[float] = None,
        output_model: Optional[Type[T]] = None,
    ) -> Union[ActorRunResult, List[T]]:
        """
        Run an actor asynchronously and get results with retry support.
        
        Args:
            input_data: Input data for the actor.
            options: Actor run options.
            max_budget: Maximum allowed cost for this actor run.
            output_model: Optional Pydantic model to parse output data into.
            
        Returns:
            Standardized actor run result or list of parsed models if output_model is provided.
            
        Raises:
            ApifyActorException: If the actor run fails.
            CostExceededException: If the estimated cost exceeds the max_budget.
        """
        options = options or ActorRunOptions()
        self._log_actor_call(input_data, options)
        
        # Prepare webhooks parameter
        webhooks = None
        if options.webhook_id:
            webhooks = [{"id": options.webhook_id}]
            
        # Start actor run with retries
        run = None
        retry_count = 0
        
        # Initialize retry parameters
        max_retries = self.max_retries
        base_delay_ms = self.retry_delay_ms
        
        while retry_count <= max_retries:
            try:
                # Use the correct Apify client parameters
                run = await self.async_actor.call(
                    run_input=input_data,
                    build=options.build,
                    memory_mbytes=options.memory_mbytes,
                    timeout_secs=options.timeout_secs or self.timeout_seconds,
                    webhooks=webhooks,
                    wait_secs=options.wait_for_finish,
                )
                
                # call() returns None if the run fails
                if run is None:
                    self.logger.error("Actor call returned None - run failed")
                    if retry_count >= max_retries:
                        raise ApifyActorException(
                            message=f"Actor run failed after {retry_count} retries: call returned None",
                            actor_id=self.actor_id,
                        )
                else:
                    self.logger.info(
                        "Actor run completed", 
                        run_id=run.get("id"), 
                        status=run.get("status"),
                    )
                    
                    # Check for successful run
                    if run.get("status") == ActorJobStatus.SUCCEEDED:
                        break
                    
                    # Handle specific failures
                    if run.get("status") == ActorJobStatus.FAILED:
                        error_message = run.get("statusMessage", "Actor run failed without a specific error message.")
                        self.logger.error(
                            "Actor run failed", 
                            run_id=run.get("id"), 
                            error=error_message,
                        )
                        
                        # If we've retried enough times, raise an exception
                        if retry_count >= max_retries:
                            raise ApifyActorException(
                                message=f"Actor run failed after {retry_count} retries: {error_message}",
                                actor_id=self.actor_id,
                                run_id=run.get("id"),
                                details={"status_message": error_message},
                            )
                
                # Prepare for retry
                retry_count += 1
                delay_ms = base_delay_ms * (2 ** retry_count)  # Exponential backoff
                
                self.logger.info(
                    f"Retrying actor run (attempt {retry_count}/{max_retries})",
                    delay_ms=delay_ms,
                )
                
                await asyncio.sleep(delay_ms / 1000)  # Convert ms to seconds
                
            except Exception as e:
                self.logger.error(
                    "Error during actor run",
                    error=str(e),
                    retry_count=retry_count,
                )
                
                # If we've retried enough times, raise the exception
                if retry_count >= max_retries:
                    raise ApifyActorException(
                        message=f"Actor run failed after {retry_count} retries: {str(e)}",
                        actor_id=self.actor_id,
                    )
                
                # Prepare for retry
                retry_count += 1
                delay_ms = base_delay_ms * (2 ** retry_count)  # Exponential backoff
                await asyncio.sleep(delay_ms / 1000)  # Convert ms to seconds
        
        # Check if we have a successful run
        if not run or run.get("status") != ActorJobStatus.SUCCEEDED:
            raise ApifyActorException(
                message="Actor run did not complete successfully",
                actor_id=self.actor_id,
                run_id=run.get("id") if run else None,
            )
        
        # Calculate cost and check budget
        cost = self._calculate_cost(run)
        if max_budget is not None and cost > Decimal(str(max_budget)):
            raise CostExceededException(
                message=f"Actor run cost ({cost}) exceeds maximum budget ({max_budget})",
                current_cost=float(cost),
                max_budget=float(max_budget),
            )
            
        # Get dataset items
        dataset_items = []
        if "defaultDatasetId" in run:
            dataset_client = self.async_client.dataset(run["defaultDatasetId"])
            
            # Get items - this returns a ListPage object
            items_list_result = await dataset_client.list_items(limit=1000)
            
            # Extract items from ListPage object
            if hasattr(items_list_result, "items"):
                # It's a ListPage object
                dataset_items = list(items_list_result.items)
                total_count = items_list_result.total if hasattr(items_list_result, "total") else len(dataset_items)
                
                # Handle larger datasets with pagination
                offset = len(dataset_items)
                
                while offset < total_count:
                    next_items_result = await dataset_client.list_items(offset=offset, limit=1000)
                    
                    if hasattr(next_items_result, "items"):
                        next_items = list(next_items_result.items)
                    else:
                        next_items = []
                    
                    if not next_items:
                        break
                        
                    dataset_items.extend(next_items)
                    offset += len(next_items)
            else:
                # Fallback for dict response (shouldn't happen with modern client)
                dataset_items = items_list_result.get("items", [])

            self.logger.info(
                "Retrieved dataset items",
                dataset_id=run["defaultDatasetId"],
                item_count=len(dataset_items),
            )
        
        # Process results
        result = self._process_run_result(run, dataset_items)
        
        # Convert to output model if provided
        if output_model and dataset_items:
            try:
                return [output_model.model_validate(item) for item in dataset_items]
            except Exception as e:
                self.logger.error(
                    "Error converting dataset items to output model", 
                    error=str(e),
                    model=output_model.__name__,
                )
                # Fall back to returning the raw result
                return result
        
        return result
    
    def run(
        self,
        input_data: Dict[str, Any],
        options: Optional[ActorRunOptions] = None,
        max_budget: Optional[float] = None,
        output_model: Optional[Type[T]] = None,
    ) -> Union[ActorRunResult, List[T]]:
        """
        Run an actor synchronously and get results with retry support.
        
        Args:
            input_data: Input data for the actor.
            options: Actor run options.
            max_budget: Maximum allowed cost for this actor run.
            output_model: Optional Pydantic model to parse output data into.
            
        Returns:
            Standardized actor run result or list of parsed models if output_model is provided.
            
        Raises:
            ApifyActorException: If the actor run fails.
            CostExceededException: If the estimated cost exceeds the max_budget.
        """
        options = options or ActorRunOptions()
        self._log_actor_call(input_data, options)
        
        # Prepare webhooks parameter
        webhooks = None
        if options.webhook_id:
            webhooks = [{"id": options.webhook_id}]
            
        # Start actor run with retries
        run = None
        retry_count = 0
        
        # Initialize retry parameters
        max_retries = self.max_retries
        base_delay_ms = self.retry_delay_ms
        
        while retry_count <= max_retries:
            try:
                # Use the correct Apify client parameters
                run = self.actor.call(
                    run_input=input_data,
                    build=options.build,
                    memory_mbytes=options.memory_mbytes,
                    timeout_secs=options.timeout_secs or self.timeout_seconds,
                    webhooks=webhooks,
                    wait_secs=options.wait_for_finish,
                )
                
                # call() returns None if the run fails
                if run is None:
                    self.logger.error("Actor call returned None - run failed")
                    if retry_count >= max_retries:
                        raise ApifyActorException(
                            message=f"Actor run failed after {retry_count} retries: call returned None",
                            actor_id=self.actor_id,
                        )
                else:
                    self.logger.info(
                        "Actor run completed", 
                        run_id=run.get("id"), 
                        status=run.get("status"),
                    )
                    
                    # Check for successful run
                    if run.get("status") == ActorJobStatus.SUCCEEDED:
                        break
                    
                    # Handle specific failures
                    if run.get("status") == ActorJobStatus.FAILED:
                        error_message = run.get("statusMessage", "Actor run failed without a specific error message.")
                        self.logger.error(
                            "Actor run failed", 
                            run_id=run.get("id"), 
                            error=error_message,
                        )
                        
                        # If we've retried enough times, raise an exception
                        if retry_count >= max_retries:
                            raise ApifyActorException(
                                message=f"Actor run failed after {retry_count} retries: {error_message}",
                                actor_id=self.actor_id,
                                run_id=run.get("id"),
                                details={"status_message": error_message},
                            )
                
                # Prepare for retry
                retry_count += 1
                delay_ms = base_delay_ms * (2 ** retry_count)  # Exponential backoff
                
                self.logger.info(
                    f"Retrying actor run (attempt {retry_count}/{max_retries})",
                    delay_ms=delay_ms,
                )
                
                time.sleep(delay_ms / 1000)  # Convert ms to seconds
                
            except Exception as e:
                self.logger.error(
                    "Error during actor run",
                    error=str(e),
                    retry_count=retry_count,
                )
                
                # If we've retried enough times, raise the exception
                if retry_count >= max_retries:
                    raise ApifyActorException(
                        message=f"Actor run failed after {retry_count} retries: {str(e)}",
                        actor_id=self.actor_id,
                    )
                
                # Prepare for retry
                retry_count += 1
                delay_ms = base_delay_ms * (2 ** retry_count)  # Exponential backoff
                time.sleep(delay_ms / 1000)  # Convert ms to seconds
        
        # Check if we have a successful run
        if not run or run.get("status") != ActorJobStatus.SUCCEEDED:
            raise ApifyActorException(
                message="Actor run did not complete successfully",
                actor_id=self.actor_id,
                run_id=run.get("id") if run else None,
            )
        
        # Calculate cost and check budget
        cost = self._calculate_cost(run)
        if max_budget is not None and cost > Decimal(str(max_budget)):
            raise CostExceededException(
                message=f"Actor run cost ({cost}) exceeds maximum budget ({max_budget})",
                current_cost=float(cost),
                max_budget=float(max_budget),
            )
            
        # Get dataset items
        dataset_items = []
        if "defaultDatasetId" in run:
            dataset_client = self.client.dataset(run["defaultDatasetId"])
            
            # Get items - this returns a ListPage object
            items_list_result = dataset_client.list_items(limit=1000)
            
            # Extract items from ListPage object
            if hasattr(items_list_result, "items"):
                # It's a ListPage object
                dataset_items = list(items_list_result.items)
                total_count = items_list_result.total if hasattr(items_list_result, "total") else len(dataset_items)
                
                # Handle larger datasets with pagination
                offset = len(dataset_items)
                
                while offset < total_count:
                    next_items_result = dataset_client.list_items(offset=offset, limit=1000)
                    
                    if hasattr(next_items_result, "items"):
                        next_items = list(next_items_result.items)
                    else:
                        next_items = []
                    
                    if not next_items:
                        break
                        
                    dataset_items.extend(next_items)
                    offset += len(next_items)
            else:
                # Fallback for dict response (shouldn't happen with modern client)
                dataset_items = items_list_result.get("items", [])

            self.logger.info(
                "Retrieved dataset items",
                dataset_id=run["defaultDatasetId"],
                item_count=len(dataset_items),
            )
        
        # Process results
        result = self._process_run_result(run, dataset_items)
        
        # Convert to output model if provided
        if output_model and dataset_items:
            try:
                return [output_model.model_validate(item) for item in dataset_items]
            except Exception as e:
                self.logger.error(
                    "Error converting dataset items to output model", 
                    error=str(e),
                    model=output_model.__name__,
                )
                # Fall back to returning the raw result
                return result
        
        return result

    async def get_info_async(self) -> Dict[str, Any]:
        """
        Get information about the actor asynchronously.
        
        Returns:
            Actor information.
        """
        return await self.async_actor.get()
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the actor.
        
        Returns:
            Actor information.
        """
        return self.actor.get()
    
    async def get_last_run_async(self) -> Optional[Dict[str, Any]]:
        """
        Get the last actor run asynchronously.
        
        Returns:
            Last actor run or None if no runs exist.
        """
        runs = await self.async_actor.list_runs(desc=True, limit=1)
        if runs and runs.get("items"):
            return runs["items"][0]
        return None
    
    def get_last_run(self) -> Optional[Dict[str, Any]]:
        """
        Get the last actor run.
        
        Returns:
            Last actor run or None if no runs exist.
        """
        runs = self.actor.list_runs(desc=True, limit=1)
        if runs and runs.get("items"):
            return runs["items"][0]
        return None
        
    def estimate_cost(self, input_data: Dict[str, Any]) -> Decimal:
        """
        Estimate the cost of running an actor with the given input data.
        This is a very simple estimation based on actor-specific logic.
        
        Args:
            input_data: Input data for the actor.
            
        Returns:
            Estimated cost as a Decimal.
        """
        # Default implementation provides a very basic estimation
        # Specific actor implementations should override this method
        settings = get_settings()
        actor_configs = settings.actor_configs
        
        # Get actor config by ID if available
        for actor_config in actor_configs.values():
            if actor_config.get("actor_id") == self.actor_id:
                # Simple estimation for bulk actors
                if "cost_per_1k" in actor_config:
                    # Estimate based on number of items in the input
                    cost_per_1k = Decimal(str(actor_config["cost_per_1k"]))
                    item_count = 0
                    
                    # Find the appropriate field to count
                    for field in actor_config.get("required_fields", []):
                        if field in input_data and isinstance(input_data[field], list):
                            item_count = len(input_data[field])
                            break
                    
                    return (cost_per_1k * Decimal(item_count)) / Decimal('1000')
                
                # Fixed base cost + per-item cost
                if "cost_base" in actor_config:
                    cost_base = Decimal(str(actor_config["cost_base"]))
                    
                    # If there's also a per-item cost
                    if "cost_per_company" in actor_config or "cost_per_contact" in actor_config or "cost_per_page" in actor_config:
                        per_item_cost_key = [k for k in actor_config.keys() if k.startswith("cost_per_")][0]
                        per_item_cost = Decimal(str(actor_config[per_item_cost_key]))
                        
                        item_count = 0
                        for field in actor_config.get("required_fields", []):
                            if field in input_data and isinstance(input_data[field], list):
                                item_count = len(input_data[field])
                                break
                        
                        return cost_base + (per_item_cost * Decimal(item_count))
                    
                    return cost_base
                
                # Cost per query
                if "cost_per_query" in actor_config:
                    return Decimal(str(actor_config["cost_per_query"]))
        
        # Default fallback estimation (0.10 USD)
        return Decimal('0.10') 