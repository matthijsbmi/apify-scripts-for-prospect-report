"""
Endpoints for company data scraping including Erasmus+, ZoomInfo, and D&B.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field, validator

import structlog

from app.core.apify_client import ApifyService
from app.cost.manager import CostManager
from app.actors.company.erasmus_actor import ErasmusActor
from app.actors.company.zoominfo_actor import ZoomInfoActor
from app.actors.company.duns_actor import DunsActor
from app.models.data import ActorResponse


logger = structlog.get_logger(__name__)
router = APIRouter()

# Initialize services
apify_service = ApifyService()
cost_manager = CostManager()


class ErasmusDomainRequest(BaseModel):
    """Request model for Erasmus domain search."""
    domain: str = Field(..., description="Domain to search for (e.g., 'www.uva.nl')")
    max_budget_usd: Optional[float] = Field(None, description="Maximum budget in USD")
    timeout_secs: int = Field(300, description="Timeout in seconds", ge=60, le=1800)

    @validator('domain')
    def clean_domain(cls, v):
        """Clean and validate domain."""
        # Remove protocol and path
        domain = v.lower().replace('http://', '').replace('https://', '').split('/')[0]
        if not domain or '.' not in domain:
            raise ValueError(f"Invalid domain format: {v}")
        return domain


class ErasmusNameRequest(BaseModel):
    """Request model for Erasmus name search."""
    organization_names: List[str] = Field(..., description="List of organization names to search", min_items=1, max_items=50)
    max_budget_usd: Optional[float] = Field(None, description="Maximum budget in USD")
    timeout_secs: int = Field(600, description="Timeout in seconds", ge=120, le=3600)

    @validator('organization_names')
    def validate_names(cls, v):
        """Validate organization names."""
        for name in v:
            if not name.strip() or len(name.strip()) < 2:
                raise ValueError(f"Invalid organization name: {name}")
        return [name.strip() for name in v]


class ZoomInfoRequest(BaseModel):
    """Request model for ZoomInfo search."""
    urls_or_names: List[str] = Field(..., description="List of ZoomInfo URLs or company names to search", min_items=1, max_items=50)
    include_similar_companies: bool = Field(True, description="Whether to include similar companies data")
    max_budget_usd: Optional[float] = Field(None, description="Maximum budget in USD")
    timeout_secs: int = Field(600, description="Timeout in seconds", ge=120, le=3600)

    @validator('urls_or_names')
    def validate_urls_or_names(cls, v):
        """Validate URLs or company names."""
        for item in v:
            if not item.strip() or len(item.strip()) < 2:
                raise ValueError(f"Invalid URL or company name: {item}")
        return [item.strip() for item in v]


class DunsRequest(BaseModel):
    """Request model for D&B DUNS search."""
    search_term: str = Field(..., description="Company name or search term")
    revenue_min: Optional[int] = Field(None, description="Minimum revenue filter")
    number_of_employees_min: Optional[int] = Field(None, description="Minimum number of employees filter")
    year_start_from: Optional[int] = Field(None, description="Minimum year company was established")
    country_in: Optional[str] = Field(None, description="Countries to search in (comma-separated)")
    industry_in: Optional[str] = Field(None, description="Industries to search in (comma-separated)")
    max_items: int = Field(10, description="Maximum number of companies to retrieve", ge=1, le=100)
    proxy_configuration: Optional[Dict[str, Any]] = Field(None, description="Optional proxy configuration")
    max_budget_usd: Optional[float] = Field(None, description="Maximum budget in USD")
    timeout_secs: int = Field(600, description="Timeout in seconds", ge=120, le=3600)


@router.post("/erasmus/domain", response_model=ActorResponse, tags=["Company"])
async def search_erasmus_by_domain(
    request: ErasmusDomainRequest,
    background_tasks: BackgroundTasks
) -> ActorResponse:
    """
    Search Erasmus+ database by organization domain (most effective method).
    
    **Actor:** Erasmus+ Organisation Scraper (5ms6D6gKCnJhZN61e)  
    **Cost:** Pay-per-use  
    **Search Method:** Domain-based (recommended)
    
    **Features:**
    - Organization data from Erasmus+ database
    - Legal names, business names, and registration info
    - Location data (country, city)
    - PIC codes and VAT numbers
    - Website validation
    
    **Returns:** Organization data with registration details.
    """
    request_id = str(uuid.uuid4())
    log = logger.bind(request_id=request_id, domain=request.domain)
    
    log.info("Starting Erasmus domain search")
    start_time = time.time()
    
    try:
        actor = ErasmusActor()
        
        # Execute search
        result = await actor.scrape_by_domain(
            domain=request.domain,
            max_budget_usd=request.max_budget_usd,
            timeout_secs=request.timeout_secs
        )
        
        execution_time = time.time() - start_time
        log.info(
            "Erasmus domain search completed",
            execution_time=execution_time,
            organizations_found=len(result['data']) if result['data'] else 0
        )
        
        return ActorResponse(
            success=True,
            data=result['data'] or [],
            metadata={
                **(result['metadata'].__dict__ if hasattr(result['metadata'], '__dict__') else result['metadata']),
                'execution_time': execution_time,
                'actor_id': '5ms6D6gKCnJhZN61e',
                'actor_name': 'Erasmus+ Organisation Scraper',
                'search_method': 'domain'
            },
            request_id=request_id
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "Erasmus domain search failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erasmus domain search failed: {str(e)}"
        )


@router.post("/erasmus/name", response_model=ActorResponse, tags=["Company"])
async def search_erasmus_by_name(
    request: ErasmusNameRequest,
    background_tasks: BackgroundTasks
) -> ActorResponse:
    """
    Search Erasmus+ database by organization names.
    
    **Actor:** Erasmus+ Organisation Scraper (5ms6D6gKCnJhZN61e)  
    **Cost:** Pay-per-use  
    **Search Method:** Name-based
    
    **Features:**
    - Multiple organization name searches
    - Fuzzy matching capabilities
    - Complete organization profiles
    - European education institution data
    
    **Returns:** Organization data for multiple searches.
    """
    request_id = str(uuid.uuid4())
    log = logger.bind(request_id=request_id, org_count=len(request.organization_names))
    
    log.info("Starting Erasmus name search")
    start_time = time.time()
    
    try:
        actor = ErasmusActor()
        
        # Execute searches for each organization
        all_results = []
        total_metadata = {'searches': []}
        
        for org_name in request.organization_names:
            result = await actor.scrape_single_organization(
                organization_name=org_name,
                max_budget_usd=request.max_budget_usd,
                timeout_secs=request.timeout_secs // len(request.organization_names)
            )
            
            if result['data']:
                all_results.extend(result['data'])
            
            # Collect metadata
            total_metadata['searches'].append({
                'organization_name': org_name,
                'results_found': len(result['data']) if result['data'] else 0,
                'metadata': result['metadata'].__dict__ if hasattr(result['metadata'], '__dict__') else result['metadata']
            })
        
        execution_time = time.time() - start_time
        log.info(
            "Erasmus name search completed",
            execution_time=execution_time,
            total_organizations_found=len(all_results)
        )
        
        return ActorResponse(
            success=True,
            data=all_results,
            metadata={
                **total_metadata,
                'execution_time': execution_time,
                'actor_id': '5ms6D6gKCnJhZN61e',
                'actor_name': 'Erasmus+ Organisation Scraper',
                'search_method': 'name',
                'organizations_searched': len(request.organization_names)
            },
            request_id=request_id
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "Erasmus name search failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erasmus name search failed: {str(e)}"
        )


@router.post("/zoominfo", response_model=ActorResponse, tags=["Company"])
async def search_zoominfo(
    request: ZoomInfoRequest,
    background_tasks: BackgroundTasks
) -> ActorResponse:
    """
    Scrape company data from ZoomInfo using URLs or company names.
    
    **Actor:** ZoomInfo Scraper (C6OyLbP5ixnfc5lYe)  
    **Cost:** ~$0.01-0.05 per company  
    **Input Types:** ZoomInfo URLs or company names
    
    **Features:**
    - Comprehensive company data including financial info, employees, and similar companies
    - Revenue details with currency and text format
    - Complete address and contact information 
    - Founding year and industry classifications
    - Similar companies with CEO information
    - Complete funding history with investor details
    - Social network URLs (LinkedIn, Twitter, Facebook)
    - Stock symbols and business descriptions
    
    **Returns:** Raw company data with 19+ fields per company.
    """
    request_id = str(uuid.uuid4())
    log = logger.bind(request_id=request_id, input_count=len(request.urls_or_names))
    
    log.info("Starting ZoomInfo search")
    start_time = time.time()
    
    try:
        actor = ZoomInfoActor()
        
        # Execute search
        result = await actor.scrape_companies(
            urls_or_names=request.urls_or_names,
            include_similar_companies=request.include_similar_companies,
            max_budget_usd=request.max_budget_usd,
            timeout_secs=request.timeout_secs
        )
        
        execution_time = time.time() - start_time
        log.info(
            "ZoomInfo search completed",
            execution_time=execution_time,
            companies_found=len(result) if result else 0
        )
        
        return ActorResponse(
            success=True,
            data=result or [],
            metadata={
                'execution_time': execution_time,
                'actor_id': 'C6OyLbP5ixnfc5lYe',
                'actor_name': 'ZoomInfo Scraper',
                'companies_found': len(result) if result else 0,
                'include_similar_companies': request.include_similar_companies
            },
            request_id=request_id
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "ZoomInfo search failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"ZoomInfo search failed: {str(e)}"
        )


@router.post("/duns", response_model=ActorResponse, tags=["Company"])
async def search_duns(
    request: DunsRequest,
    background_tasks: BackgroundTasks
) -> ActorResponse:
    """
    Search D&B (Dun & Bradstreet) database for company credit and business data.
    
    **Actor:** Dun & Bradstreet Scraper (RIq8Fe9BdxSR4GUXY)  
    **Cost:** ~1 Compute unit per 1000 actor pages scraped  
    **Search Method:** Search term with advanced filters
    
    **Features:**
    - Company profiles with detailed information
    - Revenue, employees, industry classifications
    - Principal/executive information
    - Address and contact details
    - Business type and incorporation data
    - Raw output with 20+ fields per company
    
    **Returns:** Raw company data with comprehensive business information.
    """
    request_id = str(uuid.uuid4())
    log = logger.bind(request_id=request_id, search_term=request.search_term, max_items=request.max_items)
    
    log.info("Starting D&B DUNS search")
    start_time = time.time()
    
    try:
        actor = DunsActor()
        
        # Execute search
        result = await actor.search_companies(
            search_term=request.search_term,
            revenue_min=request.revenue_min,
            number_of_employees_min=request.number_of_employees_min,
            year_start_from=request.year_start_from,
            country_in=request.country_in,
            industry_in=request.industry_in,
            max_items=request.max_items,
            proxy_configuration=request.proxy_configuration,
            max_budget_usd=request.max_budget_usd,
            timeout_secs=request.timeout_secs
        )
        
        execution_time = time.time() - start_time
        log.info(
            "D&B DUNS search completed",
            execution_time=execution_time,
            companies_found=len(result) if result else 0
        )
        
        return ActorResponse(
            success=True,
            data=result or [],
            metadata={
                'execution_time': execution_time,
                'actor_id': 'RIq8Fe9BdxSR4GUXY',
                'actor_name': 'Dun & Bradstreet Scraper',
                'search_term': request.search_term,
                'filters_applied': {
                    'revenue_min': request.revenue_min,
                    'employees_min': request.number_of_employees_min,
                    'year_start_from': request.year_start_from,
                    'countries': request.country_in,
                    'industries': request.industry_in
                }
            },
            request_id=request_id
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "D&B DUNS search failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"D&B DUNS search failed: {str(e)}"
        )


@router.get("/erasmus/pricing", tags=["Company"])
async def get_erasmus_pricing() -> Dict[str, Any]:
    """
    Get current pricing information for Erasmus+ actor.
    
    **Returns:** Pricing details for Erasmus+ organization searches.
    """
    return {
        "erasmus_actor": {
            "actor_id": "5ms6D6gKCnJhZN61e",
            "cost_model": "Pay-per-use",
            "currency": "USD",
            "search_types": ["domain", "name", "organization_id"],
            "recommended_method": "domain",
            "max_organizations_per_run": 50,
            "estimated_runtime_per_search": "10-30 seconds"
        }
    }


@router.get("/zoominfo/pricing", tags=["Company"])
async def get_zoominfo_pricing() -> Dict[str, Any]:
    """
    Get current pricing information for ZoomInfo Scraper actor.
    
    **Returns:** Pricing details for ZoomInfo company searches.
    """
    return {
        "zoominfo_actor": {
            "actor_id": "C6OyLbP5ixnfc5lYe",
            "cost_model": "Pay-per-use",
            "currency": "USD",
            "estimated_cost_per_company": "$0.01-0.05",
            "input_types": ["ZoomInfo URLs", "Company names"],
            "recommended_input": "Company names (e.g., 'walmart', 'microsoft')",
            "max_companies_per_run": 50,
            "estimated_runtime_per_company": "5-15 seconds",
            "features": [
                "Company profiles with 19+ fields",
                "Financial data (revenue, funding)",
                "Similar companies with CEO info",
                "Social network URLs",
                "Complete contact information",
                "Industry classifications"
            ]
        }
    }


@router.get("/duns/pricing", tags=["Company"])
async def get_duns_pricing() -> Dict[str, Any]:
    """
    Get current pricing information for Dun & Bradstreet Scraper actor.
    
    **Returns:** Pricing details for D&B company searches.
    """
    return {
        "duns_actor": {
            "actor_id": "RIq8Fe9BdxSR4GUXY",
            "cost_model": "Pay-per-use",
            "currency": "USD",
            "estimated_cost": "1 Compute unit per 1000 actor pages scraped",
            "input_types": ["Search terms with filters"],
            "max_items_per_run": 100,
            "estimated_runtime": "Varies by search complexity",
            "features": [
                "Company profiles with 20+ fields",
                "Revenue and employee data",
                "Principal/executive information",
                "Complete address and contact details",
                "Industry classifications",
                "Business type and incorporation data",
                "Advanced filtering (revenue, employees, year, country, industry)"
            ],
            "filters": {
                "revenue_min": "Minimum revenue filter",
                "number_of_employees_min": "Minimum employee count",
                "year_start_from": "Company establishment year",
                "country_in": "Countries (comma-separated)",
                "industry_in": "Industries (comma-separated)"
            }
        }
    }


@router.get("/test", tags=["Company"])
async def test_company_actor(
    actor_type: str = Query(..., description="Actor type: erasmus-domain, erasmus-name, zoominfo, or duns"),
    sample_size: int = Query(1, description="Number of sample items to test", ge=1, le=2)
) -> Dict[str, Any]:
    """
    Test company actors with predefined sample data.
    
    **Parameters:**
    - `actor_type`: Type of actor to test
    - `sample_size`: Number of sample items to process (1-2)
    
    **Returns:** Test results with sample data.
    """
    test_data = {
        "erasmus-domain": {
            "domains": ["www.uva.nl", "www.ox.ac.uk"],
            "endpoint": "erasmus/domain"
        },
        "erasmus-name": {
            "names": ["University of Amsterdam", "Oxford University"],
            "endpoint": "erasmus/name"
        },
        "zoominfo": {
            "urls_or_names": ["walmart", "microsoft"],
            "endpoint": "zoominfo"
        },
        "duns": {
            "search_term": "Apple",
            "max_items": 2,
            "endpoint": "duns"
        }
    }
    
    if actor_type not in test_data:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid actor type. Must be one of: {list(test_data.keys())}"
        )
    
    sample_data = test_data[actor_type]
    
    try:
        if actor_type == "erasmus-domain":
            domain = sample_data["domains"][0]  # Use first domain for single test
            request = ErasmusDomainRequest(domain=domain, timeout_secs=180)
            result = await search_erasmus_by_domain(request, BackgroundTasks())
        elif actor_type == "erasmus-name":
            names = sample_data["names"][:sample_size]
            request = ErasmusNameRequest(organization_names=names, timeout_secs=300)
            result = await search_erasmus_by_name(request, BackgroundTasks())
        elif actor_type == "zoominfo":
            urls_or_names = sample_data["urls_or_names"][:sample_size]
            request = ZoomInfoRequest(urls_or_names=urls_or_names, timeout_secs=300)
            result = await search_zoominfo(request, BackgroundTasks())
        elif actor_type == "duns":
            search_term = sample_data["search_term"]
            max_items = min(sample_data["max_items"], sample_size)
            request = DunsRequest(search_term=search_term, max_items=max_items, timeout_secs=300)
            result = await search_duns(request, BackgroundTasks())
        
        return {
            "test_type": actor_type,
            "sample_data": sample_data,
            "success": result.success,
            "items_retrieved": len(result.data),
            "execution_time": result.metadata.get('execution_time'),
            "cost": result.metadata.get('cost_usd', 0),
            "sample_results": result.data[:1] if result.data else []  # Return first result
        }
        
    except Exception as e:
        return {
            "test_type": actor_type,
            "sample_data": sample_data,
            "success": False,
            "error": str(e)
        } 