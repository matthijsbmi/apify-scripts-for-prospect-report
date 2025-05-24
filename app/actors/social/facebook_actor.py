"""
Facebook Posts Scraper actor implementation.

Integration with the Facebook Posts Scraper Apify actor (KoJrdxJCTtpon81KY).
"""

import logging
from typing import Any, Dict, List, Optional, Union

import structlog

from app.actors.base import BaseActor, ActorRunOptions, ActorRunResult


logger = structlog.get_logger(__name__)


class FacebookActor(BaseActor):
    """
    Integration with Facebook Posts Scraper actor.
    
    Actor ID: KoJrdxJCTtpon81KY
    """
    
    def __init__(self):
        """Initialize the Facebook Posts Scraper actor."""
        super().__init__("KoJrdxJCTtpon81KY")
    
    async def scrape_posts(
        self,
        page_urls: List[str],
        results_limit: int = 50,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_request_retries: int = 10,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 600,
    ) -> List[Dict[str, Any]]:
        """
        Scrape Facebook posts from one or more Facebook pages.
        
        Args:
            page_urls: List of Facebook page URLs to scrape.
            results_limit: Maximum number of results to collect total.
            proxy_configuration: Optional proxy configuration. If None, uses default residential proxy.
            max_request_retries: Maximum number of retries per request.
            max_budget_usd: Maximum budget in USD. If None, no budget limit.
            timeout_secs: Timeout in seconds.
            
        Returns:
            List of raw Facebook post data dictionaries.
            
        Raises:
            ValueError: If no valid page URLs are provided.
        """
        if not page_urls:
            raise ValueError("No Facebook page URLs provided")
        
        log = logger.bind(
            actor="facebook_posts_scraper", 
            url_count=len(page_urls)
        )
        log.info("Scraping Facebook posts")
        
        # Prepare startUrls format
        start_urls = [{"url": url} for url in page_urls]
        
        # Prepare input with default proxy configuration
        input_data = {
            "startUrls": start_urls,
            "resultsLimit": results_limit,
            "maxRequestRetries": max_request_retries,
        }
        
        # Add proxy configuration (default to residential proxy if none provided)
        if proxy_configuration:
            input_data["proxy"] = proxy_configuration
        else:
            input_data["proxy"] = {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"]
            }
        
        # Set options
        options = ActorRunOptions(
            timeout_secs=timeout_secs,
            memory_mbytes=2048,  # Use 2GB of memory
        )
        
        # Run actor
        result = await self.run_async(
            input_data=input_data,
            options=options,
            max_budget=max_budget_usd,
        )
        
        # Return raw data
        if result and result.items:
            log.info(
                "Successfully scraped Facebook posts", 
                item_count=len(result.items)
            )
            return result.items
        else:
            log.warning("No Facebook posts found")
            return []
    
    async def scrape_single_page(
        self,
        page_url: str,
        results_limit: int = 50,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_request_retries: int = 10,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 600,
    ) -> List[Dict[str, Any]]:
        """
        Scrape Facebook posts from a single Facebook page.
        
        Args:
            page_url: Facebook page URL to scrape.
            results_limit: Maximum number of results to collect.
            proxy_configuration: Optional proxy configuration. If None, uses default residential proxy.
            max_request_retries: Maximum number of retries per request.
            max_budget_usd: Maximum budget in USD. If None, no budget limit.
            timeout_secs: Timeout in seconds.
            
        Returns:
            List of raw Facebook post data dictionaries.
            
        Raises:
            ValueError: If no page URL is provided.
        """
        if not page_url:
            raise ValueError("No Facebook page URL provided")
        
        return await self.scrape_posts(
            page_urls=[page_url],
            results_limit=results_limit,
            proxy_configuration=proxy_configuration,
            max_request_retries=max_request_retries,
            max_budget_usd=max_budget_usd,
            timeout_secs=timeout_secs
        ) 