"""
Validators for social media URLs and identifiers.

Contains validation functions for social media URLs, handles, and other identifiers.
"""

import re
from typing import List, Optional


def is_valid_facebook_page_url(url: str) -> bool:
    """
    Validate if a URL is a valid Facebook page URL.
    
    Args:
        url: URL to validate.
        
    Returns:
        True if the URL is a valid Facebook page URL, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic Facebook page URL pattern
    patterns = [
        # Standard page URL: facebook.com/PageName
        r"^https?://(?:www\.)?facebook\.com/(?!(?:profile\.php|pages/|events/|groups/|hashtag/))[a-zA-Z0-9\.\-_]+/?(?:\?.*)?$",
        
        # Explicit page URL: facebook.com/pages/PageName
        r"^https?://(?:www\.)?facebook\.com/pages/[a-zA-Z0-9\.\-_%]+(/[0-9]+)?/?(?:\?.*)?$",
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    
    return False


def is_valid_facebook_profile_url(url: str) -> bool:
    """
    Validate if a URL is a valid Facebook profile URL.
    
    Args:
        url: URL to validate.
        
    Returns:
        True if the URL is a valid Facebook profile URL, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic Facebook profile URL pattern
    patterns = [
        # Standard profile URL: facebook.com/profile.php?id=123
        r"^https?://(?:www\.)?facebook\.com/profile\.php\?id=[0-9]+(?:&.*)?$",
        
        # Username profile URL: facebook.com/username
        r"^https?://(?:www\.)?facebook\.com/(?![a-zA-Z]+\.php)[a-zA-Z0-9\.]+/?(?:\?.*)?$",
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    
    return False


def is_valid_facebook_post_url(url: str) -> bool:
    """
    Validate if a URL is a valid Facebook post URL.
    
    Args:
        url: URL to validate.
        
    Returns:
        True if the URL is a valid Facebook post URL, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic Facebook post URL pattern
    patterns = [
        # Standard post URL: facebook.com/PageName/posts/123
        r"^https?://(?:www\.)?facebook\.com/[^/]+/posts/[a-zA-Z0-9_]+/?(?:\?.*)?$",
        
        # Photo post URL: facebook.com/PageName/photos/123
        r"^https?://(?:www\.)?facebook\.com/[^/]+/photos/[a-zA-Z0-9_\.]+/?(?:\?.*)?$",
        
        # Video post URL: facebook.com/PageName/videos/123
        r"^https?://(?:www\.)?facebook\.com/[^/]+/videos/[a-zA-Z0-9_]+/?(?:\?.*)?$",
        
        # Story URL: facebook.com/stories/123
        r"^https?://(?:www\.)?facebook\.com/stories/[a-zA-Z0-9_]+/?(?:\?.*)?$",
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    
    return False


def extract_facebook_page_name(url: str) -> Optional[str]:
    """
    Extract Facebook page name from a URL.
    
    Args:
        url: Facebook page URL.
        
    Returns:
        Page name if found, None otherwise.
    """
    if not is_valid_facebook_page_url(url):
        return None
    
    # Standard page URL: facebook.com/PageName
    pattern1 = r"facebook\.com/([a-zA-Z0-9\.\-_]+)/?(?:\?.*)?$"
    match = re.search(pattern1, url)
    if match:
        return match.group(1)
    
    # Explicit page URL: facebook.com/pages/PageName/123
    pattern2 = r"facebook\.com/pages/([a-zA-Z0-9\.\-_%]+)(?:/[0-9]+)?/?(?:\?.*)?$"
    match = re.search(pattern2, url)
    if match:
        return match.group(1)
    
    return None


def is_valid_twitter_handle(handle: str) -> bool:
    """
    Validate if a string is a valid Twitter/X handle.
    
    Args:
        handle: Twitter handle to validate.
        
    Returns:
        True if the handle is valid, False otherwise.
    """
    if not handle or not isinstance(handle, str):
        return False
    
    # Remove @ if present
    if handle.startswith('@'):
        handle = handle[1:]
    
    # Twitter handles are 1-15 characters, alphanumeric and underscores
    pattern = r"^[a-zA-Z0-9_]{1,15}$"
    return bool(re.match(pattern, handle))


def is_valid_twitter_url(url: str) -> bool:
    """
    Validate if a URL is a valid Twitter/X URL.
    
    Args:
        url: URL to validate.
        
    Returns:
        True if the URL is a valid Twitter URL, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic Twitter URL pattern (works for both twitter.com and x.com)
    patterns = [
        # Profile URL: twitter.com/username or x.com/username
        r"^https?://(?:www\.)?(?:twitter|x)\.com/([a-zA-Z0-9_]{1,15})/?(?:\?.*)?$",
        
        # Tweet URL: twitter.com/username/status/123 or x.com/username/status/123
        r"^https?://(?:www\.)?(?:twitter|x)\.com/[a-zA-Z0-9_]{1,15}/status/[0-9]+/?(?:\?.*)?$",
    ]
    
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    
    return False


def extract_twitter_handle(url_or_handle: str) -> Optional[str]:
    """
    Extract Twitter/X handle from a URL or handle string.
    
    Args:
        url_or_handle: Twitter URL or handle.
        
    Returns:
        Handle if found, None otherwise.
    """
    # Check if it's already a handle
    if url_or_handle.startswith('@'):
        handle = url_or_handle[1:]  # Remove @
        if is_valid_twitter_handle(handle):
            return handle
    elif is_valid_twitter_handle(url_or_handle):
        return url_or_handle
    
    # Check if it's a URL
    if is_valid_twitter_url(url_or_handle):
        # Extract handle from profile URL
        pattern = r"(?:twitter|x)\.com/([a-zA-Z0-9_]{1,15})(?:/|$|\?)"
        match = re.search(pattern, url_or_handle)
        if match:
            return match.group(1)
    
    return None


def normalize_twitter_handles(handles: List[str]) -> List[str]:
    """
    Normalize a list of Twitter/X handles or URLs.
    
    Args:
        handles: List of handles or URLs to normalize.
        
    Returns:
        List of normalized handles (without @ prefix).
    """
    result = []
    
    for item in handles:
        if not item or not isinstance(item, str):
            continue
        
        handle = extract_twitter_handle(item)
        if handle:
            result.append(handle)
    
    return result