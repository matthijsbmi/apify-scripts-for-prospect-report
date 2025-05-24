"""
Twitter/X Scraper actor implementation.

Integration with the Twitter/X Scraper Apify actor (61RPP7dywgiy0JPD0).
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import structlog

from app.actors.base import BaseActor, ActorRunOptions, ActorRunResult
from app.actors.social.validators import (
    is_valid_twitter_handle, is_valid_twitter_url, extract_twitter_handle,
    normalize_twitter_handles
)
from app.actors.social.transformers import transform_twitter_data
from app.models.data import TwitterData


logger = structlog.get_logger(__name__)


class TwitterActor(BaseActor):
    """
    Integration with Twitter/X Scraper actor.
    
    Actor ID: 61RPP7dywgiy0JPD0
    """
    
    def __init__(self):
        """Initialize the Twitter/X Scraper actor."""
        super().__init__("61RPP7dywgiy0JPD0")
    
    async def scrape_tweets(
        self,
        twitter_handles: Optional[List[str]] = None,
        search_terms: Optional[List[str]] = None,
        max_items: int = 50,
        sort: str = "Latest",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        tweet_language: str = "en",
        minimum_favorites: Optional[int] = None,
        minimum_replies: Optional[int] = None,
        minimum_retweets: Optional[int] = None,
        only_verified_users: bool = False,
        only_twitter_blue: bool = False,
        only_image: bool = False,
        only_video: bool = False,
        only_quote: bool = False,
        include_search_terms: bool = False,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 600,
    ) -> Dict[str, Union[List[Dict[str, Any]], ActorRunResult]]:
        """
        Scrape tweets using either Twitter handles or search terms (or both).
        
        Args:
            twitter_handles: List of Twitter handles to scrape from.
            search_terms: List of search terms to find tweets.
            max_items: Maximum number of tweets to scrape.
            sort: Sort order ("Latest", "Popular", etc.).
            start_date: Start date for tweets (YYYY-MM-DD format).
            end_date: End date for tweets (YYYY-MM-DD format).
            tweet_language: Language of tweets (e.g., "en", "es").
            minimum_favorites: Minimum number of favorites/likes.
            minimum_replies: Minimum number of replies.
            minimum_retweets: Minimum number of retweets.
            only_verified_users: Only include tweets from verified users.
            only_twitter_blue: Only include tweets from Twitter Blue users.
            only_image: Only include tweets with images.
            only_video: Only include tweets with videos.
            only_quote: Only include quote tweets.
            include_search_terms: Include search terms in results.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD.
            timeout_secs: Timeout in seconds.
            
        Returns:
            Dictionary with 'data' containing tweet data and 'metadata' containing ActorRunResult.
            
        Raises:
            ValueError: If neither twitter_handles nor search_terms are provided.
        """
        # Validate that at least one parameter is provided
        if not twitter_handles and not search_terms:
            raise ValueError("At least one of twitter_handles or search_terms must be provided")
        
        # Normalize Twitter handles if provided
        normalized_handles = []
        if twitter_handles:
            for handle in twitter_handles:
                if is_valid_twitter_url(handle):
                    normalized_handle = extract_twitter_handle(handle)
                else:
                    normalized_handle = extract_twitter_handle(handle)
                
                if normalized_handle and is_valid_twitter_handle(normalized_handle):
                    normalized_handles.append(normalized_handle)
                else:
                    logger.warning(f"Invalid Twitter handle: {handle}")
        
        log = logger.bind(
            actor="twitter_scraper",
            handles_count=len(normalized_handles) if normalized_handles else 0,
            search_terms_count=len(search_terms) if search_terms else 0,
            max_items=max_items
        )
        log.info("Scraping Twitter/X data")
        
        # Prepare input data using the correct format
        input_data = {
            "maxItems": max_items,
            "sort": sort,
            "tweetLanguage": tweet_language,
            "includeSearchTerms": include_search_terms,
        }
        
        # Add Twitter handles if provided
        if normalized_handles:
            input_data["twitterHandles"] = normalized_handles
        
        # Add search terms if provided
        if search_terms:
            input_data["searchTerms"] = search_terms
        
        # Add optional parameters
        if start_date:
            input_data["start"] = start_date
        if end_date:
            input_data["end"] = end_date
        if minimum_favorites is not None:
            input_data["minimumFavorites"] = minimum_favorites
        if minimum_replies is not None:
            input_data["minimumReplies"] = minimum_replies
        if minimum_retweets is not None:
            input_data["minimumRetweets"] = minimum_retweets
        
        # Add boolean flags
        if only_verified_users:
            input_data["onlyVerifiedUsers"] = True
        if only_twitter_blue:
            input_data["onlyTwitterBlue"] = True
        if only_image:
            input_data["onlyImage"] = True
        if only_video:
            input_data["onlyVideo"] = True
        if only_quote:
            input_data["onlyQuote"] = True
        
        # Add proxy configuration if provided
        if proxy_configuration:
            input_data["proxyConfiguration"] = proxy_configuration
        else:
            # Use default proxy configuration
            input_data["proxyConfiguration"] = {"useApifyProxy": True}
        
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
        tweet_data = []
        if result and result.items and len(result.items) > 0:
            log.info(
                "Successfully scraped Twitter data",
                tweet_count=len(result.items)
            )
            
            # Return raw tweet data for now
            tweet_data = result.items
        else:
            log.warning("No Twitter data retrieved")
        
        return {
            "data": tweet_data,
            "metadata": result,
        }
    
    async def scrape_user_tweets(
        self,
        username: str,
        max_items: int = 50,
        sort: str = "Latest",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 300,
    ) -> Dict[str, Union[List[Dict[str, Any]], ActorRunResult]]:
        """
        Scrape tweets from a specific Twitter/X user.
        
        Args:
            username: Twitter/X username (with or without @).
            max_items: Maximum number of tweets to scrape.
            sort: Sort order ("Latest", "Popular", etc.).
            start_date: Start date for tweets (YYYY-MM-DD format).
            end_date: End date for tweets (YYYY-MM-DD format).
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD.
            timeout_secs: Timeout in seconds.
            
        Returns:
            Dictionary with 'data' containing tweet data and 'metadata' containing ActorRunResult.
            
        Raises:
            ValueError: If username is invalid.
        """
        return await self.scrape_tweets(
            twitter_handles=[username],
            search_terms=None,
            max_items=max_items,
            sort=sort,
            start_date=start_date,
            end_date=end_date,
            proxy_configuration=proxy_configuration,
            max_budget_usd=max_budget_usd,
            timeout_secs=timeout_secs,
        )
    
    async def scrape_search_terms(
        self,
        search_terms: List[str],
        max_items: int = 50,
        sort: str = "Latest",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        tweet_language: str = "en",
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 600,
    ) -> Dict[str, Union[List[Dict[str, Any]], ActorRunResult]]:
        """
        Scrape tweets based on search terms.
        
        Args:
            search_terms: List of search terms to find tweets.
            max_items: Maximum number of tweets to scrape.
            sort: Sort order ("Latest", "Popular", etc.).
            start_date: Start date for tweets (YYYY-MM-DD format).
            end_date: End date for tweets (YYYY-MM-DD format).
            tweet_language: Language of tweets (e.g., "en", "es").
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD.
            timeout_secs: Timeout in seconds.
            
        Returns:
            Dictionary with 'data' containing tweet data and 'metadata' containing ActorRunResult.
            
        Raises:
            ValueError: If no search terms are provided.
        """
        return await self.scrape_tweets(
            twitter_handles=None,
            search_terms=search_terms,
            max_items=max_items,
            sort=sort,
            start_date=start_date,
            end_date=end_date,
            tweet_language=tweet_language,
            proxy_configuration=proxy_configuration,
            max_budget_usd=max_budget_usd,
            timeout_secs=timeout_secs,
        )
    
    async def scrape_multiple_users(
        self,
        usernames: List[str],
        max_tweets_per_user: int = 50,
        include_replies: bool = False,
        include_retweets: bool = False,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        timeout_secs: int = 600,
    ) -> Dict[str, Union[List[TwitterData], ActorRunResult]]:
        """
        Scrape tweets from multiple Twitter/X users.
        
        Args:
            usernames: List of Twitter/X usernames (with or without @).
            max_tweets_per_user: Maximum number of tweets per user.
            include_replies: Whether to include replies.
            include_retweets: Whether to include retweets.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD.
            timeout_secs: Timeout in seconds.
            
        Returns:
            Dictionary with 'data' containing list of TwitterData and 'metadata' containing ActorRunResult.
            
        Raises:
            ValueError: If no valid usernames are provided.
        """
        if not usernames:
            raise ValueError("At least one username must be provided")
        
        # Normalize usernames
        normalized_handles = []
        for username in usernames:
            if is_valid_twitter_url(username):
                handle = extract_twitter_handle(username)
            else:
                handle = extract_twitter_handle(username)
            
            if handle and is_valid_twitter_handle(handle):
                normalized_handles.append(handle)
        
        if not normalized_handles:
            raise ValueError("No valid Twitter usernames provided")
        
        log = logger.bind(
            actor="twitter_scraper",
            user_count=len(normalized_handles),
            max_tweets_per_user=max_tweets_per_user
        )
        log.info("Scraping multiple Twitter users")
        
        # Prepare input
        input_data = {
            "usernames": normalized_handles,
            "maxTweetsPerUser": max_tweets_per_user,
            "includeReplies": include_replies,
            "includeRetweets": include_retweets,
        }
        
        # Add proxy configuration if provided
        if proxy_configuration:
            input_data["proxyConfiguration"] = proxy_configuration
        
        # Set options
        options = ActorRunOptions(
            timeout_secs=timeout_secs,
            memory_mbytes=1024,  # Use 1GB of memory for multiple users
        )
        
        # Run actor
        result = await self.run_async(
            input_data=input_data,
            options=options,
            max_budget=max_budget_usd,
        )
        
        # Process results
        twitter_data_list = []
        if result and result.items and len(result.items) > 0:
            log.info(
                "Successfully scraped Twitter data",
                total_items=len(result.items)
            )
            
            # Group items by username and transform
            for handle in normalized_handles:
                # Filter items for this user
                user_items = [
                    item for item in result.items
                    if item.get("author", {}).get("username", "").lower() == handle.lower()
                ]
                
                try:
                    twitter_data = transform_twitter_data(user_items, handle)
                    twitter_data_list.append(twitter_data)
                except Exception as e:
                    log.error(
                        "Error transforming Twitter data",
                        username=handle,
                        error=str(e)
                    )
                    # Add basic TwitterData with error info
                    twitter_data_list.append(TwitterData(
                        handle=handle,
                        profile_info={"error": str(e)},
                        tweets=[],
                        followers_count=None,
                        following_count=None,
                    ))
        else:
            # Create empty TwitterData for each user
            for handle in normalized_handles:
                twitter_data_list.append(TwitterData(
                    handle=handle,
                    profile_info={},
                    tweets=[],
                    followers_count=None,
                    following_count=None,
                ))
        
        return {
            "data": twitter_data_list,
            "metadata": result,
        } 