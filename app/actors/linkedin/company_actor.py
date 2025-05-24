"""
LinkedIn Company Profile Scraper actor implementation.

Integration with the LinkedIn Company Profile Scraper Apify actor (3rgDeYgLhr6XrVnjs).
"""

import logging
from typing import Any, Dict, List, Optional, Union

import structlog

from app.actors.base import BaseActor, ActorRunOptions, ActorRunResult
from app.actors.linkedin.validators import (
    validate_linkedin_company_urls, is_valid_linkedin_company_url
)


logger = structlog.get_logger(__name__)


class LinkedInCompanyActor(BaseActor):
    """
    Integration with LinkedIn Company Profile Scraper actor.
    
    Actor ID: sanjeta/linkedin-company-profile-scraper
    """
    
    def __init__(self):
        """Initialize the LinkedIn Company Profile Scraper actor."""
        super().__init__("sanjeta/linkedin-company-profile-scraper")
    
    async def scrape_companies(
        self,
        company_urls: List[str],
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 600,
    ) -> Dict[str, ActorRunResult]:
        """
        Scrape LinkedIn company profiles.
        
        Args:
            company_urls: List of LinkedIn company URLs (slug-based format only).
            proxy_configuration: Optional proxy configuration. If None, use default.
            max_budget_usd: Maximum budget in USD. If None, no budget limit.
            timeout_secs: Timeout in seconds.
            
        Returns:
            Dictionary with 'metadata' containing actor execution metadata and 
            raw scraped company data in metadata.items.
            
        Raises:
            ValueError: If no valid LinkedIn company URLs are provided.
        """
        # Validate URLs
        valid_urls = validate_linkedin_company_urls(company_urls)
        if not valid_urls:
            raise ValueError("No valid LinkedIn company URLs provided")
        
        log = logger.bind(
            actor="linkedin_company_scraper", 
            url_count=len(valid_urls)
        )
        log.info("Scraping LinkedIn company profiles")
        
        # Prepare input according to actor documentation
        input_data = {
            "urls": valid_urls,
            "proxy": {
                "useApifyProxy": True
            }
        }
        
        # Add proxy configuration if provided
        if proxy_configuration:
            input_data["proxy"] = proxy_configuration
        
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
        
        # Return only metadata with raw data (no duplication)
        if result and result.items and len(result.items) > 0:
            log.info(
                "Successfully scraped companies", 
                count=len(result.items)
            )
        
        return {
            "metadata": result,
        }
    
    async def scrape_company(
        self,
        company_url: str,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape a single LinkedIn company profile.
        
        Args:
            company_url: LinkedIn company URL (slug-based format only).
            proxy_configuration: Optional proxy configuration. If None, use default.
            max_budget_usd: Maximum budget in USD. If None, no budget limit.
            
        Returns:
            Raw company data if found, None otherwise.
            
        Raises:
            ValueError: If company_url is not a valid LinkedIn company URL.
        """
        # Validate URL
        if not is_valid_linkedin_company_url(company_url):
            raise ValueError(f"Invalid LinkedIn company URL: {company_url}")
        
        # Scrape company
        result = await self.scrape_companies(
            company_urls=[company_url],
            proxy_configuration=proxy_configuration,
            max_budget_usd=max_budget_usd,
        )
        
        metadata = result["metadata"]
        if not metadata or not metadata.items:
            return None
        
        # Return first (and should be only) company from raw items
        return metadata.items[0] 