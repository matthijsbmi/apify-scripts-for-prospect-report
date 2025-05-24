"""
Social media service for orchestrating data collection.

This module provides a high-level service for collecting data from multiple
social media platforms (Facebook, Twitter/X) in a coordinated manner.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog

from app.actors.social.facebook_actor import FacebookActor
from app.actors.social.twitter_actor import TwitterActor
from app.actors.social.validators import (
    is_valid_facebook_page_url, is_valid_twitter_handle, is_valid_twitter_url,
    extract_twitter_handle
)
from app.models.data import SocialMediaData, FacebookData, TwitterData


logger = structlog.get_logger(__name__)


class SocialMediaService:
    """
    Service for collecting social media data.
    
    Coordinates data collection from Facebook and Twitter/X platforms.
    """
    
    def __init__(self):
        """Initialize the social media service."""
        self.facebook_actor = FacebookActor()
        self.twitter_actor = TwitterActor()
    
    async def collect_social_media_data(
        self,
        facebook_page_url: Optional[str] = None,
        twitter_handle: Optional[str] = None,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        max_posts_per_platform: int = 20,
        include_facebook_comments: bool = False,
        include_twitter_replies: bool = False,
        include_twitter_retweets: bool = False,
    ) -> SocialMediaData:
        """
        Collect data from multiple social media platforms.
        
        Args:
            facebook_page_url: Facebook page URL to scrape.
            twitter_handle: Twitter handle or URL to scrape.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD for all platforms.
            max_posts_per_platform: Maximum posts to collect per platform.
            include_facebook_comments: Whether to include Facebook comments.
            include_twitter_replies: Whether to include Twitter replies.
            include_twitter_retweets: Whether to include Twitter retweets.
            
        Returns:
            Combined social media data.
            
        Raises:
            ValueError: If no valid social media identifiers are provided.
        """
        if not facebook_page_url and not twitter_handle:
            raise ValueError("At least one social media identifier must be provided")
        
        log = logger.bind(
            facebook_url=facebook_page_url,
            twitter_handle=twitter_handle,
        )
        log.info("Collecting social media data")
        
        # Calculate budget distribution
        budget_distribution = self._calculate_budget_distribution(
            max_budget_usd,
            facebook=bool(facebook_page_url),
            twitter=bool(twitter_handle),
        )
        
        # Prepare tasks for parallel execution
        tasks = []
        task_names = []
        
        # Facebook data collection
        if facebook_page_url and is_valid_facebook_page_url(facebook_page_url):
            tasks.append(
                self._collect_facebook_data(
                    page_url=facebook_page_url,
                    max_posts=max_posts_per_platform,
                    include_comments=include_facebook_comments,
                    proxy_configuration=proxy_configuration,
                    max_budget_usd=budget_distribution.get("facebook"),
                )
            )
            task_names.append("facebook")
        
        # Twitter data collection
        if twitter_handle:
            # Normalize Twitter handle
            if is_valid_twitter_url(twitter_handle):
                normalized_handle = extract_twitter_handle(twitter_handle)
            else:
                normalized_handle = extract_twitter_handle(twitter_handle)
            
            if normalized_handle and is_valid_twitter_handle(normalized_handle):
                tasks.append(
                    self._collect_twitter_data(
                        handle=normalized_handle,
                        max_tweets=max_posts_per_platform,
                        include_replies=include_twitter_replies,
                        include_retweets=include_twitter_retweets,
                        proxy_configuration=proxy_configuration,
                        max_budget_usd=budget_distribution.get("twitter"),
                    )
                )
                task_names.append("twitter")
        
        if not tasks:
            raise ValueError("No valid social media identifiers provided")
        
        # Execute tasks in parallel
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            facebook_data = None
            twitter_data = None
            
            for i, result in enumerate(results):
                task_name = task_names[i]
                
                if isinstance(result, Exception):
                    log.error(
                        f"Error collecting {task_name} data",
                        error=str(result),
                    )
                elif task_name == "facebook":
                    facebook_data = result
                elif task_name == "twitter":
                    twitter_data = result
            
            # Create combined result
            social_media_data = SocialMediaData(
                facebook=facebook_data,
                twitter=twitter_data,
            )
            
            log.info(
                "Social media data collection completed",
                facebook_collected=facebook_data is not None,
                twitter_collected=twitter_data is not None,
            )
            
            return social_media_data
        
        except Exception as e:
            log.error("Error in social media data collection", error=str(e))
            raise
    
    async def _collect_facebook_data(
        self,
        page_url: str,
        max_posts: int,
        include_comments: bool,
        proxy_configuration: Optional[Dict[str, Any]],
        max_budget_usd: Optional[float],
    ) -> Optional[FacebookData]:
        """
        Collect Facebook data.
        
        Args:
            page_url: Facebook page URL.
            max_posts: Maximum posts to collect.
            include_comments: Whether to include comments.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget for Facebook data.
            
        Returns:
            Facebook data or None if collection fails.
        """
        try:
            result = await self.facebook_actor.scrape_page(
                page_url=page_url,
                max_posts=max_posts,
                include_comments=include_comments,
                proxy_configuration=proxy_configuration,
                max_budget_usd=max_budget_usd,
            )
            
            return result.get("data")
        
        except Exception as e:
            logger.error(
                "Failed to collect Facebook data",
                page_url=page_url,
                error=str(e),
            )
            return None
    
    async def _collect_twitter_data(
        self,
        handle: str,
        max_tweets: int,
        include_replies: bool,
        include_retweets: bool,
        proxy_configuration: Optional[Dict[str, Any]],
        max_budget_usd: Optional[float],
    ) -> Optional[TwitterData]:
        """
        Collect Twitter data.
        
        Args:
            handle: Twitter handle.
            max_tweets: Maximum tweets to collect.
            include_replies: Whether to include replies.
            include_retweets: Whether to include retweets.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget for Twitter data.
            
        Returns:
            Twitter data or None if collection fails.
        """
        try:
            result = await self.twitter_actor.scrape_user_tweets(
                username=handle,
                max_tweets=max_tweets,
                include_replies=include_replies,
                include_retweets=include_retweets,
                proxy_configuration=proxy_configuration,
                max_budget_usd=max_budget_usd,
            )
            
            return result.get("data")
        
        except Exception as e:
            logger.error(
                "Failed to collect Twitter data",
                handle=handle,
                error=str(e),
            )
            return None
    
    def _calculate_budget_distribution(
        self,
        max_budget_usd: Optional[float],
        facebook: bool = True,
        twitter: bool = True,
    ) -> Dict[str, float]:
        """
        Calculate budget distribution across platforms.
        
        Args:
            max_budget_usd: Maximum budget in USD.
            facebook: Whether Facebook data is being collected.
            twitter: Whether Twitter data is being collected.
            
        Returns:
            Dictionary with budget allocation per platform.
        """
        if not max_budget_usd:
            return {}
        
        # Count active platforms
        platforms = []
        if facebook:
            platforms.append("facebook")
        if twitter:
            platforms.append("twitter")
        
        if not platforms:
            return {}
        
        # Base distribution
        base_budget = max_budget_usd / len(platforms)
        distribution = {}
        
        # Facebook typically costs more due to higher complexity
        if facebook and twitter:
            # Facebook gets 60% of budget, Twitter gets 40%
            distribution["facebook"] = max_budget_usd * 0.6
            distribution["twitter"] = max_budget_usd * 0.4
        elif facebook:
            distribution["facebook"] = max_budget_usd
        elif twitter:
            distribution["twitter"] = max_budget_usd
        
        return distribution
    
    async def validate_social_media_urls(
        self,
        facebook_page_url: Optional[str] = None,
        twitter_handle: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate social media URLs and handles.
        
        Args:
            facebook_page_url: Facebook page URL to validate.
            twitter_handle: Twitter handle or URL to validate.
            
        Returns:
            Validation results.
        """
        results = {
            "facebook": {
                "valid": False,
                "url": facebook_page_url,
                "error": None,
            },
            "twitter": {
                "valid": False,
                "handle": twitter_handle,
                "error": None,
            },
        }
        
        # Validate Facebook URL
        if facebook_page_url:
            if is_valid_facebook_page_url(facebook_page_url):
                results["facebook"]["valid"] = True
            else:
                results["facebook"]["error"] = "Invalid Facebook page URL format"
        
        # Validate Twitter handle
        if twitter_handle:
            # Try to extract and validate handle
            if is_valid_twitter_url(twitter_handle):
                normalized_handle = extract_twitter_handle(twitter_handle)
                if normalized_handle and is_valid_twitter_handle(normalized_handle):
                    results["twitter"]["valid"] = True
                    results["twitter"]["normalized_handle"] = normalized_handle
                else:
                    results["twitter"]["error"] = "Could not extract valid handle from URL"
            else:
                normalized_handle = extract_twitter_handle(twitter_handle)
                if normalized_handle and is_valid_twitter_handle(normalized_handle):
                    results["twitter"]["valid"] = True
                    results["twitter"]["normalized_handle"] = normalized_handle
                else:
                    results["twitter"]["error"] = "Invalid Twitter handle format"
        
        return results 