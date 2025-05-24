"""
Actor orchestration system.

This module provides the core orchestration system to manage the execution of multiple
Apify actors, handle dependencies, and optimize for parallel execution.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

import structlog
from pydantic import BaseModel, Field

from app.actors.base import BaseActor, ActorRunOptions, ActorRunResult
from app.actors.config import ActorConfig, get_actor_configurations
from app.models.data import Analysis, AnalysisStatus, ActorExecution, AnalysisParameters
from app.services.storage import get_storage_service


logger = structlog.get_logger(__name__)


class ExecutionStatus(str, Enum):
    """Status of an actor execution task."""
    
    PENDING = "pending"  # Waiting for dependencies
    SCHEDULED = "scheduled"  # Ready to execute
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Failed
    SKIPPED = "skipped"  # Skipped due to constraints
    CANCELLED = "cancelled"  # Cancelled by user or system


class ExecutionNode(BaseModel):
    """Node in the execution DAG representing an actor execution."""
    
    actor_id: str = Field(..., description="ID of the actor to execute")
    input_data: Dict[str, Any] = Field(..., description="Input data for the actor")
    dependencies: List[str] = Field(default_factory=list, 
                                description="IDs of nodes this node depends on")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING, 
                                description="Current status of this node")
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()), 
                      description="Unique ID for this node")
    estimated_cost: Decimal = Field(default=Decimal('0'), 
                                description="Estimated cost of execution")
    actual_cost: Optional[Decimal] = Field(default=None, 
                                       description="Actual cost after execution")
    result_id: Optional[str] = Field(default=None, 
                                 description="ID of the execution result")
    error_message: Optional[str] = Field(default=None, 
                                     description="Error message if failed")
    start_time: Optional[datetime] = Field(default=None, 
                                       description="When execution started")
    end_time: Optional[datetime] = Field(default=None, 
                                     description="When execution ended")
    retries: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout_seconds: Optional[int] = Field(default=None, 
                                       description="Execution timeout in seconds")
    memory_mbytes: Optional[int] = Field(default=None, 
                                     description="Memory limit in megabytes")


class ExecutionPlan(BaseModel):
    """Execution plan for a prospect analysis."""
    
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()), 
                      description="Unique ID for this plan")
    analysis_id: str = Field(..., description="ID of the associated analysis")
    nodes: Dict[str, ExecutionNode] = Field(default_factory=dict, 
                                       description="Execution nodes in the plan")
    node_dependencies: Dict[str, List[str]] = Field(default_factory=dict, 
                                              description="Reverse dependencies")
    total_estimated_cost: Decimal = Field(default=Decimal('0'), 
                                     description="Total estimated cost")
    total_actual_cost: Decimal = Field(default=Decimal('0'), 
                                   description="Total actual cost")
    max_budget: Optional[Decimal] = Field(default=None, 
                                     description="Maximum budget")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING, 
                                description="Status of the plan execution")
    start_time: Optional[datetime] = Field(default=None, 
                                       description="When execution started")
    end_time: Optional[datetime] = Field(default=None, 
                                     description="When execution ended")
    error_message: Optional[str] = Field(default=None, 
                                     description="Error message if failed")


class ActorOrchestrator:
    """
    Actor orchestration system.
    
    Manages the execution of multiple Apify actors, handles dependencies,
    and optimizes for parallel execution.
    """
    
    def __init__(
        self, 
        max_parallel: int = 5,
        max_retries: int = 3,
        default_timeout_seconds: int = 300,
        storage_service = None,
    ):
        """
        Initialize the orchestrator.
        
        Args:
            max_parallel: Maximum number of parallel actor executions.
            max_retries: Default maximum retry attempts for failed actors.
            default_timeout_seconds: Default timeout for actor execution.
            storage_service: Optional storage service. If None, use the singleton.
        """
        self.max_parallel = max_parallel
        self.max_retries = max_retries
        self.default_timeout_seconds = default_timeout_seconds
        self.storage_service = storage_service or get_storage_service()
        self.actor_configurations = get_actor_configurations()
        
        # Initialize semaphore for parallel execution control
        self.semaphore = asyncio.Semaphore(max_parallel)
        
        # Default actor instances cache
        self._actor_instances: Dict[str, BaseActor] = {}
    
    def _get_actor(self, actor_id: str) -> BaseActor:
        """
        Get or create an actor instance.
        
        Args:
            actor_id: ID of the actor.
            
        Returns:
            Actor instance.
            
        Raises:
            ValueError: If actor configuration is not found.
        """
        if actor_id not in self._actor_instances:
            actor_config = self.actor_configurations.get_actor_config(actor_id)
            if not actor_config:
                raise ValueError(f"Actor configuration not found: {actor_id}")
            
            self._actor_instances[actor_id] = BaseActor(actor_id)
        
        return self._actor_instances[actor_id]
    
    def create_plan(
        self, 
        analysis_id: str,
        parameters: AnalysisParameters,
    ) -> ExecutionPlan:
        """
        Create an execution plan for an analysis.
        
        Args:
            analysis_id: ID of the analysis.
            parameters: Analysis parameters.
            
        Returns:
            Execution plan.
            
        Raises:
            ValueError: If analysis is not found.
        """
        # Get the analysis
        analysis = self.storage_service.get_analysis(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis not found: {analysis_id}")
        
        # Create a new execution plan
        plan = ExecutionPlan(
            analysis_id=analysis_id,
            max_budget=Decimal(str(parameters.max_budget)),
        )
        
        # Build the plan based on analysis parameters
        self._build_plan(plan, analysis, parameters)
        
        return plan
    
    def _build_plan(
        self, 
        plan: ExecutionPlan,
        analysis: Analysis,
        parameters: AnalysisParameters,
    ) -> None:
        """
        Build the execution plan by adding necessary actors.
        
        Args:
            plan: Execution plan to build.
            analysis: Analysis object.
            parameters: Analysis parameters.
        """
        # Get the prospect
        prospect = self.storage_service.get_prospect(analysis.prospect_id)
        if not prospect:
            raise ValueError(f"Prospect not found: {analysis.prospect_id}")
        
        # LinkedIn data collection
        if parameters.include_linkedin:
            linkedin_nodes = []
            
            # LinkedIn Profile
            if prospect.linkedin_url:
                profile_node = self._add_actor_to_plan(
                    plan=plan,
                    actor_id="LpVuK3Zozwuipa5bp",  # LinkedIn Profile Bulk Scraper
                    input_data={
                        "profileUrls": [str(prospect.linkedin_url)],
                        "includeSkills": True,
                        "includeEducation": True,
                        "includeExperience": True,
                    },
                    dependencies=[],
                )
                linkedin_nodes.append(profile_node.node_id)
            
            # LinkedIn Posts
            if prospect.linkedin_url:
                posts_node = self._add_actor_to_plan(
                    plan=plan,
                    actor_id="A3cAPGpwBEG8RJwse",  # LinkedIn Posts Bulk Scraper
                    input_data={
                        "profileUrls": [str(prospect.linkedin_url)],
                        "maxPostsPerProfile": 20,
                        "includeComments": False,
                    },
                    dependencies=[],
                )
                linkedin_nodes.append(posts_node.node_id)
            
            # Company data from LinkedIn - dependent on profile to extract company URL
            if prospect.linkedin_url and prospect.company:
                company_node = self._add_actor_to_plan(
                    plan=plan,
                    actor_id="3rgDeYgLhr6XrVnjs",  # LinkedIn Company Profile Scraper
                    input_data={
                        "companyUrls": [],  # Will be populated from profile results
                        "includeJobs": False,
                        "includePeople": True,
                    },
                    dependencies=linkedin_nodes[:1] if linkedin_nodes else [],
                )
        
        # Social media data collection
        if parameters.include_social_media:
            # Facebook data
            if prospect.facebook_page:
                self._add_actor_to_plan(
                    plan=plan,
                    actor_id="KoJrdxJCTtpon81KY",  # Facebook Posts Scraper
                    input_data={
                        "pageUrls": [str(prospect.facebook_page)],
                        "maxPostsPerPage": 20,
                        "includeComments": False,
                    },
                    dependencies=[],
                )
            
            # Twitter/X data
            if prospect.twitter_handle:
                self._add_actor_to_plan(
                    plan=plan,
                    actor_id="61RPP7dywgiy0JPD0",  # Twitter/X Scraper
                    input_data={
                        "usernames": [prospect.twitter_handle],
                        "maxTweetsPerUser": 50,
                        "includeReplies": False,
                        "includeRetweets": False,
                    },
                    dependencies=[],
                )
        
        # Company data collection
        if parameters.include_company_data and prospect.company:
            # Add company data actors based on available identifiers
            if prospect.additional_identifiers.duns_number:
                self._add_actor_to_plan(
                    plan=plan,
                    actor_id="RIq8Fe9BdxSR4GUXY",  # Dun & Bradstreet Scraper
                    input_data={
                        "companyIdentifiers": [prospect.additional_identifiers.duns_number],
                        "includeFinancials": True,
                        "includeRiskScores": True,
                    },
                    dependencies=[],
                )
            
            if prospect.additional_identifiers.crunchbase_url:
                self._add_actor_to_plan(
                    plan=plan,
                    actor_id="BBfgvSNWcySEk1jQO",  # Crunchbase Scraper
                    input_data={
                        "companyNames": [prospect.company],
                        "companyUrls": [str(prospect.additional_identifiers.crunchbase_url)],
                        "includeFundingRounds": True,
                        "includeInvestors": True,
                    },
                    dependencies=[],
                )
            
            # Add ZoomInfo if email is available
            if prospect.email:
                self._add_actor_to_plan(
                    plan=plan,
                    actor_id="C6OyLbP5ixnfc5lYe",  # ZoomInfo Scraper
                    input_data={
                        "contactInfo": [prospect.email],
                        "companyInfo": [prospect.company],
                        "includeTechStack": True,
                    },
                    dependencies=[],
                )
    
    def _add_actor_to_plan(
        self,
        plan: ExecutionPlan,
        actor_id: str,
        input_data: Dict[str, Any],
        dependencies: List[str],
    ) -> ExecutionNode:
        """
        Add an actor to the execution plan.
        
        Args:
            plan: Execution plan to add to.
            actor_id: ID of the actor to add.
            input_data: Input data for the actor.
            dependencies: IDs of nodes this actor depends on.
            
        Returns:
            Created execution node.
            
        Raises:
            ValueError: If actor configuration is not found.
        """
        actor_config = self.actor_configurations.get_actor_config(actor_id)
        if not actor_config:
            raise ValueError(f"Actor configuration not found: {actor_id}")
        
        # Validate input data
        input_data = self.actor_configurations.validate_actor_input(actor_id, input_data)
        
        # Estimate cost
        estimated_cost = self.actor_configurations.estimate_cost(actor_id, input_data)
        
        # Create node
        node = ExecutionNode(
            actor_id=actor_id,
            input_data=input_data,
            dependencies=dependencies.copy(),
            estimated_cost=estimated_cost,
            max_retries=self.max_retries,
            timeout_seconds=actor_config.default_timeout_secs or self.default_timeout_seconds,
            memory_mbytes=actor_config.memory_mbytes,
        )
        
        # Add node to plan
        plan.nodes[node.node_id] = node
        
        # Update reverse dependencies
        for dep_id in dependencies:
            if dep_id not in plan.node_dependencies:
                plan.node_dependencies[dep_id] = []
            plan.node_dependencies[dep_id].append(node.node_id)
        
        # Update total estimated cost
        plan.total_estimated_cost += estimated_cost
        
        return node
    
    def get_ready_nodes(self, plan: ExecutionPlan) -> List[str]:
        """
        Get nodes ready for execution (dependencies satisfied).
        
        Args:
            plan: Execution plan.
            
        Returns:
            List of node IDs ready for execution.
        """
        result = []
        
        for node_id, node in plan.nodes.items():
            if node.status == ExecutionStatus.PENDING:
                # Check if all dependencies are completed
                if all(
                    plan.nodes[dep_id].status == ExecutionStatus.COMPLETED
                    for dep_id in node.dependencies
                ):
                    result.append(node_id)
        
        return result
    
    def has_pending_nodes(self, plan: ExecutionPlan) -> bool:
        """
        Check if the plan has pending nodes.
        
        Args:
            plan: Execution plan.
            
        Returns:
            True if the plan has pending or scheduled nodes.
        """
        for node in plan.nodes.values():
            if node.status in (ExecutionStatus.PENDING, ExecutionStatus.SCHEDULED):
                return True
        
        return False
    
    def prepare_node_input(self, plan: ExecutionPlan, node_id: str) -> Dict[str, Any]:
        """
        Prepare input data for a node, incorporating results from dependencies.
        
        Args:
            plan: Execution plan.
            node_id: ID of the node.
            
        Returns:
            Prepared input data.
        """
        node = plan.nodes[node_id]
        input_data = node.input_data.copy()
        
        # Get the actor configuration
        actor_config = self.actor_configurations.get_actor_config(node.actor_id)
        if not actor_config:
            return input_data
        
        # Special handling for known actors
        if node.actor_id == "3rgDeYgLhr6XrVnjs":  # LinkedIn Company Profile Scraper
            # Try to extract company URL from profile results
            for dep_id in node.dependencies:
                dep_node = plan.nodes[dep_id]
                if dep_node.status == ExecutionStatus.COMPLETED and dep_node.result_id:
                    # Get the result
                    execution = self.storage_service.get_execution(dep_node.result_id)
                    if execution and execution.output_summary:
                        company_url = execution.output_summary.get("company_url")
                        if company_url:
                            input_data["companyUrls"] = [company_url]
                            break
        
        return input_data
    
    async def execute_node(
        self, 
        plan: ExecutionPlan,
        node_id: str,
        analysis_id: str,
    ) -> None:
        """
        Execute a single node.
        
        Args:
            plan: Execution plan.
            node_id: ID of the node to execute.
            analysis_id: ID of the analysis.
        """
        node = plan.nodes[node_id]
        log = logger.bind(node_id=node_id, actor_id=node.actor_id)
        
        # Mark node as running
        node.status = ExecutionStatus.RUNNING
        node.start_time = datetime.now()
        
        # Update analysis
        self.storage_service.update_analysis_status(
            analysis_id=analysis_id,
            status=AnalysisStatus.RUNNING,
        )
        
        try:
            # Get the actor
            actor = self._get_actor(node.actor_id)
            
            # Prepare input data
            input_data = self.prepare_node_input(plan, node_id)
            
            # Create options
            options = ActorRunOptions(
                timeout_secs=node.timeout_seconds,
                memory_mbytes=node.memory_mbytes,
            )
            
            # Execute the actor with semaphore for parallel execution control
            async with self.semaphore:
                log.info("Starting actor execution")
                
                # Actor execution
                result = await actor.run_async(
                    input_data=input_data,
                    options=options,
                    max_budget=float(node.estimated_cost) * 1.5,  # Add 50% buffer
                )
                
                # Handle result
                if isinstance(result, ActorRunResult):
                    # Create execution record
                    execution = ActorExecution(
                        actor_id=node.actor_id,
                        run_id=result.run_id,
                        actor_name=self.actor_configurations.get_actor_config(node.actor_id).name
                            if self.actor_configurations.get_actor_config(node.actor_id) else "Unknown Actor",
                        status=result.status,
                        started_at=result.started_at,
                        completed_at=result.finished_at,
                        duration_secs=result.duration_secs,
                        cost=result.cost,
                        input_summary={
                            key: value if not isinstance(value, list) or len(value) <= 5
                            else f"{len(value)} items"
                            for key, value in input_data.items()
                        },
                        output_summary={
                            "status": result.status,
                            "items_count": result.items_count,
                            "success": result.success,
                        },
                    )
                    
                    # Save execution record
                    saved_execution = self.storage_service.create_execution(execution)
                    
                    # Update node
                    node.status = ExecutionStatus.COMPLETED
                    node.actual_cost = result.cost
                    node.end_time = datetime.now()
                    node.result_id = execution.run_id
                    
                    # Update plan
                    plan.total_actual_cost += result.cost
                    
                    log.info(
                        "Actor execution completed",
                        cost=float(result.cost),
                        item_count=result.items_count,
                    )
                else:
                    # Just for typing - this shouldn't happen with our implementation
                    raise ValueError("Unexpected result type")
        
        except Exception as e:
            log.error(
                "Actor execution failed",
                error=str(e),
                retry_count=node.retries,
            )
            
            # Check if we should retry
            if node.retries < node.max_retries:
                node.retries += 1
                node.status = ExecutionStatus.PENDING
                
                # Add random delay before retry (1-5 seconds)
                retry_delay = 1 + (node.retries * 2)
                log.info(f"Scheduling retry in {retry_delay} seconds")
                await asyncio.sleep(retry_delay)
            else:
                # Mark as failed
                node.status = ExecutionStatus.FAILED
                node.error_message = str(e)
                node.end_time = datetime.now()
    
    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """
        Execute an execution plan.
        
        Args:
            plan: Execution plan to execute.
            
        Returns:
            Updated execution plan with results.
        """
        log = logger.bind(plan_id=plan.plan_id, analysis_id=plan.analysis_id)
        
        # Mark plan as running
        plan.status = ExecutionStatus.RUNNING
        plan.start_time = datetime.now()
        
        try:
            # Execute until no pending nodes
            while self.has_pending_nodes(plan):
                # Get nodes ready for execution
                ready_node_ids = self.get_ready_nodes(plan)
                
                if not ready_node_ids:
                    # No nodes ready but still have pending nodes
                    # This could indicate a circular dependency or all nodes are running
                    running_count = sum(
                        1 for node in plan.nodes.values()
                        if node.status == ExecutionStatus.RUNNING
                    )
                    
                    if running_count > 0:
                        # Wait for running nodes to complete
                        log.debug(
                            f"Waiting for {running_count} running nodes to complete"
                        )
                        await asyncio.sleep(1)
                    else:
                        # No nodes running and none ready - possible circular dependency
                        log.error("Possible circular dependency detected")
                        for node_id, node in plan.nodes.items():
                            if node.status == ExecutionStatus.PENDING:
                                node.status = ExecutionStatus.FAILED
                                node.error_message = "Circular dependency detected"
                        break
                else:
                    # Mark nodes as scheduled
                    for node_id in ready_node_ids:
                        plan.nodes[node_id].status = ExecutionStatus.SCHEDULED
                    
                    # Start execution of ready nodes
                    tasks = [
                        self.execute_node(plan, node_id, plan.analysis_id)
                        for node_id in ready_node_ids
                    ]
                    
                    # Wait for all executions to complete (or fail)
                    await asyncio.gather(*tasks)
                    
                    # Check budget constraint
                    if (
                        plan.max_budget
                        and plan.total_actual_cost > plan.max_budget
                    ):
                        log.warning(
                            "Budget exceeded",
                            actual=float(plan.total_actual_cost),
                            budget=float(plan.max_budget),
                        )
                        
                        # Mark remaining nodes as skipped
                        for node in plan.nodes.values():
                            if node.status in (
                                ExecutionStatus.PENDING, 
                                ExecutionStatus.SCHEDULED
                            ):
                                node.status = ExecutionStatus.SKIPPED
                                node.error_message = "Budget exceeded"
                        
                        # Mark plan as failed
                        plan.status = ExecutionStatus.FAILED
                        plan.error_message = (
                            f"Budget exceeded: {plan.total_actual_cost} "
                            f"> {plan.max_budget}"
                        )
                        break
            
            # Check if all nodes completed successfully
            all_completed = all(
                node.status == ExecutionStatus.COMPLETED
                for node in plan.nodes.values()
            )
            
            if all_completed:
                plan.status = ExecutionStatus.COMPLETED
            elif plan.status != ExecutionStatus.FAILED:
                # Some nodes failed
                plan.status = ExecutionStatus.FAILED
                plan.error_message = "One or more nodes failed"
            
            log.info(
                "Plan execution completed",
                status=plan.status,
                cost=float(plan.total_actual_cost),
                node_count=len(plan.nodes),
            )
        
        except Exception as e:
            log.error("Plan execution failed", error=str(e))
            plan.status = ExecutionStatus.FAILED
            plan.error_message = str(e)
        
        # Record end time
        plan.end_time = datetime.now()
        
        # Update analysis status
        if plan.status == ExecutionStatus.COMPLETED:
            self.storage_service.update_analysis_status(
                analysis_id=plan.analysis_id,
                status=AnalysisStatus.COMPLETED,
            )
        elif plan.status == ExecutionStatus.FAILED:
            self.storage_service.update_analysis_status(
                analysis_id=plan.analysis_id,
                status=AnalysisStatus.FAILED,
                error=plan.error_message,
            )
        
        return plan 