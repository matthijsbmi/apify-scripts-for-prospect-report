"""
ZoomInfo Scraper actor implementation.

Integration with the ZoomInfo Scraper Apify actor (C6OyLbP5ixnfc5lYe).
Extracts comprehensive company data from ZoomInfo including financial info, employees, and similar companies.
"""

import logging
from typing import Any, Dict, List, Optional, Union

import structlog

from app.actors.base import BaseActor, ActorRunOptions, ActorRunResult
from app.actors.company.validators import (
    is_valid_company_name, normalize_company_name,
    is_valid_website_url, normalize_website_url
)



logger = structlog.get_logger(__name__)


class ZoomInfoActor(BaseActor):
    """
    Integration with ZoomInfo Scraper actor.
    
    Actor ID: C6OyLbP5ixnfc5lYe
    
    Scrapes company data from ZoomInfo platform using either:
    - ZoomInfo company URLs (e.g., https://www.zoominfo.com/c/walmart-inc/155353090)  
    - Company names (e.g., "walmart", "amazon")
    
    Returns comprehensive company information including financials, employees, 
    similar companies, funding history, and social network URLs.
    """
    
    def __init__(self):
        """Initialize the ZoomInfo Scraper actor."""
        super().__init__("C6OyLbP5ixnfc5lYe")
    
    async def scrape_companies(
        self,
        urls_or_names: List[str],
        include_similar_companies: bool = True,
        max_retries_per_url: int = 2,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 300,
    ) -> List[Dict[str, Any]]:
        """
        Scrape company data from ZoomInfo using URLs or company names.
        
        Args:
            urls_or_names: List of ZoomInfo URLs or company names to scrape.
                          Examples: 
                          - URLs: ["https://www.zoominfo.com/c/walmart-inc/155353090"]
                          - Names: ["walmart", "amazon", "microsoft"]
            include_similar_companies: Whether to include similar companies data.
            max_retries_per_url: Maximum number of retries for each URL/name.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD.
            timeout_secs: Timeout in seconds.
            
        Returns:
            List of raw company data dictionaries exactly as returned by the ZoomInfo actor.
            
        Raises:
            ValueError: If no valid URLs or company names are provided.
        """
        # Validate inputs
        if not urls_or_names:
            raise ValueError("At least one URL or company name must be provided")
        
        # Validate and normalize input
        validated_inputs = []
        for item in urls_or_names:
            item_str = str(item).strip()
            if not item_str:
                continue
                
            # Check if it's a ZoomInfo URL
            if "zoominfo.com/c/" in item_str.lower():
                validated_inputs.append(item_str)
            # Check if it's a valid website URL (convert to company name)
            elif is_valid_website_url(item_str):
                # Extract domain from URL and treat as company name
                if "://" in item_str:
                    domain = item_str.split("://")[1].split("/")[0]
                    domain = domain.replace("www.", "")
                    validated_inputs.append(domain.split(".")[0])  # Get company name from domain
                else:
                    validated_inputs.append(item_str)
            # Check if it's a company name
            elif is_valid_company_name(item_str):
                normalized_name = normalize_company_name(item_str)
                if normalized_name:
                    validated_inputs.append(normalized_name)
            else:
                # Treat as company name/identifier anyway
                validated_inputs.append(item_str)
        
        if not validated_inputs:
            raise ValueError("No valid URLs or company names provided")
        
        log = logger.bind(
            actor="zoominfo_scraper",
            inputs_count=len(validated_inputs)
        )
        log.info("Scraping ZoomInfo company data")
        
        # Prepare input according to ZoomInfo actor specification
        input_data = {
            "urls_or_companies_names": validated_inputs,
            "include_similar_companies": include_similar_companies,
            "max_retries_per_url": max_retries_per_url,
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
        
        # Return exact raw data from actor (no wrapping)
        if result and result.items and len(result.items) > 0:
            log.info(
                "Successfully scraped ZoomInfo data",
                companies_found=len(result.items)
            )
            # Return the exact raw items array from the actor
            return result.items
        else:
            log.warning("No ZoomInfo data found")
            return []
    
    async def scrape_single_company(
        self,
        url_or_name: str,
        include_similar_companies: bool = True,
        max_retries_per_url: int = 2,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape data for a single company from ZoomInfo.
        
        Args:
            url_or_name: ZoomInfo URL or company name to scrape.
                        Examples:
                        - URL: "https://www.zoominfo.com/c/walmart-inc/155353090"
                        - Name: "walmart"
            include_similar_companies: Whether to include similar companies data.
            max_retries_per_url: Maximum number of retries for the URL/name.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD.
            timeout_secs: Timeout in seconds.
            
        Returns:
            Raw company data if found, None otherwise.
            
        Raises:
            ValueError: If no valid URL or company name is provided.
        """
        # Use the multi-company method with single input
        result = await self.scrape_companies(
            urls_or_names=[url_or_name],
            include_similar_companies=include_similar_companies,
            max_retries_per_url=max_retries_per_url,
            proxy_configuration=proxy_configuration,
            max_budget_usd=max_budget_usd,
            timeout_secs=timeout_secs,
        )
        
        # Return single result from raw data
        if not result or len(result) == 0:
            return None
        
        # Return first (and should be only) company from raw items
        return result[0] 