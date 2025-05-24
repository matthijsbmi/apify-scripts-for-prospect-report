"""
Data transformers for social media actors.

Contains functions for transforming raw actor responses into standardized formats.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.data import FacebookData, TwitterData


def transform_facebook_data(raw_data: List[Dict[str, Any]], page_url: str) -> FacebookData:
    """
    Transform raw Facebook data to standardized format.
    
    Args:
        raw_data: Raw data from Facebook Posts Scraper actor.
        page_url: Facebook page URL.
        
    Returns:
        Standardized Facebook data.
    """
    # Extract page information from the first item or construct from URL
    page_info = {}
    page_name = None
    posts = []
    
    for item in raw_data:
        # Extract page information if available
        if not page_name and item.get("pageName"):
            page_name = item.get("pageName")
        
        if not page_info.get("followers") and item.get("pageFollowers"):
            page_info["followers"] = item.get("pageFollowers")
        
        if not page_info.get("likes") and item.get("pageLikes"):
            page_info["likes"] = item.get("pageLikes")
        
        # Extract post data
        if item.get("type") == "post" or item.get("text"):
            post_data = {
                "id": item.get("id", ""),
                "text": item.get("text", ""),
                "url": item.get("url", ""),
                "published_at": _parse_facebook_date(item.get("time")),
                "likes": item.get("likes", 0),
                "comments": item.get("comments", 0),
                "shares": item.get("shares", 0),
                "reactions": item.get("reactions", {}),
                "media": item.get("attachments", []),
                "raw_data": item,
            }
            posts.append(post_data)
    
    # Add any additional page info we can extract
    if not page_info.get("description") and raw_data:
        for item in raw_data:
            if item.get("pageDescription"):
                page_info["description"] = item.get("pageDescription")
                break
    
    return FacebookData(
        page_url=page_url,
        name=page_name or "Unknown Page",
        posts=posts,
        page_info=page_info,
        extracted_at=datetime.now(),
    )


def transform_twitter_data(raw_data: List[Dict[str, Any]], handle: str) -> TwitterData:
    """
    Transform raw Twitter data to standardized format.
    
    Args:
        raw_data: Raw data from Twitter/X Scraper actor.
        handle: Twitter handle.
        
    Returns:
        Standardized Twitter data.
    """
    # Extract profile information
    profile_info = {}
    tweets = []
    followers_count = None
    following_count = None
    
    for item in raw_data:
        # Extract profile information from any item that has it
        author = item.get("author", {})
        if author:
            if not profile_info.get("name") and author.get("name"):
                profile_info["name"] = author.get("name")
            
            if not profile_info.get("bio") and author.get("description"):
                profile_info["bio"] = author.get("description")
            
            if not profile_info.get("verified") and author.get("verified") is not None:
                profile_info["verified"] = author.get("verified")
            
            if not profile_info.get("profile_image") and author.get("profileImageUrl"):
                profile_info["profile_image"] = author.get("profileImageUrl")
            
            if not profile_info.get("banner_image") and author.get("profileBannerUrl"):
                profile_info["banner_image"] = author.get("profileBannerUrl")
            
            if not profile_info.get("location") and author.get("location"):
                profile_info["location"] = author.get("location")
            
            if not profile_info.get("website") and author.get("url"):
                profile_info["website"] = author.get("url")
            
            if followers_count is None and author.get("followers"):
                followers_count = author.get("followers")
            
            if following_count is None and author.get("following"):
                following_count = author.get("following")
        
        # Extract tweet data
        if item.get("text") or item.get("fullText"):
            tweet_data = {
                "id": item.get("id", ""),
                "text": item.get("fullText") or item.get("text", ""),
                "url": item.get("url", ""),
                "created_at": _parse_twitter_date(item.get("createdAt")),
                "retweet_count": item.get("retweetCount", 0),
                "favorite_count": item.get("favoriteCount", 0),
                "reply_count": item.get("replyCount", 0),
                "quote_count": item.get("quoteCount", 0),
                "hashtags": _extract_hashtags(item.get("hashtags", [])),
                "mentions": _extract_mentions(item.get("mentions", [])),
                "urls": _extract_urls(item.get("urls", [])),
                "media": _extract_media(item.get("media", [])),
                "is_retweet": item.get("isRetweet", False),
                "is_reply": item.get("isReply", False),
                "is_quote": item.get("isQuote", False),
                "language": item.get("lang", ""),
                "raw_data": item,
            }
            tweets.append(tweet_data)
    
    # Add account creation date if available
    if raw_data and raw_data[0].get("author", {}).get("createdAt"):
        profile_info["created_at"] = _parse_twitter_date(
            raw_data[0]["author"]["createdAt"]
        )
    
    # Add tweet count if available
    if raw_data and raw_data[0].get("author", {}).get("statusesCount"):
        profile_info["tweets_count"] = raw_data[0]["author"]["statusesCount"]
    
    return TwitterData(
        handle=handle,
        profile_info=profile_info,
        tweets=tweets,
        followers_count=followers_count,
        following_count=following_count,
        extracted_at=datetime.now(),
    )


def _parse_facebook_date(date_str: Optional[str]) -> Optional[str]:
    """
    Parse Facebook date string to ISO format.
    
    Args:
        date_str: Date string from Facebook.
        
    Returns:
        ISO formatted date string or None.
    """
    if not date_str:
        return None
    
    try:
        # Facebook usually provides dates in ISO format or timestamp
        if isinstance(date_str, (int, float)):
            # Convert timestamp to datetime
            dt = datetime.fromtimestamp(date_str)
            return dt.isoformat()
        elif isinstance(date_str, str):
            # Try to parse ISO date
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.isoformat()
            else:
                # Try other common formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y"]:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.isoformat()
                    except ValueError:
                        continue
    except (ValueError, TypeError):
        pass
    
    return date_str  # Return original if parsing fails


def _parse_twitter_date(date_str: Optional[str]) -> Optional[str]:
    """
    Parse Twitter date string to ISO format.
    
    Args:
        date_str: Date string from Twitter.
        
    Returns:
        ISO formatted date string or None.
    """
    if not date_str:
        return None
    
    try:
        # Twitter usually provides dates in ISO format
        if isinstance(date_str, str):
            # Handle various Twitter date formats
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return dt.isoformat()
            else:
                # Try Twitter's common date format
                try:
                    dt = datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
                    return dt.isoformat()
                except ValueError:
                    # Try other formats
                    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            dt = datetime.strptime(date_str, fmt)
                            return dt.isoformat()
                        except ValueError:
                            continue
    except (ValueError, TypeError):
        pass
    
    return date_str  # Return original if parsing fails


def _extract_hashtags(hashtags_data: List[Any]) -> List[str]:
    """Extract hashtags from Twitter data."""
    hashtags = []
    for tag in hashtags_data:
        if isinstance(tag, str):
            hashtags.append(tag)
        elif isinstance(tag, dict) and tag.get("text"):
            hashtags.append(tag["text"])
    return hashtags


def _extract_mentions(mentions_data: List[Any]) -> List[Dict[str, str]]:
    """Extract mentions from Twitter data."""
    mentions = []
    for mention in mentions_data:
        if isinstance(mention, dict):
            mentions.append({
                "username": mention.get("username", ""),
                "name": mention.get("name", ""),
                "id": mention.get("id", ""),
            })
    return mentions


def _extract_urls(urls_data: List[Any]) -> List[Dict[str, str]]:
    """Extract URLs from Twitter data."""
    urls = []
    for url in urls_data:
        if isinstance(url, dict):
            urls.append({
                "url": url.get("url", ""),
                "expanded_url": url.get("expandedUrl", ""),
                "display_url": url.get("displayUrl", ""),
            })
    return urls


def _extract_media(media_data: List[Any]) -> List[Dict[str, Any]]:
    """Extract media from Twitter data."""
    media = []
    for item in media_data:
        if isinstance(item, dict):
            media.append({
                "type": item.get("type", ""),
                "url": item.get("url", ""),
                "media_url": item.get("mediaUrl", ""),
                "alt_text": item.get("altText", ""),
                "width": item.get("width"),
                "height": item.get("height"),
            })
    return media 