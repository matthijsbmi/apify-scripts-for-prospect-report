"""
LinkedIn API endpoints.

Endpoints for LinkedIn profile scraping, posts, and company data.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field, validator

import structlog

from app.actors.linkedin.profile_scraper import LinkedInProfileScraper
from app.actors.linkedin.posts_scraper import LinkedInPostsScraper
from app.actors.linkedin.company_actor import LinkedInCompanyActor
from app.core.apify_client import ApifyService
from app.cost.manager import CostManager


logger = structlog.get_logger(__name__)
router = APIRouter()

# Initialize services
apify_service = ApifyService()
cost_manager = CostManager()


class LinkedInProfileRequest(BaseModel):
    """Request model for LinkedIn profile scraping."""
    urls: List[str] = Field(..., description="List of LinkedIn profile URLs", min_items=1, max_items=100)
    max_budget_usd: Optional[float] = Field(None, description="Maximum budget in USD")
    timeout_secs: int = Field(300, description="Timeout in seconds", ge=60, le=1800)

    @validator('urls')
    def validate_urls(cls, v):
        """Validate LinkedIn URLs."""
        for url in v:
            if 'linkedin.com/in/' not in url.lower():
                raise ValueError(f"Invalid LinkedIn profile URL: {url}")
        return v


class LinkedInPostsRequest(BaseModel):
    """Request model for LinkedIn posts scraping."""
    profile_urls: List[str] = Field(..., description="List of LinkedIn profile URLs", min_items=1, max_items=50)
    max_posts_per_profile: int = Field(10, description="Maximum posts per profile", ge=1, le=100)
    max_budget_usd: Optional[float] = Field(None, description="Maximum budget in USD")
    timeout_secs: int = Field(600, description="Timeout in seconds", ge=120, le=3600)

    @validator('profile_urls')
    def validate_urls(cls, v):
        """Validate LinkedIn URLs."""
        for url in v:
            if 'linkedin.com/in/' not in url.lower():
                raise ValueError(f"Invalid LinkedIn profile URL: {url}")
        return v


class LinkedInCompanyRequest(BaseModel):
    """Request model for LinkedIn company scraping."""
    company_urls: List[str] = Field(..., description="List of LinkedIn company URLs", min_items=1, max_items=50)
    max_budget_usd: Optional[float] = Field(None, description="Maximum budget in USD")
    timeout_secs: int = Field(600, description="Timeout in seconds", ge=120, le=3600)

    @validator('company_urls')
    def validate_urls(cls, v):
        """Validate LinkedIn company URLs."""
        for url in v:
            if 'linkedin.com/company/' not in url.lower():
                raise ValueError(f"Invalid LinkedIn company URL: {url}")
        return v


class ActorResponse(BaseModel):
    """Standard response model for actor results."""
    success: bool = Field(..., description="Whether the operation was successful")
    data: List[Any] = Field(..., description="Retrieved data")
    metadata: Dict[str, Any] = Field(..., description="Run metadata including costs and timing")
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


@router.post("/profiles", response_model=ActorResponse, tags=["LinkedIn"])
async def scrape_linkedin_profiles(
    request: LinkedInProfileRequest,
    background_tasks: BackgroundTasks
) -> ActorResponse:
    """
    Scrape LinkedIn profile data including personal information, experience, and education.
    
    **Actor:** LinkedIn Profile Bulk Scraper (LpVuK3Zozwuipa5bp)  
    **Cost:** $0.004 per profile  
    **Max Profiles:** 100 per run
    
    **Features:**
    - Profile data (name, headline, location, connections)
    - Work experience and education history
    - Skills and certifications
    - Data transformation to standardized format
    - Cost tracking and validation
    
    **Returns:** Complete profile data with metadata.
    """
    request_id = str(uuid.uuid4())
    log = logger.bind(request_id=request_id, profile_count=len(request.urls))
    
    log.info("Starting LinkedIn profile scraping")
    start_time = time.time()
    
    try:
        scraper = LinkedInProfileScraper(apify_service, cost_manager)
        
        # Execute scraping
        result = await scraper.scrape_profiles(
            profile_urls=request.urls,
            max_budget_usd=request.max_budget_usd,
            timeout_secs=request.timeout_secs
        )
        
        execution_time = time.time() - start_time
        log.info(
            "LinkedIn profile scraping completed",
            execution_time=execution_time,
            profiles_retrieved=len(result['data']) if result['data'] else 0
        )
        
        return ActorResponse(
            success=True,
            data=result['data'] or [],
            metadata={
                **result['metadata'].__dict__,
                'execution_time': execution_time,
                'actor_id': 'LpVuK3Zozwuipa5bp',
                'actor_name': 'LinkedIn Profile Bulk Scraper'
            },
            request_id=request_id
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "LinkedIn profile scraping failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"Profile scraping failed: {str(e)}"
        )


@router.post("/posts", response_model=ActorResponse, tags=["LinkedIn"])
async def scrape_linkedin_posts(
    request: LinkedInPostsRequest,
    background_tasks: BackgroundTasks
) -> ActorResponse:
    """
    Scrape recent posts from LinkedIn profiles including content and engagement metrics.
    
    **Actor:** LinkedIn Posts Bulk Scraper (A3cAPGpwBEG8RJwse)  
    **Cost:** $0.002 per post  
    **Max Posts:** 1000 per run
    
    **Features:**
    - Recent posts extraction from LinkedIn profiles
    - Content, engagement metrics, and metadata
    - Author information and posting dates
    - Article links and media detection
    
    **Returns:** Posts data with engagement metrics and metadata.
    """
    request_id = str(uuid.uuid4())
    log = logger.bind(
        request_id=request_id, 
        profile_count=len(request.profile_urls),
        max_posts_per_profile=request.max_posts_per_profile
    )
    
    log.info("Starting LinkedIn posts scraping")
    start_time = time.time()
    
    try:
        scraper = LinkedInPostsScraper(apify_service, cost_manager)
        
        # Execute scraping
        result = await scraper.scrape_posts(
            profile_urls=request.profile_urls,
            max_posts=request.max_posts_per_profile,
            max_budget_usd=request.max_budget_usd,
            timeout_secs=request.timeout_secs
        )
        
        execution_time = time.time() - start_time
        log.info(
            "LinkedIn posts scraping completed",
            execution_time=execution_time,
            posts_retrieved=len(result['data']) if result['data'] else 0
        )
        
        return ActorResponse(
            success=True,
            data=result['data'] or [],
            metadata={
                **result['metadata'].__dict__,
                'execution_time': execution_time,
                'actor_id': 'A3cAPGpwBEG8RJwse',
                'actor_name': 'LinkedIn Posts Bulk Scraper'
            },
            request_id=request_id
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "LinkedIn posts scraping failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"Posts scraping failed: {str(e)}"
        )


@router.post("/companies", response_model=ActorResponse, tags=["LinkedIn"])
async def scrape_linkedin_companies(
    request: LinkedInCompanyRequest,
    background_tasks: BackgroundTasks
) -> ActorResponse:
    """
    Scrape LinkedIn company pages for comprehensive business information and insights.
    
    **Actor:** sanjeta/linkedin-company-profile-scraper  
    **Cost:** ~$0.01-0.05 per company profile  
    **Max Companies:** 50 per run
    
    **Features:**
    - Complete company information (name, tagline, about, website)
    - Industry classification and company size data
    - Employee profiles with photos and positions
    - Recent company updates and posts with engagement metrics
    - Office locations and contact information
    - Similar and affiliated companies
    - Logo and cover images
    - Raw data format with 26+ fields per company
    
    **Returns:** Raw company data directly from LinkedIn with comprehensive metadata.
    """
    request_id = str(uuid.uuid4())
    log = logger.bind(request_id=request_id, company_count=len(request.company_urls))
    
    log.info("Starting LinkedIn company scraping")
    start_time = time.time()
    
    try:
        actor = LinkedInCompanyActor()
        
        # Execute scraping
        result = await actor.scrape_companies(
            company_urls=request.company_urls,
            max_budget_usd=request.max_budget_usd,
            timeout_secs=request.timeout_secs
        )
        
        # Extract raw data from metadata.items
        metadata = result.get('metadata')
        raw_companies = metadata.items if metadata and hasattr(metadata, 'items') and metadata.items else []
        
        execution_time = time.time() - start_time
        log.info(
            "LinkedIn company scraping completed",
            execution_time=execution_time,
            companies_retrieved=len(raw_companies)
        )
        
        return ActorResponse(
            success=True,
            data=raw_companies,
            metadata={
                **(metadata.__dict__ if hasattr(metadata, '__dict__') else {}),
                'execution_time': execution_time,
                'actor_id': 'sanjeta/linkedin-company-profile-scraper',
                'actor_name': 'LinkedIn Company Profile Scraper'
            },
            request_id=request_id
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "LinkedIn company scraping failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"Company scraping failed: {str(e)}"
        )


@router.get("/pricing", tags=["LinkedIn"])
async def get_linkedin_pricing() -> Dict[str, Any]:
    """
    Get current pricing information for LinkedIn actors.
    
    **Returns:** Pricing details for all LinkedIn scraping services.
    """
    return {
        "profile_scraper": {
            "actor_id": "LpVuK3Zozwuipa5bp",
            "cost_per_profile": 0.004,
            "currency": "USD",
            "max_profiles_per_run": 100,
            "estimated_runtime_per_profile": "2-5 seconds"
        },
        "posts_scraper": {
            "actor_id": "A3cAPGpwBEG8RJwse", 
            "cost_per_post": 0.002,
            "currency": "USD",
            "max_posts_per_run": 1000,
            "estimated_runtime_per_post": "1-3 seconds"
        },
        "company_scraper": {
            "actor_id": "sanjeta/linkedin-company-profile-scraper",
            "cost_per_company": "0.01-0.05",
            "cost_model": "Pay-per-use",
            "currency": "USD",
            "max_companies_per_run": 50,
            "estimated_runtime_per_company": "5-10 seconds",
            "data_fields": "26+ fields including employees, updates, locations"
        }
    }


@router.get("/test", tags=["LinkedIn"])
async def test_linkedin_actor(
    actor_type: str = Query(..., description="Actor type: profiles, posts, or companies"),
    sample_size: int = Query(1, description="Number of sample items to test", ge=1, le=3)
) -> Dict[str, Any]:
    """
    Test LinkedIn actors with predefined sample data.
    
    **Parameters:**
    - `actor_type`: Type of actor to test (profiles, posts, companies)
    - `sample_size`: Number of sample items to process (1-3)
    
    **Returns:** Test results with sample data.
    """
    test_data = {
        "profiles": [
            "https://www.linkedin.com/in/billgates/",
            "https://www.linkedin.com/in/satyanadella/",
            "https://www.linkedin.com/in/jeffweiner08/"
        ],
        "posts": [
            "https://www.linkedin.com/in/billgates/",
            "https://www.linkedin.com/in/satyanadella/"
        ],
        "companies": [
            "https://www.linkedin.com/company/microsoft/",
            "https://www.linkedin.com/company/apple/"
        ]
    }
    
    if actor_type not in test_data:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid actor type. Must be one of: {list(test_data.keys())}"
        )
    
    sample_urls = test_data[actor_type][:sample_size]
    
    try:
        if actor_type == "profiles":
            request = LinkedInProfileRequest(urls=sample_urls, timeout_secs=180)
            result = await scrape_linkedin_profiles(request, BackgroundTasks())
        elif actor_type == "posts":
            request = LinkedInPostsRequest(profile_urls=sample_urls, max_posts_per_profile=5, timeout_secs=300)
            result = await scrape_linkedin_posts(request, BackgroundTasks())
        elif actor_type == "companies":
            request = LinkedInCompanyRequest(company_urls=sample_urls, timeout_secs=300)
            result = await scrape_linkedin_companies(request, BackgroundTasks())
        
        return {
            "test_type": actor_type,
            "sample_urls": sample_urls,
            "success": result.success,
            "items_retrieved": len(result.data),
            "execution_time": result.metadata.get('execution_time'),
            "cost": result.metadata.get('cost_usd', 0),
            "sample_data": result.data[:2] if result.data else []  # Return first 2 items
        }
        
    except Exception as e:
        return {
            "test_type": actor_type,
            "sample_urls": sample_urls,
            "success": False,
            "error": str(e)
        } 