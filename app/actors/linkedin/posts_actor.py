"""
LinkedIn Posts Bulk Scraper actor implementation.

Integration with the LinkedIn Posts Bulk Scraper Apify actor (A3cAPGpwBEG8RJwse).
"""

import logging
from typing import Any, Dict, List, Optional, Union

import structlog

from app.actors.base import BaseActor, ActorRunOptions, ActorRunResult
from app.actors.linkedin.validators import (
    validate_linkedin_profile_urls, is_valid_linkedin_profile_url,
    validate_linkedin_company_urls, is_valid_linkedin_company_url
)
from app.actors.linkedin.transformers import transform_posts_data
from app.models.data import LinkedInPost


logger = structlog.get_logger(__name__)


class LinkedInPostsActor(BaseActor):
    """
    Integration with LinkedIn Posts Bulk Scraper actor.
    
    Actor ID: A3cAPGpwBEG8RJwse
    """
    
    def __init__(self):
        """Initialize the LinkedIn Posts Bulk Scraper actor."""
        super().__init__("A3cAPGpwBEG8RJwse")
    
    async def scrape_posts(
        self,
        urls: List[str],
        max_posts_per_url: int = 10,
        include_comments: bool = False,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_concurrency: int = 5,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 300,
    ) -> Dict[str, Union[List[LinkedInPost], ActorRunResult]]:
        """
        Scrape LinkedIn posts from profiles or company pages.
        
        Args:
            urls: List of LinkedIn profile or company URLs.
            max_posts_per_url: Maximum number of posts to scrape per URL.
            include_comments: Whether to include post comments.
            proxy_configuration: Optional proxy configuration. If None, use default.
            max_concurrency: Maximum concurrent requests.
            max_budget_usd: Maximum budget in USD. If None, no budget limit.
            timeout_secs: Timeout in seconds.
            
        Returns:
            Dictionary with 'posts' containing scraped post data and 
            'metadata' containing actor execution metadata.
            
        Raises:
            ValueError: If no valid LinkedIn URLs are provided.
        """
        # Validate URLs - this actor accepts both profile and company URLs
        valid_profile_urls = validate_linkedin_profile_urls(urls)
        valid_company_urls = validate_linkedin_company_urls(urls)
        valid_urls = list(set(valid_profile_urls + valid_company_urls))
        
        if not valid_urls:
            raise ValueError("No valid LinkedIn profile or company URLs provided")
        
        log = logger.bind(
            actor="linkedin_posts_scraper", 
            url_count=len(valid_urls)
        )
        log.info("Scraping LinkedIn posts")
        
        # Prepare input
        input_data = {
            "profileUrls": valid_urls,  # The actor accepts both profile and company URLs
            "maxPostsPerProfile": max_posts_per_url,
            "includeComments": include_comments,
            "maxConcurrency": max_concurrency,
        }
        
        # Add proxy configuration if provided
        if proxy_configuration:
            input_data["proxyConfiguration"] = proxy_configuration
        
        # Set options
        options = ActorRunOptions(
            timeout_secs=timeout_secs,
            memory_mbytes=1024,  # Use 1GB of memory
        )
        
        # Run actor
        result = await self.run_async(
            input_data=input_data,
            options=options,
            max_budget=max_budget_usd,
        )
        
        # Process results
        posts = []
        if result and result.items and len(result.items) > 0:
            log.info(
                "Successfully scraped posts", 
                count=len(result.items)
            )
            
            # Transform posts
            try:
                posts = transform_posts_data(result.items)
            except Exception as e:
                log.error("Error transforming posts", error=str(e))
        
        return {
            "posts": posts,
            "metadata": result,
        }
    
    async def scrape_profile_posts(
        self,
        profile_url: str,
        max_posts: int = 10,
        include_comments: bool = False,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
    ) -> Dict[str, Union[List[LinkedInPost], ActorRunResult]]:
        """
        Scrape posts from a LinkedIn profile.
        
        Args:
            profile_url: LinkedIn profile URL.
            max_posts: Maximum number of posts to scrape.
            include_comments: Whether to include post comments.
            proxy_configuration: Optional proxy configuration. If None, use default.
            max_budget_usd: Maximum budget in USD. If None, no budget limit.
            
        Returns:
            Dictionary with 'posts' containing scraped post data and 
            'metadata' containing actor execution metadata.
            
        Raises:
            ValueError: If profile_url is not a valid LinkedIn profile URL.
        """
        # Validate URL
        if not is_valid_linkedin_profile_url(profile_url):
            raise ValueError(f"Invalid LinkedIn profile URL: {profile_url}")
        
        # Delegate to general method
        return await self.scrape_posts(
            urls=[profile_url],
            max_posts_per_url=max_posts,
            include_comments=include_comments,
            proxy_configuration=proxy_configuration,
            max_budget_usd=max_budget_usd,
        )
    
    async def scrape_company_posts(
        self,
        company_url: str,
        max_posts: int = 10,
        include_comments: bool = False,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
    ) -> Dict[str, Union[List[LinkedInPost], ActorRunResult]]:
        """
        Scrape posts from a LinkedIn company page.
        
        Args:
            company_url: LinkedIn company URL.
            max_posts: Maximum number of posts to scrape.
            include_comments: Whether to include post comments.
            proxy_configuration: Optional proxy configuration. If None, use default.
            max_budget_usd: Maximum budget in USD. If None, no budget limit.
            
        Returns:
            Dictionary with 'posts' containing scraped post data and 
            'metadata' containing actor execution metadata.
            
        Raises:
            ValueError: If company_url is not a valid LinkedIn company URL.
        """
        # Validate URL
        if not is_valid_linkedin_company_url(company_url):
            raise ValueError(f"Invalid LinkedIn company URL: {company_url}")
        
        # Delegate to general method
        return await self.scrape_posts(
            urls=[company_url],
            max_posts_per_url=max_posts,
            include_comments=include_comments,
            proxy_configuration=proxy_configuration,
            max_budget_usd=max_budget_usd,
        )