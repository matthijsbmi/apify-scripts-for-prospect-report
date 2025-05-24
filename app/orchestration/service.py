"""
Orchestration service for prospect analysis.

This module provides the high-level service for orchestrating prospect analysis
using Apify actors, managing the full flow from input to output.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Union

import structlog

from app.actors.config import get_actor_configurations
from app.models.data import (
    Prospect, Analysis, AnalysisStatus, AnalysisParameters, 
    ProspectAnalysisResponse
)
from app.services.storage import get_storage_service
from app.orchestration.orchestrator import ActorOrchestrator, ExecutionPlan
from app.orchestration.processor import AnalysisProcessor


logger = structlog.get_logger(__name__)


class OrchestrationService:
    """
    Service for orchestrating prospect analysis.
    
    Ties together the actor orchestrator and result processor to provide
    a complete workflow for analysis.
    """
    
    def __init__(
        self, 
        storage_service = None,
        max_parallel: int = 5,
        max_retries: int = 3,
    ):
        """
        Initialize the orchestration service.
        
        Args:
            storage_service: Optional storage service. If None, use the singleton.
            max_parallel: Maximum number of parallel actor executions.
            max_retries: Default maximum retry attempts for failed actors.
        """
        self.storage_service = storage_service or get_storage_service()
        self.actor_configurations = get_actor_configurations()
        
        # Initialize orchestrator and processor
        self.orchestrator = ActorOrchestrator(
            max_parallel=max_parallel,
            max_retries=max_retries,
            storage_service=self.storage_service,
        )
        
        self.processor = AnalysisProcessor(
            storage_service=self.storage_service,
        )
    
    async def analyze_prospect(
        self,
        prospect_id: str,
        parameters: Optional[AnalysisParameters] = None,
    ) -> Analysis:
        """
        Analyze a prospect by executing and processing actor runs.
        
        Args:
            prospect_id: ID of the prospect to analyze.
            parameters: Analysis parameters. If None, use defaults.
            
        Returns:
            Created analysis object.
            
        Raises:
            ValueError: If prospect is not found.
        """
        log = logger.bind(prospect_id=prospect_id)
        
        # Get the prospect
        prospect = self.storage_service.get_prospect(prospect_id)
        if not prospect:
            raise ValueError(f"Prospect not found: {prospect_id}")
        
        # Use default parameters if not provided
        if not parameters:
            parameters = AnalysisParameters(
                include_linkedin=True,
                include_social_media=True,
                include_company_data=True,
                max_budget=100.0,
                priority="quality",
            )
        
        # Create analysis record
        analysis = Analysis(
            id=str(uuid.uuid4()),
            prospect_id=prospect_id,
            parameters=parameters,
            status=AnalysisStatus.PENDING,
            created_at=datetime.now(),
        )
        
        # Save analysis to storage
        analysis = self.storage_service.create_analysis(analysis)
        
        log = log.bind(analysis_id=analysis.id)
        log.info("Starting prospect analysis")
        
        # Create execution plan
        plan = self.orchestrator.create_plan(
            analysis_id=analysis.id,
            parameters=parameters,
        )
        
        log.info(
            "Created execution plan",
            plan_id=plan.plan_id,
            node_count=len(plan.nodes),
            estimated_cost=float(plan.total_estimated_cost),
        )
        
        # Execute plan
        executed_plan = await self.orchestrator.execute_plan(plan)
        
        # Process results
        if executed_plan.status.value in ("completed", "failed"):
            # Even if the plan failed, we might still have some data to process
            try:
                response = await self.processor.process_analysis(
                    analysis_id=analysis.id,
                    plan=executed_plan,
                )
                
                log.info(
                    "Prospect analysis completed",
                    status=executed_plan.status.value,
                    cost=float(executed_plan.total_actual_cost),
                )
            
            except Exception as e:
                log.error("Error processing analysis results", error=str(e))
                
                # Update analysis status
                self.storage_service.update_analysis_status(
                    analysis_id=analysis.id,
                    status=AnalysisStatus.FAILED,
                    error=f"Error processing results: {e}",
                )
        
        # Return updated analysis
        return self.storage_service.get_analysis(analysis.id)
    
    async def get_analysis_result(
        self, 
        analysis_id: str,
    ) -> Optional[ProspectAnalysisResponse]:
        """
        Get analysis result by ID.
        
        Args:
            analysis_id: ID of the analysis.
            
        Returns:
            Analysis result if found, None otherwise.
        """
        return self.storage_service.get_analysis_result(analysis_id)
    
    def get_analysis(self, analysis_id: str) -> Optional[Analysis]:
        """
        Get analysis by ID.
        
        Args:
            analysis_id: ID of the analysis.
            
        Returns:
            Analysis if found, None otherwise.
        """
        return self.storage_service.get_analysis(analysis_id)
    
    def list_analyses_for_prospect(
        self, 
        prospect_id: str,
    ) -> List[Analysis]:
        """
        List all analyses for a prospect.
        
        Args:
            prospect_id: ID of the prospect.
            
        Returns:
            List of analyses for the prospect.
        """
        return self.storage_service.filter_analyses({"prospect_id": prospect_id})
    
    def cancel_analysis(self, analysis_id: str) -> bool:
        """
        Cancel a running analysis.
        
        Args:
            analysis_id: ID of the analysis to cancel.
            
        Returns:
            True if successfully cancelled, False otherwise.
        """
        analysis = self.storage_service.get_analysis(analysis_id)
        if not analysis:
            return False
        
        if analysis.status == AnalysisStatus.RUNNING:
            # Currently we don't have a way to cancel running actors,
            # so we just mark the analysis as cancelled
            self.storage_service.update_analysis_status(
                analysis_id=analysis_id,
                status=AnalysisStatus.FAILED,
                error="Analysis cancelled by user",
            )
            return True
        
        return False
    
    def estimate_cost(
        self, 
        prospect_id: str,
        parameters: AnalysisParameters,
    ) -> Decimal:
        """
        Estimate the cost of analyzing a prospect.
        
        Args:
            prospect_id: ID of the prospect to analyze.
            parameters: Analysis parameters.
            
        Returns:
            Estimated cost.
            
        Raises:
            ValueError: If prospect is not found.
        """
        # Get the prospect
        prospect = self.storage_service.get_prospect(prospect_id)
        if not prospect:
            raise ValueError(f"Prospect not found: {prospect_id}")
        
        # Use a temporary analysis ID
        temp_analysis_id = "temp-" + str(uuid.uuid4())
        
        # Create a temporary analysis object
        temp_analysis = Analysis(
            id=temp_analysis_id,
            prospect_id=prospect_id,
            parameters=parameters,
            status=AnalysisStatus.PENDING,
            created_at=datetime.now(),
        )
        
        # Create execution plan without saving to storage
        plan = self.orchestrator._build_plan(
            plan=ExecutionPlan(analysis_id=temp_analysis_id),
            analysis=temp_analysis, 
            parameters=parameters,
        )
        
        return plan.total_estimated_cost 