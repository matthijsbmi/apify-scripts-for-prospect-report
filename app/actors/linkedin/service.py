"""
LinkedIn service for orchestrating LinkedIn actor integrations.

Provides a unified interface for all LinkedIn actor functionality.
"""

import logging
from typing import Any, Dict, List, Optional, Union

import structlog

from app.actors.base import ActorRunResult
from app.actors.linkedin.profile_actor import LinkedInProfileActor
from app.actors.linkedin.posts_actor import LinkedInPostsActor
from app.actors.linkedin.company_actor import LinkedInCompanyActor
from app.actors.linkedin.validators import (
    is_valid_linkedin_profile_url, is_valid_linkedin_company_url,
    is_valid_linkedin_post_url, extract_linkedin_username,
    extract_linkedin_company_id
)
from app.models.data import (
    LinkedInData, LinkedInProfile, LinkedInPost, LinkedInCompany
)


logger = structlog.get_logger(__name__)


class LinkedInService:
    """
    Service for orchestrating LinkedIn actor integrations.
    
    Provides a unified interface for all LinkedIn actor functionality.
    """
    
    def __init__(self):
        """Initialize the LinkedIn service."""
        # Initialize actors
        self.profile_actor = LinkedInProfileActor()
        self.posts_actor = LinkedInPostsActor()
        self.company_actor = LinkedInCompanyActor()
    
    async def collect_linkedin_data(
        self,
        profile_url: Optional[str] = None,
        company_url: Optional[str] = None,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        include_posts: bool = True,
        include_company: bool = True,
        max_posts: int = 10,
    ) -> LinkedInData:
        """
        Collect comprehensive LinkedIn data for a prospect.
        
        Args:
            profile_url: LinkedIn profile URL.
            company_url: LinkedIn company URL. If None and profile_url is provided,
                         will attempt to extract from profile.
            proxy_configuration: Optional proxy configuration. If None, use default.
            max_budget_usd: Maximum budget in USD. If None, no budget limit.
            include_posts: Whether to include posts data.
            include_company: Whether to include company data.
            max_posts: Maximum number of posts to collect.
            
        Returns:
            Comprehensive LinkedIn data.
            
        Raises:
            ValueError: If no valid URLs are provided.
        """
        # Initialize result
        linkedin_data = LinkedInData()
        
        # Ensure at least one valid URL
        if not profile_url and not company_url:
            raise ValueError("No LinkedIn URLs provided")
        
        if profile_url and not is_valid_linkedin_profile_url(profile_url):
            raise ValueError(f"Invalid LinkedIn profile URL: {profile_url}")
        
        if company_url and not is_valid_linkedin_company_url(company_url):
            raise ValueError(f"Invalid LinkedIn company URL: {company_url}")
        
        log = logger.bind(
            service="linkedin_service",
            profile_url=profile_url,
            company_url=company_url,
        )
        log.info("Collecting LinkedIn data")
        
        # Calculate budget distribution
        budget_distribution = self._calculate_budget_distribution(
            max_budget_usd=max_budget_usd,
            profile=bool(profile_url),
            posts=bool(profile_url) and include_posts,
            company=bool(company_url) or (bool(profile_url) and include_company),
        )
        
        # Collect profile data if provided
        if profile_url:
            profile_budget = budget_distribution.get("profile", 2.0)
            
            try:
                profile_result = await self.profile_actor.scrape_profiles(
                    profile_urls=[profile_url],
                    include_skills=True,
                    include_education=True,
                    include_experience=True,
                    proxy_configuration=proxy_configuration,
                    max_budget_usd=profile_budget,
                )
                
                profiles = profile_result["profiles"]
                if profiles:
                    linkedin_data.profile = profiles[0]
                    
                    # Extract company URL if needed and not provided
                    if not company_url and include_company and linkedin_data.profile.current_company_url:
                        company_url = linkedin_data.profile.current_company_url
            
            except Exception as e:
                log.error("Error collecting LinkedIn profile data", error=str(e))
        
        # Collect posts data if profile provided and posts requested
        if profile_url and include_posts:
            posts_budget = budget_distribution.get("posts", 1.0)
            
            try:
                posts_result = await self.posts_actor.scrape_profile_posts(
                    profile_url=profile_url,
                    max_posts=max_posts,
                    include_comments=False,
                    proxy_configuration=proxy_configuration,
                    max_budget_usd=posts_budget,
                )
                
                posts = posts_result["posts"]
                if posts:
                    linkedin_data.posts = posts
            
            except Exception as e:
                log.error("Error collecting LinkedIn posts data", error=str(e))
        
        # Collect company data if company URL provided or extracted
        if company_url and include_company:
            company_budget = budget_distribution.get("company", 3.0)
            
            try:
                company = await self.company_actor.scrape_company(
                    company_url=company_url,
                    include_jobs=False,
                    include_people=True,
                    proxy_configuration=proxy_configuration,
                    max_budget_usd=company_budget,
                )
                
                if company:
                    linkedin_data.company = company
            
            except Exception as e:
                log.error("Error collecting LinkedIn company data", error=str(e))
        
        return linkedin_data
    
    def _calculate_budget_distribution(
        self,
        max_budget_usd: Optional[float],
        profile: bool = True,
        posts: bool = True,
        company: bool = True,
    ) -> Dict[str, float]:
        """
        Calculate budget distribution among different data types.
        
        Args:
            max_budget_usd: Maximum total budget.
            profile: Whether to include profile data.
            posts: Whether to include posts data.
            company: Whether to include company data.
            
        Returns:
            Dictionary with budget allocation per data type.
        """
        # Default budgets
        default_budgets = {
            "profile": 2.0,  # $2 for profile data
            "posts": 1.0,    # $1 for posts data
            "company": 3.0,  # $3 for company data
        }
        
        # If no max budget, return defaults for requested data
        if not max_budget_usd:
            return {
                key: value
                for key, value in default_budgets.items()
                if (
                    (key == "profile" and profile) or
                    (key == "posts" and posts) or
                    (key == "company" and company)
                )
            }
        
        # Calculate total needed
        total_needed = 0
        if profile:
            total_needed += default_budgets["profile"]
        if posts:
            total_needed += default_budgets["posts"]
        if company:
            total_needed += default_budgets["company"]
        
        # If budget is sufficient, return defaults
        if max_budget_usd >= total_needed:
            return {
                key: value
                for key, value in default_budgets.items()
                if (
                    (key == "profile" and profile) or
                    (key == "posts" and posts) or
                    (key == "company" and company)
                )
            }
        
        # Otherwise, distribute proportionally
        result = {}
        weights = {}
        
        if profile:
            weights["profile"] = default_budgets["profile"]
        if posts:
            weights["posts"] = default_budgets["posts"]
        if company:
            weights["company"] = default_budgets["company"]
        
        total_weight = sum(weights.values())
        
        for key, weight in weights.items():
            result[key] = (weight / total_weight) * max_budget_usd
        
        return result
    
    async def validate_linkedin_url(
        self,
        url: str,
    ) -> Dict[str, Any]:
        """
        Validate and categorize LinkedIn URL.
        
        Args:
            url: URL to validate.
            
        Returns:
            Dictionary with validation results.
        """
        result = {
            "valid": False,
            "type": None,
            "url": url,
        }
        
        if is_valid_linkedin_profile_url(url):
            result["valid"] = True
            result["type"] = "profile"
            result["username"] = extract_linkedin_username(url)
        
        elif is_valid_linkedin_company_url(url):
            result["valid"] = True
            result["type"] = "company"
            result["company_id"] = extract_linkedin_company_id(url)
        
        elif is_valid_linkedin_post_url(url):
            result["valid"] = True
            result["type"] = "post"
        
        return result 