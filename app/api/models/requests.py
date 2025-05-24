"""
API Request Models.

Pydantic models for validating incoming API requests.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class PriorityLevel(str, Enum):
    """Priority levels for analysis."""
    LOW = "low"
    MEDIUM = "medium"  
    HIGH = "high"


class DataFreshness(str, Enum):
    """Data freshness preferences."""
    LATEST = "latest"
    CACHED_OK = "cached_ok"
    FORCE_REFRESH = "force_refresh"


class DetailLevel(str, Enum):
    """Analysis detail levels."""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class ProspectInput(BaseModel):
    """Input model for prospect data."""
    name: Optional[str] = Field(None, description="Prospect's full name")
    company: Optional[str] = Field(None, description="Company name")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    profile_url: Optional[str] = Field(None, description="Alternative LinkedIn profile URL")
    company_website: Optional[str] = Field(None, description="Company website URL")
    company_domain: Optional[str] = Field(None, description="Company domain")
    twitter_handle: Optional[str] = Field(None, description="Twitter handle")
    facebook_page: Optional[str] = Field(None, description="Facebook page URL")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    title: Optional[str] = Field(None, description="Job title")
    location: Optional[str] = Field(None, description="Location")
    additional_identifiers: Dict[str, str] = Field(
        default_factory=dict, 
        description="Additional identifiers"
    )
    
    @validator('linkedin_url', 'profile_url')
    def validate_linkedin_url(cls, v):
        """Validate LinkedIn URL format."""
        if v and not any(domain in v.lower() for domain in ['linkedin.com', 'www.linkedin.com']):
            raise ValueError('Must be a valid LinkedIn URL')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        """Basic email validation."""
        if v and '@' not in v:
            raise ValueError('Must be a valid email address')
        return v
    
    @validator('twitter_handle')
    def validate_twitter_handle(cls, v):
        """Validate Twitter handle format."""
        if v and not v.startswith('@'):
            return f"@{v}"
        return v


class AnalysisParameters(BaseModel):
    """Parameters for prospect analysis configuration."""
    include_linkedin: bool = Field(True, description="Include LinkedIn data collection")
    include_social_media: bool = Field(True, description="Include social media data collection")
    include_company_data: bool = Field(True, description="Include company financial data")
    max_budget: Optional[float] = Field(None, description="Maximum budget for analysis in USD", gt=0)
    priority: PriorityLevel = Field(PriorityLevel.MEDIUM, description="Analysis priority level")
    data_freshness: DataFreshness = Field(DataFreshness.LATEST, description="Data freshness preference")
    detail_level: DetailLevel = Field(DetailLevel.STANDARD, description="Analysis detail level")
    timeout: Optional[int] = Field(None, description="Timeout in seconds", gt=0, le=3600)
    use_cache: bool = Field(True, description="Use cached results if available")
    cache_results: bool = Field(True, description="Cache analysis results")
    custom_actor_configs: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Custom actor configurations"
    )


class AnalysisRequest(BaseModel):
    """Request model for single prospect analysis."""
    prospect: ProspectInput = Field(..., description="Prospect data to analyze")
    parameters: AnalysisParameters = Field(
        default_factory=AnalysisParameters,
        description="Analysis parameters"
    )


class BatchProspectItem(BaseModel):
    """Individual prospect item for batch analysis."""
    data: ProspectInput = Field(..., description="Prospect data")
    params: Optional[AnalysisParameters] = Field(
        None, 
        description="Prospect-specific parameters (overrides global)"
    )


class BatchAnalysisRequest(BaseModel):
    """Request model for batch prospect analysis."""
    prospects: List[BatchProspectItem] = Field(
        ..., 
        description="List of prospects to analyze",
        min_items=1,
        max_items=100
    )
    global_parameters: AnalysisParameters = Field(
        default_factory=AnalysisParameters,
        description="Global analysis parameters"
    )


class CostEstimateRequest(BaseModel):
    """Request model for cost estimation."""
    prospect: ProspectInput = Field(..., description="Prospect data for estimation")
    parameters: AnalysisParameters = Field(
        default_factory=AnalysisParameters,
        description="Analysis parameters for estimation"
    )


class HealthCheckRequest(BaseModel):
    """Request model for detailed health check."""
    include_services: bool = Field(False, description="Include service health details")
    include_actors: bool = Field(False, description="Include actor status")
    include_metrics: bool = Field(False, description="Include system metrics") 