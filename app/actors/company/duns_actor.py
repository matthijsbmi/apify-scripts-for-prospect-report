"""
Dun & Bradstreet Scraper actor implementation.

Integration with the Dun & Bradstreet Scraper Apify actor (RIq8Fe9BdxSR4GUXY).
"""

import logging
from typing import Any, Dict, List, Optional

import structlog

from app.actors.base import BaseActor, ActorRunOptions, ActorRunResult


logger = structlog.get_logger(__name__)


class DunsActor(BaseActor):
    """
    Integration with Dun & Bradstreet Scraper actor.
    
    Actor ID: RIq8Fe9BdxSR4GUXY
    """
    
    def __init__(self):
        """Initialize the Dun & Bradstreet Scraper actor."""
        super().__init__("RIq8Fe9BdxSR4GUXY")
    
    async def search_companies(
        self,
        search_term: str,
        revenue_min: Optional[int] = None,
        number_of_employees_min: Optional[int] = None,
        year_start_from: Optional[int] = None,
        country_in: Optional[str] = None,
        industry_in: Optional[str] = None,
        max_items: int = 10,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 600,
    ) -> List[Dict[str, Any]]:
        """
        Search for companies in Dun & Bradstreet database.
        
        Args:
            search_term: Company name or search term.
            revenue_min: Minimum revenue filter.
            number_of_employees_min: Minimum number of employees filter.
            year_start_from: Minimum year company was established.
            country_in: Countries to search in (comma-separated).
            industry_in: Industries to search in (comma-separated).
            max_items: Maximum number of companies to retrieve.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD.
            timeout_secs: Timeout in seconds.
            
        Returns:
            List of raw company data dictionaries.
            
        Raises:
            ValueError: If no search term is provided.
        """
        if not search_term or not search_term.strip():
            raise ValueError("Search term is required")
        
        log = logger.bind(
            actor="duns_scraper",
            search_term=search_term,
            max_items=max_items
        )
        log.info("Searching Dun & Bradstreet database")
        
        # Prepare input data
        input_data = {
            "searchTerm": search_term.strip(),
            "maxItems": max_items,
        }
        
        # Add optional filters
        if revenue_min is not None:
            input_data["revenueMin"] = revenue_min
            
        if number_of_employees_min is not None:
            input_data["numberOfEmployeesMin"] = number_of_employees_min
            
        if year_start_from is not None:
            input_data["yearStartFrom"] = year_start_from
            
        if country_in:
            input_data["countryIn"] = country_in
            
        if industry_in:
            input_data["industryIn"] = industry_in
        
        # Add proxy configuration (default to US proxy if none provided)
        if proxy_configuration:
            input_data["proxyConfiguration"] = proxy_configuration
        else:
            input_data["proxyConfiguration"] = {
                "useApifyProxy": True,
                "apifyProxyCountry": "US"
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
                "Successfully scraped Dun & Bradstreet data",
                companies_found=len(result.items)
            )
            return result.items
        else:
            log.warning("No Dun & Bradstreet data found")
            return []
    
    async def search_single_company(
        self,
        search_term: str,
        revenue_min: Optional[int] = None,
        number_of_employees_min: Optional[int] = None,
        year_start_from: Optional[int] = None,
        country_in: Optional[str] = None,
        industry_in: Optional[str] = None,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 600,
    ) -> Optional[Dict[str, Any]]:
        """
        Search for a single company in Dun & Bradstreet database.
        
        Args:
            search_term: Company name or search term.
            revenue_min: Minimum revenue filter.
            number_of_employees_min: Minimum number of employees filter.
            year_start_from: Minimum year company was established.
            country_in: Countries to search in (comma-separated).
            industry_in: Industries to search in (comma-separated).
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD.
            timeout_secs: Timeout in seconds.
            
        Returns:
            Raw company data dictionary or None if not found.
            
        Raises:
            ValueError: If no search term is provided.
        """
        # Use the search method with max_items=1
        results = await self.search_companies(
            search_term=search_term,
            revenue_min=revenue_min,
            number_of_employees_min=number_of_employees_min,
            year_start_from=year_start_from,
            country_in=country_in,
            industry_in=industry_in,
            max_items=1,
            proxy_configuration=proxy_configuration,
            max_budget_usd=max_budget_usd,
            timeout_secs=timeout_secs,
        )
        
        # Return first result or None
        return results[0] if results else None 