"""
LinkedIn Profile Bulk Scraper actor implementation.

Integration with the LinkedIn Profile Bulk Scraper Apify actor (LpVuK3Zozwuipa5bp).
"""

import logging
from typing import Any, Dict, List, Optional, Union

import structlog

from app.actors.base import BaseActor, ActorRunOptions, ActorRunResult
from app.actors.linkedin.validators import (
    validate_linkedin_profile_urls, is_valid_linkedin_profile_url
)
from app.actors.linkedin.transformers import transform_profile_data
from app.models.data import LinkedInProfile


logger = structlog.get_logger(__name__)


class LinkedInProfileActor(BaseActor):
    """
    Integration with LinkedIn Profile Bulk Scraper actor.
    
    Actor ID: LpVuK3Zozwuipa5bp
    """
    
    def __init__(self):
        """Initialize the LinkedIn Profile Bulk Scraper actor."""
        super().__init__("LpVuK3Zozwuipa5bp")
    
    async def scrape_profiles(
        self,
        profile_urls: List[str],
        include_skills: bool = True,
        include_education: bool = True,
        include_experience: bool = True,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_concurrency: int = 5,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 600,
    ) -> Dict[str, Union[List[LinkedInProfile], ActorRunResult]]:
        """
        Scrape LinkedIn profiles.
        
        Args:
            profile_urls: List of LinkedIn profile URLs.
            include_skills: Whether to include skills section.
            include_education: Whether to include education section.
            include_experience: Whether to include experience section.
            proxy_configuration: Optional proxy configuration. If None, use default.
            max_concurrency: Maximum concurrent requests.
            max_budget_usd: Maximum budget in USD. If None, no budget limit.
            timeout_secs: Timeout in seconds.
            
        Returns:
            Dictionary with 'profiles' containing scraped profile data and 
            'metadata' containing actor execution metadata.
            
        Raises:
            ValueError: If no valid LinkedIn profile URLs are provided.
        """
        # Validate URLs
        valid_urls = validate_linkedin_profile_urls(profile_urls)
        if not valid_urls:
            raise ValueError("No valid LinkedIn profile URLs provided")
        
        log = logger.bind(
            actor="linkedin_profile_scraper", 
            url_count=len(valid_urls)
        )
        log.info("Scraping LinkedIn profiles")
        
        # Prepare input
        input_data = {
            "profileUrls": valid_urls,
            "includeSkills": include_skills,
            "includeEducation": include_education,
            "includeExperience": include_experience,
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
        profiles = []
        if result and result.items and len(result.items) > 0:
            log.info(
                "Successfully scraped profiles", 
                count=len(result.items)
            )
            
            # Transform profiles
            for item in result.items:
                try:
                    profile = transform_profile_data(item)
                    profiles.append(profile)
                except Exception as e:
                    log.error(
                        "Error transforming profile", 
                        url=item.get("profileUrl", "unknown"),
                        error=str(e)
                    )
        
        return {
            "profiles": profiles,
            "metadata": result,
        }
    
    async def get_company_url_from_profile(
        self,
        profile_url: str,
        proxy_configuration: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Extract company URL from a LinkedIn profile.
        
        Args:
            profile_url: LinkedIn profile URL.
            proxy_configuration: Optional proxy configuration. If None, use default.
            
        Returns:
            Company URL if found, None otherwise.
            
        Raises:
            ValueError: If profile_url is not a valid LinkedIn profile URL.
        """
        # Validate URL
        if not is_valid_linkedin_profile_url(profile_url):
            raise ValueError(f"Invalid LinkedIn profile URL: {profile_url}")
        
        # Scrape profile
        result = await self.scrape_profiles(
            profile_urls=[profile_url],
            include_skills=False,
            include_education=False,
            include_experience=True,
            proxy_configuration=proxy_configuration,
            max_budget_usd=2.0,  # Small budget is sufficient
        )
        
        profiles = result["profiles"]
        if not profiles:
            return None
        
        # Get the first profile
        profile = profiles[0]
        
        # Return company URL if available
        return profile.current_company_url 