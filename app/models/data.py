"""
Data models for the application.

Defines the core data structures used throughout the application.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class AnalysisPriority(str, Enum):
    """Priority levels for prospect analysis."""
    
    SPEED = "speed"
    COST = "cost"
    QUALITY = "quality"


class DataFreshness(str, Enum):
    """Data freshness options."""
    
    LATEST = "latest"
    CACHED_OK = "cached_ok"


class AnalysisStatus(str, Enum):
    """Status options for an analysis."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AdditionalIdentifiers(BaseModel):
    """Additional identifiers for a prospect."""
    
    crunchbase_url: Optional[HttpUrl] = Field(default=None, description="URL to the Crunchbase profile.")
    zoominfo_id: Optional[str] = Field(default=None, description="ZoomInfo identifier.")
    duns_number: Optional[str] = Field(default=None, description="Dun & Bradstreet D-U-N-S number.")
    company_domain: Optional[str] = Field(default=None, description="Company website domain.")


class Prospect(BaseModel):
    """Prospect information for analysis."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the prospect.")
    name: str = Field(..., description="Name of the prospect.")
    company: str = Field(..., description="Company where the prospect works.")
    linkedin_url: Optional[HttpUrl] = Field(default=None, description="LinkedIn profile URL.")
    company_website: Optional[HttpUrl] = Field(default=None, description="Company website URL.")
    twitter_handle: Optional[str] = Field(default=None, description="Twitter/X handle.")
    facebook_page: Optional[HttpUrl] = Field(default=None, description="Facebook page URL.")
    email: Optional[str] = Field(default=None, description="Email address.")
    additional_identifiers: AdditionalIdentifiers = Field(default_factory=AdditionalIdentifiers, 
                                                     description="Additional identifiers.")
    created_at: datetime = Field(default_factory=datetime.now, description="When this prospect was created.")
    updated_at: datetime = Field(default_factory=datetime.now, description="When this prospect was last updated.")
    
    @model_validator(mode="before")
    @classmethod
    def validate_at_least_one_identifier(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that at least one identifier is provided."""
        if isinstance(data, dict):
            identifiers = [
                data.get("linkedin_url"),
                data.get("company_website"),
                data.get("twitter_handle"),
                data.get("facebook_page"),
                data.get("email")
            ]
            
            # Check additional identifiers
            additional = data.get("additional_identifiers", {})
            if isinstance(additional, dict):
                identifiers.extend([
                    additional.get("crunchbase_url"),
                    additional.get("zoominfo_id"),
                    additional.get("duns_number"),
                    additional.get("company_domain")
                ])
            
            if not any(identifiers):
                raise ValueError("At least one identifier (URL, handle, email, etc.) must be provided.")
        
        return data


class AnalysisParameters(BaseModel):
    """Parameters for prospect analysis."""
    
    include_linkedin: bool = Field(default=True, description="Whether to include LinkedIn data.")
    include_social_media: bool = Field(default=True, description="Whether to include social media data.")
    include_company_data: bool = Field(default=True, description="Whether to include company data.")
    max_budget: float = Field(default=50.0, description="Maximum budget for analysis in USD.")
    priority: AnalysisPriority = Field(default=AnalysisPriority.QUALITY, 
                                    description="Priority for the analysis.")
    data_freshness: DataFreshness = Field(default=DataFreshness.LATEST,
                                       description="Data freshness requirement.")
    custom_actor_configs: Dict[str, Any] = Field(default_factory=dict,
                                            description="Custom actor configurations.")


class ProspectAnalysisRequest(BaseModel):
    """Request model for prospect analysis."""
    
    prospect: Prospect
    parameters: AnalysisParameters = Field(default_factory=AnalysisParameters)


class BatchAnalysisRequest(BaseModel):
    """Request model for batch prospect analysis."""
    
    prospects: List[Prospect]
    parameters: AnalysisParameters = Field(default_factory=AnalysisParameters)


class CostEstimateRequest(BaseModel):
    """Request model for cost estimation."""
    
    prospect: Prospect
    parameters: AnalysisParameters = Field(default_factory=AnalysisParameters)


class ActorCostEstimate(BaseModel):
    """Cost estimate for a single actor."""
    
    actor_id: str = Field(..., description="ID of the actor.")
    actor_name: str = Field(..., description="Name of the actor.")
    estimated_cost: Decimal = Field(..., description="Estimated cost in USD.")
    cost_factors: Dict[str, Any] = Field(default_factory=dict, 
                                    description="Factors affecting the cost estimate.")


class CostEstimateResponse(BaseModel):
    """Response model for cost estimation."""
    
    total_estimated_cost: Decimal = Field(..., description="Total estimated cost in USD.")
    actor_costs: List[ActorCostEstimate] = Field(..., description="Cost breakdown by actor.")
    max_budget: float = Field(..., description="Maximum budget from the request.")
    within_budget: bool = Field(..., description="Whether the estimate is within budget.")


class LinkedInProfile(BaseModel):
    """LinkedIn profile data."""
    
    profile_url: HttpUrl = Field(..., description="LinkedIn profile URL.")
    full_name: Optional[str] = Field(default=None, description="Full name of the person.")
    headline: Optional[str] = Field(default=None, description="Profile headline.")
    location: Optional[str] = Field(default=None, description="Location as shown on profile.")
    summary: Optional[str] = Field(default=None, description="Profile summary.")
    experience: List[Dict[str, Any]] = Field(default_factory=list, description="Work experience.")
    education: List[Dict[str, Any]] = Field(default_factory=list, description="Education history.")
    skills: List[str] = Field(default_factory=list, description="Skills listed on profile.")
    recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Recommendations.")
    connections_count: Optional[int] = Field(default=None, 
                                         description="Number of connections (if available).")
    extracted_at: datetime = Field(default_factory=datetime.now, 
                               description="When the data was extracted.")


class LinkedInPost(BaseModel):
    """LinkedIn post data."""
    
    post_url: HttpUrl = Field(..., description="LinkedIn post URL.")
    author_name: Optional[str] = Field(default=None, description="Name of the post author.")
    author_url: Optional[HttpUrl] = Field(default=None, 
                                      description="URL to the author's profile.")
    content: Optional[str] = Field(default=None, description="Post content.")
    published_at: Optional[datetime] = Field(default=None, 
                                         description="When the post was published.")
    reactions_count: Optional[int] = Field(default=None, 
                                       description="Number of reactions to the post.")
    comments_count: Optional[int] = Field(default=None, 
                                      description="Number of comments on the post.")
    media: List[Dict[str, Any]] = Field(default_factory=list, 
                                description="Media attachments (images, videos).")
    hashtags: List[str] = Field(default_factory=list, description="Hashtags used in the post.")
    extracted_at: datetime = Field(default_factory=datetime.now, 
                               description="When the data was extracted.")


class LinkedInCompanyLocation(BaseModel):
    """LinkedIn company location data."""
    
    is_hq: Optional[bool] = Field(default=None, description="Whether this is headquarters.")
    office_address_line_1: Optional[str] = Field(default=None, description="Address line 1.")
    office_address_line_2: Optional[str] = Field(default=None, description="Address line 2.")
    office_location_link: Optional[str] = Field(default=None, description="Location map link.")


class LinkedInEmployee(BaseModel):
    """LinkedIn employee data."""
    
    employee_photo: Optional[str] = Field(default=None, description="Employee photo URL.")
    employee_name: Optional[str] = Field(default=None, description="Employee name.")
    employee_position: Optional[str] = Field(default=None, description="Employee position/title.")
    employee_profile_url: Optional[str] = Field(default=None, description="Employee LinkedIn profile URL.")


class LinkedInCompanyUpdate(BaseModel):
    """LinkedIn company update/post data."""
    
    text: Optional[str] = Field(default=None, description="Update text content.")
    article_posted_date: Optional[str] = Field(default=None, description="When the update was posted.")
    total_likes: Optional[str] = Field(default=None, description="Number of likes on the update.")


class LinkedInSimilarCompany(BaseModel):
    """Similar company data."""
    
    link: Optional[str] = Field(default=None, description="Link to the similar company.")
    name: Optional[str] = Field(default=None, description="Company name.")
    summary: Optional[str] = Field(default=None, description="Company summary/industry.")
    location: Optional[str] = Field(default=None, description="Company location.")


class LinkedInCompany(BaseModel):
    """LinkedIn company data."""
    
    company_url: Optional[HttpUrl] = Field(default=None, description="LinkedIn company URL.")
    company_name: Optional[str] = Field(default=None, description="Company name.")
    universal_name_id: Optional[str] = Field(default=None, description="LinkedIn universal name ID.")
    background_cover_image_url: Optional[str] = Field(default=None, description="Background cover image URL.")
    linkedin_internal_id: Optional[str] = Field(default=None, description="LinkedIn internal ID.")
    industry: Optional[str] = Field(default=None, description="Company industry.")
    location: Optional[str] = Field(default=None, description="Company location.")
    follower_count: Optional[str] = Field(default=None, description="Number of followers.")
    tagline: Optional[str] = Field(default=None, description="Company tagline.")
    company_size_on_linkedin: Optional[int] = Field(default=None, description="Company size on LinkedIn.")
    about: Optional[str] = Field(default=None, description="Company about/description.")
    website: Optional[str] = Field(default=None, description="Company website.")
    industries: Optional[str] = Field(default=None, description="Industries (may be same as industry).")
    company_size: Optional[str] = Field(default=None, description="Company size (employee range).")
    headquarters: Optional[str] = Field(default=None, description="Company headquarters.")
    type: Optional[str] = Field(default=None, description="Company type (e.g., Privately Held).")
    founded: Optional[str] = Field(default=None, description="Year founded.")
    specialties: Optional[str] = Field(default=None, description="Company specialties.")
    locations: List[LinkedInCompanyLocation] = Field(default_factory=list, description="Company locations.")
    employees: List[LinkedInEmployee] = Field(default_factory=list, description="Employee information.")
    updates: List[LinkedInCompanyUpdate] = Field(default_factory=list, description="Company updates/posts.")
    similar_companies: List[LinkedInSimilarCompany] = Field(default_factory=list, description="Similar companies.")
    affiliated_companies: List[Dict[str, Any]] = Field(default_factory=list, description="Affiliated companies.")
    extracted_at: datetime = Field(default_factory=datetime.now, 
                               description="When the data was extracted.")


class LinkedInData(BaseModel):
    """Combined LinkedIn data."""
    
    profile: Optional[LinkedInProfile] = Field(default=None, description="Profile data.")
    posts: List[LinkedInPost] = Field(default_factory=list, description="Recent posts.")
    company: Optional[LinkedInCompany] = Field(default=None, description="Company data.")


class FacebookData(BaseModel):
    """Facebook data."""
    
    page_url: Optional[HttpUrl] = Field(default=None, description="Facebook page URL.")
    name: Optional[str] = Field(default=None, description="Page name.")
    posts: List[Dict[str, Any]] = Field(default_factory=list, description="Recent posts.")
    page_info: Dict[str, Any] = Field(default_factory=dict, description="Page information.")
    extracted_at: datetime = Field(default_factory=datetime.now, 
                               description="When the data was extracted.")


class TwitterData(BaseModel):
    """Twitter/X data."""
    
    handle: Optional[str] = Field(default=None, description="Twitter/X handle.")
    profile_info: Dict[str, Any] = Field(default_factory=dict, description="Profile information.")
    tweets: List[Dict[str, Any]] = Field(default_factory=list, description="Recent tweets.")
    followers_count: Optional[int] = Field(default=None, description="Number of followers.")
    following_count: Optional[int] = Field(default=None, description="Number of accounts followed.")
    extracted_at: datetime = Field(default_factory=datetime.now, 
                               description="When the data was extracted.")


class SocialMediaData(BaseModel):
    """Combined social media data."""
    
    facebook: Optional[FacebookData] = Field(default=None, description="Facebook data.")
    twitter: Optional[TwitterData] = Field(default=None, description="Twitter/X data.")


class CompanyFinancialData(BaseModel):
    """Company financial data."""
    
    revenue: Optional[str] = Field(default=None, description="Annual revenue.")
    valuation: Optional[str] = Field(default=None, description="Company valuation.")
    funding: Optional[str] = Field(default=None, description="Total funding raised.")
    funding_rounds: List[Dict[str, Any]] = Field(default_factory=list, description="Funding rounds.")
    key_investors: List[str] = Field(default_factory=list, description="Key investors.")
    stock_symbol: Optional[str] = Field(default=None, description="Stock market symbol if public.")
    ipo_date: Optional[str] = Field(default=None, description="IPO date if applicable.")


class CompanyEmployeeData(BaseModel):
    """Company employee data."""
    
    employee_count: Optional[int] = Field(default=None, description="Total employee count.")
    growth_rate: Optional[float] = Field(default=None, 
                                     description="Employee growth rate (percentage).")
    locations: List[str] = Field(default_factory=list, description="Office locations.")
    executives: List[Dict[str, Any]] = Field(default_factory=list, 
                                       description="Key executives' information.")
    departments: Dict[str, int] = Field(default_factory=dict, 
                                  description="Department breakdown (department → count).")


class CompanyData(BaseModel):
    """Combined company data."""
    
    name: Optional[str] = Field(default=None, description="Company name.")
    website: Optional[HttpUrl] = Field(default=None, description="Company website.")
    financial: Optional[CompanyFinancialData] = Field(default_factory=CompanyFinancialData, 
                                                 description="Financial information.")
    funding: Dict[str, Any] = Field(default_factory=dict, description="Funding information.")
    industry: Dict[str, Any] = Field(default_factory=dict, description="Industry classification.")
    employees: Optional[CompanyEmployeeData] = Field(default_factory=CompanyEmployeeData, 
                                                description="Employee information.")
    technologies: List[str] = Field(default_factory=list, description="Technologies used.")
    competitors: List[str] = Field(default_factory=list, description="Competitors.")
    news: List[Dict[str, Any]] = Field(default_factory=list, description="Recent news articles.")
    sources: List[str] = Field(default_factory=list, description="Data sources.")


class KeyInsight(BaseModel):
    """A key insight about a prospect."""
    
    category: str = Field(..., description="Category of the insight.")
    title: str = Field(..., description="Short title of the insight.")
    description: str = Field(..., description="Detailed description of the insight.")
    source: str = Field(..., description="Source of the data for this insight.")
    confidence: float = Field(..., description="Confidence score (0.0-1.0).")


class AnalysisSummary(BaseModel):
    """Summary of the analysis results."""
    
    key_insights: List[KeyInsight] = Field(default_factory=list, description="Key insights.")
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list, description="Risk factors.")
    opportunities: List[Dict[str, Any]] = Field(default_factory=list, description="Opportunities.")
    summary_text: Optional[str] = Field(default=None, description="Text summary of analysis.")


class ActorExecution(BaseModel):
    """Record of an actor execution."""
    
    actor_id: str = Field(..., description="ID of the actor.")
    run_id: str = Field(..., description="ID of the actor run.")
    actor_name: str = Field(..., description="Name of the actor.")
    status: str = Field(..., description="Status of the execution.")
    started_at: datetime = Field(..., description="When the execution started.")
    completed_at: Optional[datetime] = Field(default=None, description="When the execution completed.")
    duration_secs: Optional[float] = Field(default=None, description="Duration in seconds.")
    cost: Decimal = Field(..., description="Cost of the execution.")
    input_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of the input.")
    output_summary: Dict[str, Any] = Field(default_factory=dict, 
                                      description="Summary of the output.")
    error_message: Optional[str] = Field(default=None, description="Error message if any.")


class CostBreakdown(BaseModel):
    """Cost breakdown for an analysis."""
    
    total: Decimal = Field(..., description="Total cost in USD.")
    per_actor: Dict[str, Decimal] = Field(..., description="Cost per actor.")


class ExecutionMetadata(BaseModel):
    """Metadata about the analysis execution."""
    
    duration_secs: float = Field(..., description="Total duration in seconds.")
    actors_used: List[str] = Field(..., description="IDs of actors used.")
    success_rate: float = Field(..., description="Success rate (percentage).")
    started_at: datetime = Field(..., description="When the analysis started.")
    completed_at: datetime = Field(..., description="When the analysis completed.")
    trace_id: str = Field(..., description="Trace ID for debugging.")


class ConfidenceScores(BaseModel):
    """Confidence scores for different data parts."""
    
    linkedin: Optional[float] = Field(default=None, description="LinkedIn data confidence.")
    social_media: Optional[float] = Field(default=None, description="Social media data confidence.")
    company_data: Optional[float] = Field(default=None, description="Company data confidence.")
    overall: float = Field(..., description="Overall confidence score.")


class Analysis(BaseModel):
    """Complete analysis record."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier.")
    prospect_id: str = Field(..., description="ID of the prospect analyzed.")
    status: AnalysisStatus = Field(..., description="Analysis status.")
    parameters: AnalysisParameters = Field(..., description="Analysis parameters.")
    started_at: datetime = Field(..., description="When analysis started.")
    completed_at: Optional[datetime] = Field(default=None, description="When analysis completed.")
    executions: List[ActorExecution] = Field(default_factory=list, description="Actor executions.")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Analysis result.")
    error: Optional[str] = Field(default=None, description="Error message if failed.")


class ProspectAnalysisResponse(BaseModel):
    """Response model for prospect analysis."""
    
    prospect_id: str = Field(..., description="ID of the analyzed prospect.")
    analysis_id: str = Field(..., description="ID of the analysis.")
    timestamp: datetime = Field(..., description="Time of the analysis.")
    input_data: Prospect = Field(..., description="Input prospect data.")
    linkedin_data: Optional[LinkedInData] = Field(default=None, description="LinkedIn data.")
    social_media_data: Optional[SocialMediaData] = Field(default=None, 
                                                    description="Social media data.")
    company_data: Optional[CompanyData] = Field(default=None, description="Company data.")
    analysis_summary: Optional[AnalysisSummary] = Field(default=None, 
                                                   description="Analysis summary.")
    cost_breakdown: CostBreakdown = Field(..., description="Cost breakdown.")
    data_sources: List[str] = Field(..., description="Data sources used.")
    confidence_scores: ConfidenceScores = Field(..., description="Confidence scores.")
    execution_metadata: ExecutionMetadata = Field(..., description="Execution metadata.")


class BatchAnalysisResponse(BaseModel):
    """Response model for batch prospect analysis."""
    
    batch_id: str = Field(..., description="ID of the batch analysis.")
    timestamp: datetime = Field(..., description="Time of the analysis.")
    prospects_count: int = Field(..., description="Number of prospects in the batch.")
    completed_count: int = Field(..., description="Number of completed analyses.")
    failed_count: int = Field(..., description="Number of failed analyses.")
    total_cost: Decimal = Field(..., description="Total cost in USD.")
    results: List[ProspectAnalysisResponse] = Field(..., description="Analysis results.")
    execution_metadata: ExecutionMetadata = Field(..., description="Execution metadata.")


class ActorInfo(BaseModel):
    """Information about an Apify actor."""
    
    id: str = Field(..., description="Apify actor ID.")
    name: str = Field(..., description="Actor name.")
    description: Optional[str] = Field(default=None, description="Actor description.")
    category: Optional[str] = Field(default=None, description="Actor category.")
    cost_structure: Dict[str, Any] = Field(..., description="Cost structure.")
    input_schema: Dict[str, Any] = Field(..., description="Input schema.")
    output_schema: Dict[str, Any] = Field(..., description="Output schema.")
    example_input: Dict[str, Any] = Field(default_factory=dict, description="Example input.")
    example_output: Dict[str, Any] = Field(default_factory=dict, description="Example output.")


class ActorsResponse(BaseModel):
    """Response model for listing available actors."""
    
    actors: List[ActorInfo] = Field(..., description="List of available actors.")
    category_breakdown: Dict[str, int] = Field(..., 
                                         description="Number of actors per category.")
    total_count: int = Field(..., description="Total number of actors.")


class HealthStatus(str, Enum):
    """Health status options."""
    
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ActorHealthInfo(BaseModel):
    """Health information for an actor."""
    
    id: str = Field(..., description="Actor ID.")
    name: str = Field(..., description="Actor name.")
    status: HealthStatus = Field(..., description="Health status.")
    last_successful_run: Optional[datetime] = Field(default=None, 
                                                description="Last successful run.")
    error: Optional[str] = Field(default=None, description="Error message if unhealthy.")


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: HealthStatus = Field(..., description="Overall system status.")
    timestamp: datetime = Field(..., description="Current timestamp.")
    version: str = Field(..., description="API version.")
    actors: List[ActorHealthInfo] = Field(..., description="Actor health information.")
    api_latency_ms: float = Field(..., description="API latency in milliseconds.")
    database_status: HealthStatus = Field(..., description="Database status.")
    cache_status: HealthStatus = Field(..., description="Cache status.")
    uptime: str = Field(..., description="System uptime.")


class ActorResponse(BaseModel):
    """Standard response model for actor results."""
    success: bool = Field(..., description="Whether the operation was successful")
    data: List[Any] = Field(..., description="Retrieved data")
    metadata: Dict[str, Any] = Field(..., description="Run metadata including costs and timing")
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp") 