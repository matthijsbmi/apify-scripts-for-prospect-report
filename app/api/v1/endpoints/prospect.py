"""
Prospect Analysis API endpoints.

Core endpoints for prospect analysis functionality.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import ValidationError

import structlog

from app.api.models.requests import (
    AnalysisRequest, BatchAnalysisRequest, CostEstimateRequest
)
from app.api.models.responses import (
    AnalysisResponse, BatchAnalysisResponse, CostEstimateResponse,
    ErrorResponse
)
from app.services.prospect_analysis import ProspectAnalysisService
from app.core.apify_client import ApifyService
from app.cost.manager import CostManager


logger = structlog.get_logger(__name__)
router = APIRouter()

# Global service instances (would normally be injected via dependency injection)
_prospect_service: Optional[ProspectAnalysisService] = None


def get_prospect_service() -> ProspectAnalysisService:
    """Get or create prospect analysis service instance."""
    global _prospect_service
    if _prospect_service is None:
        # In production, these would be properly injected
        apify_service = ApifyService()
        _prospect_service = ProspectAnalysisService(apify_service)
    return _prospect_service


@router.post("/analyze", response_model=AnalysisResponse, tags=["Prospect Analysis"])
async def analyze_prospect(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    service: ProspectAnalysisService = Depends(get_prospect_service)
) -> AnalysisResponse:
    """
    Analyze a single prospect using all available data sources.
    
    This endpoint performs comprehensive prospect analysis including:
    - LinkedIn profile and posts data
    - Social media presence (Facebook, Twitter)
    - Company financial and business data
    - Data validation and quality scoring
    - Cost optimization and reporting
    
    **Returns:** Complete analysis report with data, insights, and metadata.
    """
    request_id = str(uuid.uuid4())
    log = logger.bind(request_id=request_id)
    
    log.info(
        "Starting prospect analysis",
        prospect_name=request.prospect.name,
        company=request.prospect.company,
        linkedin_url=request.prospect.linkedin_url
    )
    
    start_time = time.time()
    
    try:
        # Convert request models to dict format expected by service
        prospect_data = request.prospect.dict(exclude_none=True)
        analysis_params = request.parameters.dict(exclude_none=True)
        
        # Perform analysis
        result = await service.analyze_prospect(prospect_data, analysis_params)
        
        # Convert service response to API response model
        api_response = _convert_service_response_to_api(result)
        
        execution_time = time.time() - start_time
        log.info(
            "Prospect analysis completed",
            prospect_id=api_response.prospect_id,
            execution_time=execution_time,
            data_sources=len(api_response.results),
            total_cost=api_response.cost_breakdown.total_cost
        )
        
        return api_response
        
    except ValidationError as e:
        log.error("Request validation failed", error=str(e))
        raise HTTPException(
            status_code=422,
            detail=f"Request validation failed: {str(e)}"
        )
    except ValueError as e:
        log.error("Invalid input data", error=str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input data: {str(e)}"
        )
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "Prospect analysis failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/batch", response_model=BatchAnalysisResponse, tags=["Prospect Analysis"])
async def batch_analyze(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    service: ProspectAnalysisService = Depends(get_prospect_service)
) -> BatchAnalysisResponse:
    """
    Analyze multiple prospects in batch mode.
    
    Efficiently processes multiple prospects with shared parameters,
    providing individual results and aggregate statistics.
    
    **Limits:**
    - Maximum 100 prospects per batch
    - Recommended batch size: 10-50 prospects
    
    **Returns:** Batch analysis results with individual reports and statistics.
    """
    batch_id = str(uuid.uuid4())
    log = logger.bind(batch_id=batch_id, prospect_count=len(request.prospects))
    
    log.info("Starting batch prospect analysis")
    
    start_time = time.time()
    
    try:
        # Convert request to format expected by service
        prospects = []
        for item in request.prospects:
            prospect_entry = {
                "data": item.data.dict(exclude_none=True),
                "params": item.params.dict(exclude_none=True) if item.params else None
            }
            prospects.append(prospect_entry)
        
        global_params = request.global_parameters.dict(exclude_none=True)
        
        # Perform batch analysis
        result = await service.analyze_batch(prospects, global_params)
        
        # Convert service response to API response model
        api_response = _convert_batch_response_to_api(result)
        
        execution_time = time.time() - start_time
        log.info(
            "Batch analysis completed",
            execution_time=execution_time,
            successful=api_response.statistics.successful_analyses,
            failed=api_response.statistics.failed_analyses,
            total_cost=api_response.total_cost
        )
        
        return api_response
        
    except ValidationError as e:
        log.error("Batch request validation failed", error=str(e))
        raise HTTPException(
            status_code=422,
            detail=f"Batch request validation failed: {str(e)}"
        )
    except ValueError as e:
        log.error("Invalid batch data", error=str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Invalid batch data: {str(e)}"
        )
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "Batch analysis failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )


@router.get("/{prospect_id}", response_model=AnalysisResponse, tags=["Prospect Analysis"])
async def get_analysis(
    prospect_id: str,
    service: ProspectAnalysisService = Depends(get_prospect_service)
) -> AnalysisResponse:
    """
    Retrieve a previously completed prospect analysis by ID.
    
    **Returns:** Complete analysis report if found, 404 if not found.
    """
    log = logger.bind(prospect_id=prospect_id)
    log.info("Retrieving prospect analysis")
    
    try:
        # Retrieve from storage
        result = await service.storage.get_analysis_result(prospect_id)
        
        if not result:
            log.warning("Analysis not found")
            raise HTTPException(
                status_code=404,
                detail=f"Analysis for prospect {prospect_id} not found"
            )
        
        # Convert to API response format
        api_response = _convert_service_response_to_api(result)
        
        log.info("Analysis retrieved successfully")
        return api_response
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("Failed to retrieve analysis", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analysis: {str(e)}"
        )


@router.post("/estimate-cost", response_model=CostEstimateResponse, tags=["Cost Management"])
async def estimate_cost(
    request: CostEstimateRequest,
    service: ProspectAnalysisService = Depends(get_prospect_service)
) -> CostEstimateResponse:
    """
    Estimate the cost of analyzing a prospect without executing the analysis.
    
    Provides detailed cost breakdown and optimization recommendations.
    
    **Returns:** Comprehensive cost estimate with breakdown and recommendations.
    """
    log = logger.bind()
    log.info("Estimating analysis cost")
    
    try:
        # Convert request to service format
        prospect_data = request.prospect.dict(exclude_none=True)
        analysis_params = request.parameters.dict(exclude_none=True)
        
        # Build execution plan to estimate costs
        execution_plan = service._build_execution_plan(prospect_data, analysis_params)
        
        # Calculate detailed cost estimate
        cost_estimate = _calculate_detailed_cost_estimate(execution_plan, analysis_params)
        
        # Generate cost optimization recommendations
        recommendations = _generate_cost_recommendations(cost_estimate, analysis_params)
        
        # Create response
        response = CostEstimateResponse(
            prospect_summary=_generate_prospect_summary(prospect_data),
            parameters_summary=_generate_parameters_summary(analysis_params),
            cost_estimate=cost_estimate,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat()
        )
        
        log.info(
            "Cost estimate generated",
            estimated_cost=cost_estimate.estimated_total_cost,
            actors_count=len(cost_estimate.actor_breakdown)
        )
        
        return response
        
    except Exception as e:
        log.error("Cost estimation failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Cost estimation failed: {str(e)}"
        )


def _convert_service_response_to_api(service_result: Dict[str, Any]) -> AnalysisResponse:
    """Convert service response to API response model."""
    # This is a simplified conversion - in practice, you'd need more robust mapping
    from app.api.models.responses import (
        AnalysisResponse, AnalysisSummary, CostBreakdown, 
        ExecutionMetadata, DataSourceResult, DataSourceStatus
    )
    
    # Convert results to API format
    api_results = {}
    for source, result in service_result.get("results", {}).items():
        if "error" in result:
            api_results[source] = DataSourceResult(
                source=source,
                status=DataSourceStatus.FAILED,
                error=result["error"]
            )
        else:
            api_results[source] = DataSourceResult(
                source=source,
                status=DataSourceStatus.SUCCESS,
                data=result.get("data"),
                validation=result.get("validation")
            )
    
    return AnalysisResponse(
        prospect_id=service_result["prospect_id"],
        status=service_result["status"],
        prospect_data=service_result["prospect_data"],
        analysis_params=service_result["analysis_params"],
        results=api_results,
        summary=AnalysisSummary(**service_result["summary"]),
        cost_breakdown=CostBreakdown(**service_result["cost_breakdown"]),
        execution_metadata=ExecutionMetadata(**service_result["execution_metadata"])
    )


def _convert_batch_response_to_api(service_result: Dict[str, Any]) -> BatchAnalysisResponse:
    """Convert batch service response to API response model."""
    from app.api.models.responses import (
        BatchAnalysisResponse, BatchStatistics, BatchAnalysisResult
    )
    
    # Convert individual results
    api_results = []
    for result in service_result.get("results", []):
        if result["status"] == "completed":
            api_result = BatchAnalysisResult(
                index=result["index"],
                prospect_id=result["prospect_id"],
                status=result["status"],
                result=_convert_service_response_to_api(result["result"])
            )
        else:
            api_result = BatchAnalysisResult(
                index=result["index"],
                prospect_id=result["prospect_id"],
                status=result["status"],
                error=result.get("error"),
                prospect_data=result.get("prospect_data")
            )
        api_results.append(api_result)
    
    return BatchAnalysisResponse(
        batch_id=service_result["batch_id"],
        status=service_result["status"],
        execution_time=service_result["execution_time"],
        statistics=BatchStatistics(**service_result["statistics"]),
        total_cost=service_result["total_cost"],
        results=api_results,
        generated_at=service_result["generated_at"]
    )


def _calculate_detailed_cost_estimate(execution_plan: Dict[str, Any], params: Dict[str, Any]):
    """Calculate detailed cost estimate from execution plan."""
    from app.api.models.responses import CostEstimate
    
    # Base cost per actor (simplified)
    actor_costs = {
        "linkedin_profile": 0.05,
        "linkedin_posts": 0.03,
        "linkedin_company": 0.04,
        "facebook_pages": 0.06,
        "twitter_scraper": 0.04,
        "crunchbase": 0.08,
        "duns": 0.10,
        "zoominfo": 0.12
    }
    
    actor_breakdown = {}
    total_cost = 0.0
    
    for actor in execution_plan.get("actors", []):
        cost = actor_costs.get(actor, 0.05)
        actor_breakdown[actor] = cost
        total_cost += cost
    
    # Apply detail level multiplier
    detail_level = params.get("detail_level", "standard")
    if detail_level == "comprehensive":
        total_cost *= 1.5
    elif detail_level == "basic":
        total_cost *= 0.7
    
    return CostEstimate(
        estimated_total_cost=round(total_cost, 4),
        actor_breakdown=actor_breakdown,
        factors_considered=[
            "Number of actors required",
            "Analysis detail level",
            "Data source complexity"
        ],
        confidence_level="high" if len(actor_breakdown) <= 3 else "medium",
        estimated_execution_time=len(execution_plan.get("actors", [])) * 45
    )


def _generate_cost_recommendations(estimate, params: Dict[str, Any]) -> List[str]:
    """Generate cost optimization recommendations."""
    recommendations = []
    
    if estimate.estimated_total_cost > 0.50:
        recommendations.append("Consider using 'basic' detail level to reduce costs")
    
    if len(estimate.actor_breakdown) > 5:
        recommendations.append("Disable unnecessary data sources to optimize costs")
    
    if not params.get("use_cache", True):
        recommendations.append("Enable caching to reduce costs for repeated analyses")
    
    if not recommendations:
        recommendations.append("Cost is already optimized for your requirements")
    
    return recommendations


def _generate_prospect_summary(prospect_data: Dict[str, Any]) -> str:
    """Generate a human-readable prospect summary."""
    parts = []
    
    if prospect_data.get("name"):
        parts.append(f"Name: {prospect_data['name']}")
    
    if prospect_data.get("company"):
        parts.append(f"Company: {prospect_data['company']}")
    
    if prospect_data.get("title"):
        parts.append(f"Title: {prospect_data['title']}")
    
    if prospect_data.get("linkedin_url"):
        parts.append("LinkedIn profile available")
    
    return " | ".join(parts) if parts else "Prospect with basic identifiers"


def _generate_parameters_summary(params: Dict[str, Any]) -> str:
    """Generate a human-readable parameters summary."""
    parts = []
    
    detail_level = params.get("detail_level", "standard")
    parts.append(f"Detail level: {detail_level}")
    
    sources = []
    if params.get("include_linkedin", True):
        sources.append("LinkedIn")
    if params.get("include_social_media", True):
        sources.append("Social Media")
    if params.get("include_company_data", True):
        sources.append("Company Data")
    
    if sources:
        parts.append(f"Sources: {', '.join(sources)}")
    
    if params.get("max_budget"):
        parts.append(f"Budget limit: ${params['max_budget']}")
    
    return " | ".join(parts) 