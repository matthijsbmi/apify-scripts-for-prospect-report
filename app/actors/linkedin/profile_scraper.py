"""
LinkedIn Profile Bulk Scraper implementation.

This module provides the LinkedInProfileScraper class that matches the test expectations.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
import structlog

from app.actors.linkedin.profile_actor import LinkedInProfileActor
from app.core.apify_client import ApifyService
from app.cost.manager import CostManager
from app.core.config import settings

logger = structlog.get_logger(__name__)


class LinkedInProfileScraper:
    """
    LinkedIn Profile Bulk Scraper wrapper class.
    
    This class provides a simplified interface for the LinkedIn Profile Bulk Scraper
    that matches the test expectations.
    """
    
    def __init__(self, apify_service: ApifyService, cost_manager: CostManager):
        """
        Initialize the LinkedIn Profile Scraper.
        
        Args:
            apify_service: Apify service instance
            cost_manager: Cost manager instance
        """
        self.apify_service = apify_service
        self.cost_manager = cost_manager
        self.actor_id = "LpVuK3Zozwuipa5bp"
        self.name = "LinkedIn Profile Bulk Scraper"
        
        # Initialize the underlying actor
        self._actor = LinkedInProfileActor()
    
    def validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate input data for the scraper.
        
        Args:
            input_data: Input data to validate
            
        Raises:
            ValueError: If input data is invalid
        """
        # Check for both old format (profileUrls) and new format (urls)
        profile_urls = input_data.get("profileUrls") or input_data.get("urls")
        
        if not profile_urls:
            raise ValueError("profileUrls or urls is required")
        
        if not isinstance(profile_urls, list):
            raise ValueError("profileUrls/urls must be a list")
        
        if len(profile_urls) == 0:
            raise ValueError("At least one profile URL is required")
        
        if len(profile_urls) > 100:
            raise ValueError("Maximum 100 profile URLs allowed")
        
        # Validate each URL
        for url in profile_urls:
            if not isinstance(url, str):
                raise ValueError("All profile URLs must be strings")
            
            if "linkedin.com/in/" not in url:
                raise ValueError(f"Invalid LinkedIn URL: {url}")
    
    def estimate_cost(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate the cost for running the scraper.
        
        Args:
            input_data: Input data
            
        Returns:
            Cost estimation details
        """
        profile_urls = input_data.get("profileUrls") or input_data.get("urls") or []
        profile_count = len(profile_urls)
        
        # Cost estimation based on actor configuration
        # LinkedIn Profile Scraper typically costs around $4 per 1000 profiles
        base_cost = 0.002  # $0.002 per profile
        compute_units = profile_count * 0.05  # Rough estimate
        total_cost = profile_count * base_cost
        
        return {
            "estimated_cost": total_cost,
            "compute_units": compute_units,
            "cost_breakdown": {
                "base_cost": base_cost,
                "profiles": profile_count,
                "cost_per_profile": base_cost
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
            # The actor returns data in "element" key
            if "element" in item and item["element"]:
                profile_data = item["element"]
                
                # Transform to a more standard format
                transformed_item = {
                    "profile": {
                        "id": profile_data.get("id"),
                        "publicIdentifier": profile_data.get("publicIdentifier"),
                        "fullName": f"{profile_data.get('firstName', '')} {profile_data.get('lastName', '')}".strip(),
                        "firstName": profile_data.get("firstName"),
                        "lastName": profile_data.get("lastName"),
                        "headline": profile_data.get("headline"),
                        "about": profile_data.get("about"),
                        "location": profile_data.get("location", {}).get("linkedinText"),
                        "connectionsCount": profile_data.get("connectionsCount"),
                        "followerCount": profile_data.get("followerCount"),
                        "linkedinUrl": profile_data.get("linkedinUrl"),
                        "photo": profile_data.get("photo"),
                        "websites": profile_data.get("websites", [])
                    },
                    "experience": profile_data.get("experience", []),
                    "education": profile_data.get("education", []),
                    "skills": profile_data.get("skills", []),
                    "certifications": profile_data.get("certifications", []),
                    "languages": profile_data.get("languages", []),
                    "projects": profile_data.get("projects", []),
                    "publications": profile_data.get("publications", []),
                    "recommendations": profile_data.get("receivedRecommendations", []),
                    "featured": profile_data.get("featured"),
                    "meta": {
                        "status": item.get("status"),
                        "retries": item.get("retries"),
                        "requestId": item.get("requestId"),
                        "entityId": item.get("entityId")
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
            
            # Transform input to correct format for the actor
            actor_input = input_data.copy()
            
            # Convert profileUrls to urls if needed (actor expects "urls")
            if "profileUrls" in actor_input and "urls" not in actor_input:
                actor_input["urls"] = actor_input.pop("profileUrls")
            
            profile_count = len(actor_input.get("urls", []))
            
            logger.info("Running LinkedIn Profile Scraper", 
                       profile_count=profile_count)
            
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
            logger.error("Error running LinkedIn Profile Scraper", error=str(e))
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
            # Use the correct format the actor expects
            "urls": []
        } 