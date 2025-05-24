"""
Social Media API endpoints.

Endpoints for social media data scraping including Twitter/X and Facebook.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field, validator

import structlog

from app.actors.social.twitter_actor import TwitterActor
from app.actors.social.facebook_actor import FacebookActor
from app.core.apify_client import ApifyService
from app.cost.manager import CostManager


logger = structlog.get_logger(__name__)
router = APIRouter()

# Initialize services
apify_service = ApifyService()
cost_manager = CostManager()


class TwitterHandlesRequest(BaseModel):
    """Request model for Twitter handles scraping."""
    twitter_handles: List[str] = Field(..., description="List of Twitter handles (with or without @)", min_items=1, max_items=50)
    max_items: int = Field(100, description="Maximum number of tweets to scrape", ge=1, le=2000)
    sort: str = Field("Latest", description="Sort order: Latest, Popular")
    start_date: Optional[str] = Field(None, description="Start date for tweets (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date for tweets (YYYY-MM-DD)")
    tweet_language: str = Field("en", description="Tweet language code (e.g., 'en', 'es')")
    minimum_favorites: Optional[int] = Field(None, description="Minimum number of favorites/likes")
    minimum_replies: Optional[int] = Field(None, description="Minimum number of replies")
    minimum_retweets: Optional[int] = Field(None, description="Minimum number of retweets")
    only_verified_users: bool = Field(False, description="Only include tweets from verified users")
    only_twitter_blue: bool = Field(False, description="Only include tweets from Twitter Blue users")
    only_image: bool = Field(False, description="Only include tweets with images")
    only_video: bool = Field(False, description="Only include tweets with videos")
    only_quote: bool = Field(False, description="Only include quote tweets")
    max_budget_usd: Optional[float] = Field(None, description="Maximum budget in USD")
    timeout_secs: int = Field(600, description="Timeout in seconds", ge=120, le=3600)

    @validator('twitter_handles')
    def validate_handles(cls, v):
        """Validate Twitter handles."""
        cleaned_handles = []
        for handle in v:
            # Remove @ if present and clean
            clean_handle = handle.strip().lstrip('@')
            if not clean_handle:
                raise ValueError(f"Invalid Twitter handle: {handle}")
            cleaned_handles.append(clean_handle)
        return cleaned_handles


class TwitterSearchRequest(BaseModel):
    """Request model for Twitter search terms."""
    search_terms: List[str] = Field(..., description="List of search terms", min_items=1, max_items=20)
    max_items: int = Field(1000, description="Maximum number of tweets to scrape", ge=1, le=5000)
    sort: str = Field("Latest", description="Sort order: Latest, Popular")
    start_date: Optional[str] = Field(None, description="Start date for tweets (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date for tweets (YYYY-MM-DD)")
    tweet_language: str = Field("en", description="Tweet language code (e.g., 'en', 'es')")
    minimum_favorites: Optional[int] = Field(None, description="Minimum number of favorites/likes")
    minimum_replies: Optional[int] = Field(None, description="Minimum number of replies")
    minimum_retweets: Optional[int] = Field(None, description="Minimum number of retweets")
    only_verified_users: bool = Field(False, description="Only include tweets from verified users")
    only_twitter_blue: bool = Field(False, description="Only include tweets from Twitter Blue users")
    only_image: bool = Field(False, description="Only include tweets with images")
    only_video: bool = Field(False, description="Only include tweets with videos")
    only_quote: bool = Field(False, description="Only include quote tweets")
    include_search_terms: bool = Field(False, description="Include search terms in results")
    max_budget_usd: Optional[float] = Field(None, description="Maximum budget in USD")
    timeout_secs: int = Field(600, description="Timeout in seconds", ge=120, le=3600)

    @validator('search_terms')
    def validate_search_terms(cls, v):
        """Validate search terms."""
        cleaned_terms = []
        for term in v:
            if not term.strip() or len(term.strip()) < 2:
                raise ValueError(f"Invalid search term: {term}")
            cleaned_terms.append(term.strip())
        return cleaned_terms


class TwitterCombinedRequest(BaseModel):
    """Request model for combined Twitter handles and search terms."""
    twitter_handles: Optional[List[str]] = Field(None, description="List of Twitter handles (with or without @)")
    search_terms: Optional[List[str]] = Field(None, description="List of search terms")
    max_items: int = Field(1000, description="Maximum number of tweets to scrape", ge=1, le=5000)
    sort: str = Field("Latest", description="Sort order: Latest, Popular")
    start_date: Optional[str] = Field(None, description="Start date for tweets (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date for tweets (YYYY-MM-DD)")
    tweet_language: str = Field("en", description="Tweet language code")
    minimum_favorites: Optional[int] = Field(None, description="Minimum number of favorites/likes")
    minimum_replies: Optional[int] = Field(None, description="Minimum number of replies")
    minimum_retweets: Optional[int] = Field(None, description="Minimum number of retweets")
    only_verified_users: bool = Field(False, description="Only include tweets from verified users")
    only_twitter_blue: bool = Field(False, description="Only include tweets from Twitter Blue users")
    only_image: bool = Field(False, description="Only include tweets with images")
    only_video: bool = Field(False, description="Only include tweets with videos")
    only_quote: bool = Field(False, description="Only include quote tweets")
    include_search_terms: bool = Field(False, description="Include search terms in results")
    max_budget_usd: Optional[float] = Field(None, description="Maximum budget in USD")
    timeout_secs: int = Field(600, description="Timeout in seconds", ge=120, le=3600)

    @validator('twitter_handles')
    def validate_handles(cls, v):
        """Validate Twitter handles."""
        if v is None:
            return None
        cleaned_handles = []
        for handle in v:
            clean_handle = handle.strip().lstrip('@')
            if not clean_handle:
                raise ValueError(f"Invalid Twitter handle: {handle}")
            cleaned_handles.append(clean_handle)
        return cleaned_handles

    @validator('search_terms')
    def validate_search_terms(cls, v):
        """Validate search terms."""
        if v is None:
            return None
        cleaned_terms = []
        for term in v:
            if not term.strip() or len(term.strip()) < 2:
                raise ValueError(f"Invalid search term: {term}")
            cleaned_terms.append(term.strip())
        return cleaned_terms

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure at least one of twitter_handles or search_terms is provided
        if not self.twitter_handles and not self.search_terms:
            raise ValueError("At least one of twitter_handles or search_terms must be provided")


class FacebookRequest(BaseModel):
    """Request model for Facebook posts scraping."""
    page_urls: List[str] = Field(..., description="List of Facebook page URLs to scrape posts from", min_items=1, max_items=50)
    results_limit: int = Field(50, description="Maximum number of results to collect total", ge=1, le=200)
    max_request_retries: int = Field(10, description="Maximum number of retries per request", ge=1, le=20)
    proxy_configuration: Optional[Dict[str, Any]] = Field(None, description="Optional proxy configuration")
    max_budget_usd: Optional[float] = Field(None, description="Maximum budget in USD")
    timeout_secs: int = Field(600, description="Timeout in seconds", ge=120, le=3600)

    @validator('page_urls')
    def validate_page_urls(cls, v):
        """Validate Facebook page URLs."""
        cleaned_urls = []
        for url in v:
            if not url.strip():
                raise ValueError(f"Invalid Facebook page URL: {url}")
            cleaned_urls.append(url.strip())
        return cleaned_urls


class ActorResponse(BaseModel):
    """Standard response model for actor results."""
    success: bool = Field(..., description="Whether the operation was successful")
    data: List[Any] = Field(..., description="Retrieved data")
    metadata: Dict[str, Any] = Field(..., description="Run metadata including costs and timing")
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


@router.post("/twitter/handles", response_model=ActorResponse, tags=["Social"])
async def scrape_twitter_handles(
    request: TwitterHandlesRequest,
    background_tasks: BackgroundTasks
) -> ActorResponse:
    """
    Scrape tweets from specific Twitter handles/users.
    
    **Actor:** Twitter/X Scraper (61RPP7dywgiy0JPD0)  
    **Cost:** Pay-per-use  
    **Search Method:** Twitter handles
    
    **Features:**
    - Tweet content and engagement metrics
    - Author information and metadata
    - Filtering by engagement, verified status, media type
    - Date range filtering
    - Language filtering
    
    **Returns:** Tweet data with full metadata.
    """
    request_id = str(uuid.uuid4())
    log = logger.bind(request_id=request_id, handle_count=len(request.twitter_handles))
    
    log.info("Starting Twitter handles scraping")
    start_time = time.time()
    
    try:
        actor = TwitterActor()
        
        # Execute scraping
        result = await actor.scrape_tweets(
            twitter_handles=request.twitter_handles,
            search_terms=None,
            max_items=request.max_items,
            sort=request.sort,
            start_date=request.start_date,
            end_date=request.end_date,
            tweet_language=request.tweet_language,
            minimum_favorites=request.minimum_favorites,
            minimum_replies=request.minimum_replies,
            minimum_retweets=request.minimum_retweets,
            only_verified_users=request.only_verified_users,
            only_twitter_blue=request.only_twitter_blue,
            only_image=request.only_image,
            only_video=request.only_video,
            only_quote=request.only_quote,
            include_search_terms=False,
            max_budget_usd=request.max_budget_usd,
            timeout_secs=request.timeout_secs
        )
        
        execution_time = time.time() - start_time
        log.info(
            "Twitter handles scraping completed",
            execution_time=execution_time,
            tweets_retrieved=len(result['data']) if result['data'] else 0
        )
        
        return ActorResponse(
            success=True,
            data=result['data'] or [],
            metadata={
                **(result['metadata'].__dict__ if hasattr(result['metadata'], '__dict__') else result['metadata']),
                'execution_time': execution_time,
                'actor_id': '61RPP7dywgiy0JPD0',
                'actor_name': 'Twitter/X Scraper',
                'search_method': 'handles'
            },
            request_id=request_id
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "Twitter handles scraping failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"Twitter handles scraping failed: {str(e)}"
        )


@router.post("/twitter/search", response_model=ActorResponse, tags=["Social"])
async def scrape_twitter_search(
    request: TwitterSearchRequest,
    background_tasks: BackgroundTasks
) -> ActorResponse:
    """
    Scrape tweets based on search terms.
    
    **Actor:** Twitter/X Scraper (61RPP7dywgiy0JPD0)  
    **Cost:** Pay-per-use  
    **Search Method:** Search terms
    
    **Features:**
    - Content-based tweet discovery
    - Advanced search operators support
    - Real-time and historical data
    - Engagement and metadata filtering
    - Multiple search terms combination
    
    **Returns:** Tweet data matching search criteria.
    """
    request_id = str(uuid.uuid4())
    log = logger.bind(request_id=request_id, search_count=len(request.search_terms))
    
    log.info("Starting Twitter search scraping")
    start_time = time.time()
    
    try:
        actor = TwitterActor()
        
        # Execute scraping
        result = await actor.scrape_tweets(
            twitter_handles=None,
            search_terms=request.search_terms,
            max_items=request.max_items,
            sort=request.sort,
            start_date=request.start_date,
            end_date=request.end_date,
            tweet_language=request.tweet_language,
            minimum_favorites=request.minimum_favorites,
            minimum_replies=request.minimum_replies,
            minimum_retweets=request.minimum_retweets,
            only_verified_users=request.only_verified_users,
            only_twitter_blue=request.only_twitter_blue,
            only_image=request.only_image,
            only_video=request.only_video,
            only_quote=request.only_quote,
            include_search_terms=request.include_search_terms,
            max_budget_usd=request.max_budget_usd,
            timeout_secs=request.timeout_secs
        )
        
        execution_time = time.time() - start_time
        log.info(
            "Twitter search scraping completed",
            execution_time=execution_time,
            tweets_retrieved=len(result['data']) if result['data'] else 0
        )
        
        return ActorResponse(
            success=True,
            data=result['data'] or [],
            metadata={
                **(result['metadata'].__dict__ if hasattr(result['metadata'], '__dict__') else result['metadata']),
                'execution_time': execution_time,
                'actor_id': '61RPP7dywgiy0JPD0',
                'actor_name': 'Twitter/X Scraper',
                'search_method': 'search_terms'
            },
            request_id=request_id
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "Twitter search scraping failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"Twitter search scraping failed: {str(e)}"
        )


@router.post("/twitter/combined", response_model=ActorResponse, tags=["Social"])
async def scrape_twitter_combined(
    request: TwitterCombinedRequest,
    background_tasks: BackgroundTasks
) -> ActorResponse:
    """
    Scrape tweets using both Twitter handles and search terms.
    
    **Actor:** Twitter/X Scraper (61RPP7dywgiy0JPD0)  
    **Cost:** Pay-per-use  
    **Search Method:** Combined handles and search terms
    
    **Features:**
    - Targeted user content with keyword filtering
    - Comprehensive data collection
    - Advanced filtering options
    - Flexible search combinations
    
    **Returns:** Combined tweet data from both sources.
    """
    request_id = str(uuid.uuid4())
    log = logger.bind(
        request_id=request_id,
        handle_count=len(request.twitter_handles) if request.twitter_handles else 0,
        search_count=len(request.search_terms) if request.search_terms else 0
    )
    
    log.info("Starting combined Twitter scraping")
    start_time = time.time()
    
    try:
        actor = TwitterActor()
        
        # Execute scraping
        result = await actor.scrape_tweets(
            twitter_handles=request.twitter_handles,
            search_terms=request.search_terms,
            max_items=request.max_items,
            sort=request.sort,
            start_date=request.start_date,
            end_date=request.end_date,
            tweet_language=request.tweet_language,
            minimum_favorites=request.minimum_favorites,
            minimum_replies=request.minimum_replies,
            minimum_retweets=request.minimum_retweets,
            only_verified_users=request.only_verified_users,
            only_twitter_blue=request.only_twitter_blue,
            only_image=request.only_image,
            only_video=request.only_video,
            only_quote=request.only_quote,
            include_search_terms=request.include_search_terms,
            max_budget_usd=request.max_budget_usd,
            timeout_secs=request.timeout_secs
        )
        
        execution_time = time.time() - start_time
        log.info(
            "Combined Twitter scraping completed",
            execution_time=execution_time,
            tweets_retrieved=len(result['data']) if result['data'] else 0
        )
        
        return ActorResponse(
            success=True,
            data=result['data'] or [],
            metadata={
                **(result['metadata'].__dict__ if hasattr(result['metadata'], '__dict__') else result['metadata']),
                'execution_time': execution_time,
                'actor_id': '61RPP7dywgiy0JPD0',
                'actor_name': 'Twitter/X Scraper',
                'search_method': 'combined'
            },
            request_id=request_id
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "Combined Twitter scraping failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"Combined Twitter scraping failed: {str(e)}"
        )


@router.post("/facebook", response_model=ActorResponse, tags=["Social"])
async def scrape_facebook_posts(
    request: FacebookRequest,
    background_tasks: BackgroundTasks
) -> ActorResponse:
    """
    Scrape Facebook posts from one or more Facebook pages.
    
    **Actor:** Facebook Posts Scraper (KoJrdxJCTtpon81KY)  
    **Cost:** Pay-per-use  
    **Input Types:** Facebook page URLs
    
    **Features:**
    - Post content and engagement metrics (likes, comments, shares)
    - Post metadata (timestamps, URLs, IDs)
    - Page information (name, ID)
    - Media content detection (images, videos)
    - Complete post text and links
    
    **Returns:** Raw Facebook post data with engagement metrics.
    """
    request_id = str(uuid.uuid4())
    log = logger.bind(request_id=request_id, page_count=len(request.page_urls))
    
    log.info("Starting Facebook posts scraping")
    start_time = time.time()
    
    try:
        actor = FacebookActor()
        
        # Execute scraping
        result = await actor.scrape_posts(
            page_urls=request.page_urls,
            results_limit=request.results_limit,
            proxy_configuration=request.proxy_configuration,
            max_request_retries=request.max_request_retries,
            max_budget_usd=request.max_budget_usd,
            timeout_secs=request.timeout_secs
        )
        
        execution_time = time.time() - start_time
        log.info(
            "Facebook posts scraping completed",
            execution_time=execution_time,
            posts_retrieved=len(result) if result else 0
        )
        
        return ActorResponse(
            success=True,
            data=result or [],
            metadata={
                'execution_time': execution_time,
                'actor_id': 'KoJrdxJCTtpon81KY',
                'actor_name': 'Facebook Posts Scraper',
                'posts_found': len(result) if result else 0,
                'pages_processed': len(request.page_urls)
            },
            request_id=request_id
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        log.error(
            "Facebook posts scraping failed",
            error=str(e),
            execution_time=execution_time
        )
        raise HTTPException(
            status_code=500,
            detail=f"Facebook posts scraping failed: {str(e)}"
        )


@router.get("/twitter/pricing", tags=["Social"])
async def get_twitter_pricing() -> Dict[str, Any]:
    """
    Get current pricing information for Twitter/X actor.
    
    **Returns:** Pricing details for Twitter/X scraping services.
    """
    return {
        "twitter_actor": {
            "actor_id": "61RPP7dywgiy0JPD0",
            "cost_model": "Pay-per-use",
            "currency": "USD",
            "search_types": ["handles", "search_terms", "combined"],
            "max_items_per_run": 5000,
            "estimated_runtime_per_tweet": "0.1-0.5 seconds",
            "filtering_options": [
                "date_range", "language", "engagement_metrics",
                "verified_users", "twitter_blue", "media_type"
            ]
        }
    }


@router.get("/facebook/pricing", tags=["Social"])
async def get_facebook_pricing() -> Dict[str, Any]:
    """
    Get current pricing information for Facebook Posts Scraper actor.
    
    **Returns:** Pricing details for Facebook posts scraping services.
    """
    return {
        "facebook_actor": {
            "actor_id": "KoJrdxJCTtpon81KY",
            "cost_model": "Pay-per-use",
            "currency": "USD",
            "input_types": ["Facebook page URLs"],
            "max_results_per_run": 200,
            "estimated_runtime_per_post": "0.5-2 seconds",
            "features": [
                "Post content and engagement metrics",
                "Page information (name, ID)",
                "Post metadata (timestamps, URLs, IDs)",
                "Media content detection",
                "Like, comment, and share counts",
                "Complete post text and links"
            ],
            "proxy_support": "Residential proxy recommended"
        }
    }


@router.get("/test", tags=["Social"])
async def test_social_actor(
    actor_type: str = Query(..., description="Actor type: twitter-handles, twitter-search, twitter-combined, or facebook"),
    sample_size: int = Query(1, description="Number of sample items to test", ge=1, le=3)
) -> Dict[str, Any]:
    """
    Test social media actors with predefined sample data.
    
    **Parameters:**
    - `actor_type`: Type of actor to test
    - `sample_size`: Number of sample items to process (1-3)
    
    **Returns:** Test results with sample data.
    """
    test_data = {
        "twitter-handles": {
            "handles": ["elonmusk", "apify", "openai"],
            "max_items": 5
        },
        "twitter-search": {
            "search_terms": ["web scraping", "AI automation"],
            "max_items": 5
        },
        "twitter-combined": {
            "handles": ["apify"],
            "search_terms": ["web scraping"],
            "max_items": 3
        },
        "facebook": {
            "page_urls": ["https://www.facebook.com/nytimes", "https://www.facebook.com/microsoft"],
            "results_limit": 10
        }
    }
    
    if actor_type not in test_data:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid actor type. Must be one of: {list(test_data.keys())}"
        )
    
    sample_data = test_data[actor_type]
    
    try:
        if actor_type == "twitter-handles":
            handles = sample_data["handles"][:sample_size]
            request = TwitterHandlesRequest(
                twitter_handles=handles,
                max_items=sample_data["max_items"],
                timeout_secs=180
            )
            result = await scrape_twitter_handles(request, BackgroundTasks())
        elif actor_type == "twitter-search":
            terms = sample_data["search_terms"][:sample_size]
            request = TwitterSearchRequest(
                search_terms=terms,
                max_items=sample_data["max_items"],
                timeout_secs=180
            )
            result = await scrape_twitter_search(request, BackgroundTasks())
        elif actor_type == "twitter-combined":
            request = TwitterCombinedRequest(
                twitter_handles=sample_data["handles"],
                search_terms=sample_data["search_terms"],
                max_items=sample_data["max_items"],
                timeout_secs=180
            )
            result = await scrape_twitter_combined(request, BackgroundTasks())
        elif actor_type == "facebook":
            page_urls = sample_data["page_urls"][:sample_size]
            request = FacebookRequest(
                page_urls=page_urls,
                results_limit=sample_data["results_limit"],
                timeout_secs=300
            )
            result = await scrape_facebook_posts(request, BackgroundTasks())
        
        return {
            "test_type": actor_type,
            "sample_data": sample_data,
            "success": result.success,
            "items_retrieved": len(result.data),
            "execution_time": result.metadata.get('execution_time'),
            "cost": result.metadata.get('cost_usd', 0),
            "sample_results": result.data[:2] if result.data else []  # Return first 2 results
        }
        
    except Exception as e:
        return {
            "test_type": actor_type,
            "sample_data": sample_data,
            "success": False,
            "error": str(e)
        } 