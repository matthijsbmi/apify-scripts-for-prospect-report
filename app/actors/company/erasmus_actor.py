"""
Erasmus+ Organisation Scraper actor implementation.

Integration with the Erasmus+ Organisation Scraper Apify actor (5ms6D6gKCnJhZN61e).
"""

import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import structlog

from app.actors.base import BaseActor, ActorRunOptions, ActorRunResult
from app.actors.company.validators import (
    is_valid_company_name, normalize_company_name
)
from app.actors.company.transformers import transform_erasmus_data
from app.models.data import CompanyData


logger = structlog.get_logger(__name__)


class ErasmusActor(BaseActor):
    """
    Integration with Erasmus+ Organisation Scraper actor.
    
    Actor ID: 5ms6D6gKCnJhZN61e
    """
    
    def __init__(self):
        """Initialize the Erasmus+ Organisation Scraper actor."""
        super().__init__("5ms6D6gKCnJhZN61e")
    
    def clean_domain(self, domain_input: str) -> str:
        """
        Clean domain input by removing protocols, paths, and query parameters.
        
        Args:
            domain_input: Raw domain input (may include http/https, paths, etc.)
            
        Returns:
            Clean domain name only
        """
        # If it doesn't start with http/https, add https for parsing
        if not domain_input.startswith(('http://', 'https://')):
            domain_input = f"https://{domain_input}"
        
        # Parse the URL
        parsed = urlparse(domain_input)
        
        # Extract just the domain (netloc)
        domain = parsed.netloc
        
        return domain
    
    async def scrape_organizations(
        self,
        organization_ids: Optional[List[str]] = None,
        organization_names: Optional[List[str]] = None,
        website_domain: Optional[str] = None,
        max_results: int = 50,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 180,
    ) -> Dict[str, Union[List[CompanyData], ActorRunResult]]:
        """
        Scrape organization data from Erasmus+ database.
        
        Args:
            organization_ids: List of organization identifiers to search.
            organization_names: List of organization names to search.
            website_domain: Website domain to search for organizations.
            max_results: Maximum number of results.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD.
            timeout_secs: Timeout in seconds.
            
        Returns:
            Dictionary with 'data' containing list of CompanyData and 'metadata' containing ActorRunResult.
            
        Raises:
            ValueError: If no valid search parameters are provided.
        """
        # Validate inputs - need at least one search parameter
        if not organization_ids and not organization_names and not website_domain:
            raise ValueError("Either organization IDs, organization names, or website domain must be provided")
        
        # Validate and normalize organization IDs
        validated_ids = []
        if organization_ids:
            for org_id in organization_ids:
                org_id_str = str(org_id).strip()
                if org_id_str:
                    validated_ids.append(org_id_str)
        
        # Normalize organization names
        normalized_names = []
        if organization_names:
            for name in organization_names:
                normalized = normalize_company_name(name)
                if normalized:
                    normalized_names.append(normalized)
        
        # Clean website domain if provided
        cleaned_domain = None
        if website_domain:
            cleaned_domain = self.clean_domain(website_domain)
        
        # Ensure at least one valid search parameter
        if not validated_ids and not normalized_names and not cleaned_domain:
            raise ValueError("No valid organization identifiers, names, or domain provided")
        
        log = logger.bind(
            actor="erasmus_scraper",
            ids_count=len(validated_ids) if validated_ids else 0,
            names_count=len(normalized_names) if normalized_names else 0,
            website_domain=website_domain
        )
        log.info("Scraping Erasmus+ organization data")
        
        # Prepare input
        input_data = {
            "maxResults": max_results,
            "searchTerms": [],
            "debugMode": False,
        }
        
        # Add organization IDs if provided
        if validated_ids:
            input_data["organizationIds"] = validated_ids
        
        # Add organization names if provided
        if normalized_names:
            input_data["organizationNames"] = normalized_names
            
        # Add website domain if provided
        if cleaned_domain:
            input_data["websiteName"] = cleaned_domain
        
        # Add proxy configuration if provided
        if proxy_configuration:
            input_data["proxyConfiguration"] = proxy_configuration
        else:
            # Default proxy configuration
            input_data["proxyConfiguration"] = {
                "useApifyProxy": True
            }
        
        # Set options
        options = ActorRunOptions(
            timeout_secs=timeout_secs,
            memory_mbytes=512,  # Use 512MB of memory
        )
        
        # Run actor
        result = await self.run_async(
            input_data=input_data,
            options=options,
            max_budget=max_budget_usd,
        )
        
        # Process results
        company_data_list = []
        if result and result.items and len(result.items) > 0:
            log.info(
                "Successfully scraped Erasmus+ data",
                organizations_found=len(result.items),
                search_type="domain" if cleaned_domain else "name/id"
            )
            
            # Transform each organization
            for item in result.items:
                try:
                    company_data = transform_erasmus_data(item)
                    company_data_list.append(company_data)
                except Exception as e:
                    log.error(
                        "Error transforming Erasmus+ data",
                        organization=item.get("name", "unknown"),
                        error=str(e)
                    )
                    # Add basic CompanyData with error info
                    company_data_list.append(CompanyData(
                        name=item.get("name", "Unknown Organization"),
                        sources=["erasmus"],
                        funding={"error": str(e)},
                    ))
        else:
            log.warning("No Erasmus+ data found")
        
        return {
            "data": company_data_list,
            "metadata": result,
        }
    
    async def scrape_single_organization(
        self,
        organization_id: Optional[str] = None,
        organization_name: Optional[str] = None,
        website_domain: Optional[str] = None,
        max_results: int = 50,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 180,
    ) -> Dict[str, Union[CompanyData, ActorRunResult]]:
        """
        Scrape data for a single organization from Erasmus+ database.
        
        Args:
            organization_id: Organization identifier to search.
            organization_name: Organization name to search.
            website_domain: Website domain to search for organization.
            max_results: Maximum number of results.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD.
            timeout_secs: Timeout in seconds.
            
        Returns:
            Dictionary with 'data' containing CompanyData and 'metadata' containing ActorRunResult.
            
        Raises:
            ValueError: If no valid search parameter is provided.
        """
        # Convert single inputs to lists
        organization_ids = [organization_id] if organization_id else None
        organization_names = [organization_name] if organization_name else None
        
        # Use the multi-organization method
        result = await self.scrape_organizations(
            organization_ids=organization_ids,
            organization_names=organization_names,
            website_domain=website_domain,
            max_results=max_results,
            proxy_configuration=proxy_configuration,
            max_budget_usd=max_budget_usd,
            timeout_secs=timeout_secs,
        )
        
        # Return single result
        name = organization_name or website_domain or "Unknown Organization"
        company_data = result["data"][0] if result["data"] else CompanyData(
            name=name,
            sources=["erasmus"],
        )
        
        return {
            "data": company_data,
            "metadata": result["metadata"],
        }
        
    async def scrape_by_domain(
        self,
        website_domain: str,
        max_results: int = 50,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 300,  # Longer timeout for domain searches
    ) -> Dict[str, Union[List[CompanyData], ActorRunResult]]:
        """
        Scrape organization data from Erasmus+ database by website domain.
        
        This is a specialized method for domain-based searches, which we found
        to be particularly effective for the Erasmus+ Organisation Scraper.
        
        Args:
            website_domain: Website domain to search for.
            max_results: Maximum number of results.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD.
            timeout_secs: Timeout in seconds.
            
        Returns:
            Dictionary with 'data' containing list of CompanyData and 'metadata' containing ActorRunResult.
        """
        return await self.scrape_organizations(
            website_domain=website_domain,
            max_results=max_results,
            proxy_configuration=proxy_configuration,
            max_budget_usd=max_budget_usd,
            timeout_secs=timeout_secs,
        ) 