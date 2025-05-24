"""
LinkedIn Posts Bulk Scraper implementation.

This module provides the LinkedInPostsScraper class for scraping LinkedIn posts.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
import structlog

from app.core.apify_client import ApifyService
from app.cost.manager import CostManager
from app.core.config import settings

logger = structlog.get_logger(__name__)


class LinkedInPostsScraper:
    """
    LinkedIn Posts Bulk Scraper wrapper class.
    
    This class provides a simplified interface for the LinkedIn Posts Bulk Scraper
    that handles post scraping from LinkedIn profiles.
    """
    
    def __init__(self, apify_service: ApifyService, cost_manager: CostManager):
        """
        Initialize the LinkedIn Posts Scraper.
        
        Args:
            apify_service: Apify service instance
            cost_manager: Cost manager instance
        """
        self.apify_service = apify_service
        self.cost_manager = cost_manager
        self.actor_id = "A3cAPGpwBEG8RJwse"
        self.name = "LinkedIn Posts Bulk Scraper"
    
    def validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate input data for the scraper.
        
        Args:
            input_data: Input data to validate
            
        Raises:
            ValueError: If input data is invalid
        """
        # Check for profileUrls (this actor uses profileUrls, not urls)
        profile_urls = input_data.get("profileUrls")
        
        if not profile_urls:
            raise ValueError("profileUrls is required")
        
        if not isinstance(profile_urls, list):
            raise ValueError("profileUrls must be a list")
        
        if len(profile_urls) == 0:
            raise ValueError("At least one profile URL is required")
        
        if len(profile_urls) > 50:  # LinkedIn posts scraping is more intensive
            raise ValueError("Maximum 50 profile URLs allowed")
        
        # Validate each URL
        for url in profile_urls:
            if not isinstance(url, str):
                raise ValueError("All profile URLs must be strings")
            
            if "linkedin.com/in/" not in url:
                raise ValueError(f"Invalid LinkedIn URL: {url}")
        
        # Validate maxPostsPerProfile if provided
        max_posts = input_data.get("maxPostsPerProfile")
        if max_posts is not None:
            if not isinstance(max_posts, int) or max_posts < 1:
                raise ValueError("maxPostsPerProfile must be a positive integer")
            if max_posts > 100:  # Reasonable limit
                raise ValueError("maxPostsPerProfile cannot exceed 100")
    
    def estimate_cost(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate the cost for running the scraper.
        
        Args:
            input_data: Input data
            
        Returns:
            Cost estimation details
        """
        profile_urls = input_data.get("profileUrls", [])
        profile_count = len(profile_urls)
        max_posts_per_profile = input_data.get("maxPostsPerProfile", 20)  # Default from actor
        
        # Cost estimation based on actor configuration
        # LinkedIn Posts Scraper typically costs around $2 per 1000 posts
        posts_expected = profile_count * max_posts_per_profile
        base_cost_per_post = 0.002  # $0.002 per post
        compute_units = posts_expected * 0.1  # Rough estimate
        total_cost = posts_expected * base_cost_per_post
        
        return {
            "estimated_cost": total_cost,
            "compute_units": compute_units,
            "cost_breakdown": {
                "base_cost_per_post": base_cost_per_post,
                "profiles": profile_count,
                "max_posts_per_profile": max_posts_per_profile,
                "expected_posts": posts_expected
            }
        }
    
    def transform_output(self, raw_output: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform raw actor output to expected format.
        
        Args:
            raw_output: Raw output from the actor
            
        Returns:
            Transformed output
        """
        transformed = []
        
        for item in raw_output:
            # The posts actor returns structured data directly (not nested in "element")
            transformed_item = {
                "post": {
                    "id": item.get("id"),
                    "type": item.get("type"),
                    "linkedinUrl": item.get("linkedinUrl"),
                    "content": item.get("content"),
                    "postedAt": item.get("postedAt"),
                    "article": item.get("article"),
                    "newsletterUrl": item.get("newsletterUrl"),
                    "newsletterTitle": item.get("newsletterTitle")
                },
                "author": item.get("author", {}),
                "engagement": {
                    "likes": item.get("engagement", {}).get("likes", 0),
                    "comments": item.get("engagement", {}).get("comments", 0),
                    "shares": item.get("engagement", {}).get("shares", 0),
                    "reactions": item.get("engagement", {}).get("reactions", [])
                },
                "media": {
                    "images": item.get("postImages", [])
                },
                "social": item.get("socialContent", {}),
                "comments": item.get("comments", []),
                "meta": {
                    "type": item.get("type"),
                    "scraped_at": item.get("scrapedAt"),
                    "profile_url": item.get("profileUrl")
                }
            }
            
            transformed.append(transformed_item)
        
        return transformed
    
    async def run_actor_async(self, input_data: Dict[str, Any], timeout: int = 600) -> Dict[str, Any]:
        """
        Run the actor asynchronously.
        
        Args:
            input_data: Input data for the actor
            timeout: Timeout in seconds
            
        Returns:
            Actor run result
        """
        try:
            # Validate input first
            self.validate_input(input_data)
            
            # Use input as-is since this actor expects profileUrls
            actor_input = input_data.copy()
            
            # Set defaults if not provided
            if "maxPostsPerProfile" not in actor_input:
                actor_input["maxPostsPerProfile"] = 20
            
            profile_count = len(actor_input.get("profileUrls", []))
            max_posts = actor_input.get("maxPostsPerProfile", 20)
            
            logger.info("Running LinkedIn Posts Scraper", 
                       profile_count=profile_count,
                       max_posts_per_profile=max_posts)
            
            # Run using the Apify service with correct API
            result = await self.apify_service.run_actor_async(
                actor_id=self.actor_id,
                input_data=actor_input,
                timeout_secs=timeout
            )
            
            # Transform the output to expected format
            if result.get("success") and result.get("items"):
                transformed_items = self.transform_output(result["items"])
                result["items"] = transformed_items
            
            # Track costs if successful
            if result.get("success") and "run" in result:
                compute_units = result["run"].get("computeUnits", 0)
                
                # Convert to Decimal types for consistent calculation
                compute_units_decimal = Decimal(str(compute_units)) if compute_units else Decimal('0')
                cost_per_unit = Decimal(str(settings.default_compute_unit_cost))
                actual_cost = compute_units_decimal * cost_per_unit
                
                # Record the execution cost
                self.cost_manager.record_execution(
                    actor_id=self.actor_id,
                    run_id=result["run"].get("id", "unknown"),
                    actual_cost=actual_cost
                )
            
            return result
            
        except Exception as e:
            logger.error("Error running LinkedIn Posts Scraper", error=str(e))
            return {
                "run": {"id": "error", "status": "FAILED"},
                "items": [],
                "success": False,
                "error": str(e)
            }
    
    def get_default_input(self) -> Dict[str, Any]:
        """
        Get default input configuration.
        
        Returns:
            Default input data
        """
        return {
            "profileUrls": [],
            "maxPostsPerProfile": 20,
            "includeComments": False  # Usually expensive
        } 