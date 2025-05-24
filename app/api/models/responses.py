"""
API Response Models.

Pydantic models for API response serialization.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    """Analysis execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class DataSourceStatus(str, Enum):
    """Data source collection status."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class ExecutionMetadata(BaseModel):
    """Metadata about analysis execution."""
    execution_time: float = Field(..., description="Total execution time in seconds")
    generated_at: str = Field(..., description="Timestamp when analysis was generated")
    data_sources_used: List[str] = Field(..., description="List of data sources used")
    validation_enabled: bool = Field(..., description="Whether validation was enabled")


class CostBreakdown(BaseModel):
    """Cost breakdown for analysis."""
    total_cost: float = Field(..., description="Total cost in USD")
    actor_costs: Dict[str, float] = Field(..., description="Cost per actor")
    estimated_cost: Optional[float] = Field(None, description="Originally estimated cost")
    cost_savings: Optional[float] = Field(None, description="Savings from cache/optimization")


class DataSourceResult(BaseModel):
    """Result from a single data source."""
    source: str = Field(..., description="Data source name")
    status: DataSourceStatus = Field(..., description="Collection status")
    data: Optional[Dict[str, Any]] = Field(None, description="Collected data")
    validation: Optional[Dict[str, Any]] = Field(None, description="Validation results")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_error: Optional[str] = Field(None, description="Processing error if any")
    execution_time: Optional[float] = Field(None, description="Execution time for this source")


class AnalysisSummary(BaseModel):
    """High-level analysis summary."""
    data_sources_found: List[str] = Field(..., description="Successfully collected data sources")
    data_completeness: Dict[str, Any] = Field(..., description="Data completeness metrics")
    key_insights: List[str] = Field(..., description="Key insights from analysis")
    data_quality_overview: Dict[str, Any] = Field(..., description="Overall data quality")
    recommendations: List[str] = Field(..., description="Recommendations for improvement")


class AnalysisResponse(BaseModel):
    """Response model for single prospect analysis."""
    prospect_id: str = Field(..., description="Unique prospect identifier")
    status: AnalysisStatus = Field(..., description="Analysis status")
    prospect_data: Dict[str, Any] = Field(..., description="Original prospect input data")
    analysis_params: Dict[str, Any] = Field(..., description="Analysis parameters used")
    results: Dict[str, DataSourceResult] = Field(..., description="Results from each data source")
    summary: AnalysisSummary = Field(..., description="Analysis summary and insights")
    cost_breakdown: CostBreakdown = Field(..., description="Cost breakdown")
    execution_metadata: ExecutionMetadata = Field(..., description="Execution metadata")
    error: Optional[str] = Field(None, description="Error message if analysis failed")


class BatchStatistics(BaseModel):
    """Statistics for batch analysis."""
    total_prospects: int = Field(..., description="Total number of prospects")
    successful_analyses: int = Field(..., description="Number of successful analyses")
    failed_analyses: int = Field(..., description="Number of failed analyses")
    success_rate: float = Field(..., description="Success rate as percentage")


class BatchAnalysisResult(BaseModel):
    """Individual result in batch analysis."""
    index: int = Field(..., description="Prospect index in batch")
    prospect_id: str = Field(..., description="Unique prospect identifier")
    status: AnalysisStatus = Field(..., description="Analysis status")
    result: Optional[AnalysisResponse] = Field(None, description="Analysis result if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    prospect_data: Optional[Dict[str, Any]] = Field(None, description="Original prospect data")


class BatchAnalysisResponse(BaseModel):
    """Response model for batch prospect analysis."""
    batch_id: str = Field(..., description="Unique batch identifier")
    status: AnalysisStatus = Field(..., description="Overall batch status")
    execution_time: float = Field(..., description="Total batch execution time")
    statistics: BatchStatistics = Field(..., description="Batch statistics")
    total_cost: float = Field(..., description="Total cost for all analyses")
    results: List[BatchAnalysisResult] = Field(..., description="Individual analysis results")
    generated_at: str = Field(..., description="Timestamp when batch was completed")


class ActorConfiguration(BaseModel):
    """Actor configuration details."""
    actor_id: str = Field(..., description="Apify actor ID")
    name: str = Field(..., description="Actor display name")
    description: str = Field(..., description="Actor description")
    category: str = Field(..., description="Actor category")
    cost_per_run: float = Field(..., description="Estimated cost per run")
    average_runtime: Optional[float] = Field(None, description="Average runtime in seconds")
    input_schema: Dict[str, Any] = Field(..., description="Input schema definition")
    output_format: str = Field(..., description="Output data format")
    is_enabled: bool = Field(..., description="Whether actor is enabled")


class ActorsResponse(BaseModel):
    """Response model for actors listing."""
    actors: List[ActorConfiguration] = Field(..., description="Available actors")
    total_count: int = Field(..., description="Total number of actors")
    categories: List[str] = Field(..., description="Available actor categories")
    total_estimated_cost: float = Field(..., description="Total estimated cost if all actors used")


class CostEstimate(BaseModel):
    """Cost estimation details."""
    estimated_total_cost: float = Field(..., description="Estimated total cost")
    actor_breakdown: Dict[str, float] = Field(..., description="Cost breakdown by actor")
    factors_considered: List[str] = Field(..., description="Factors considered in estimation")
    confidence_level: str = Field(..., description="Confidence level of estimate")
    estimated_execution_time: float = Field(..., description="Estimated execution time in seconds")


class CostEstimateResponse(BaseModel):
    """Response model for cost estimation."""
    prospect_summary: str = Field(..., description="Summary of prospect data")
    parameters_summary: str = Field(..., description="Summary of analysis parameters")
    cost_estimate: CostEstimate = Field(..., description="Detailed cost estimate")
    recommendations: List[str] = Field(..., description="Cost optimization recommendations")
    generated_at: str = Field(..., description="Timestamp when estimate was generated")


class ServiceHealth(BaseModel):
    """Individual service health status."""
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    response_time: Optional[float] = Field(None, description="Response time in milliseconds")
    last_check: str = Field(..., description="Last health check timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


class SystemMetrics(BaseModel):
    """System performance metrics."""
    memory_usage: Dict[str, float] = Field(..., description="Memory usage statistics")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    active_analyses: int = Field(..., description="Number of active analyses")
    total_analyses_today: int = Field(..., description="Total analyses completed today")
    average_analysis_time: float = Field(..., description="Average analysis time in seconds")


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Overall system status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Health check timestamp")
    uptime: float = Field(..., description="System uptime in seconds")
    services: Optional[List[ServiceHealth]] = Field(None, description="Individual service health")
    actors: Optional[List[Dict[str, Any]]] = Field(None, description="Actor status information")
    metrics: Optional[SystemMetrics] = Field(None, description="System performance metrics")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking") 