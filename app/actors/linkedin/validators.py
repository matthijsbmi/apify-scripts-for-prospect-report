"""
Validators for LinkedIn URLs and data.

Contains validation functions for LinkedIn profile URLs, company URLs, and post URLs.
"""

import re
from typing import List, Optional


def is_valid_linkedin_profile_url(url: str) -> bool:
    """
    Validate a LinkedIn profile URL.
    
    Args:
        url: URL to validate.
        
    Returns:
        True if URL is a valid LinkedIn profile URL, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic LinkedIn profile URL pattern (linkedin.com/in/username)
    profile_pattern = r"^https?://(?:www\.)?linkedin\.com/in/[\w\-%.]+/?(?:\?.*)?$"
    return bool(re.match(profile_pattern, url))


def is_valid_linkedin_company_url(url: str) -> bool:
    """
    Validate a LinkedIn company URL.
    
    Args:
        url: URL to validate.
        
    Returns:
        True if URL is a valid LinkedIn company URL, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic LinkedIn company URL pattern (linkedin.com/company/name)
    # Exclude ID-based URLs (pure numeric company IDs)
    company_pattern = r"^https?://(?:www\.)?linkedin\.com/company/(?![\d]+/?$)[\w\-%.]+/?(?:\?.*)?$"
    return bool(re.match(company_pattern, url, re.IGNORECASE))


def is_valid_linkedin_post_url(url: str) -> bool:
    """
    Validate a LinkedIn post URL.
    
    Args:
        url: URL to validate.
        
    Returns:
        True if URL is a valid LinkedIn post URL, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic LinkedIn post URL pattern (several formats)
    post_patterns = [
        # Activity posts (linkedin.com/posts/username_activity-hash)
        r"^https?://(?:www\.)?linkedin\.com/posts/[\w\-%.]+_[\w\-]+(?:\?.*)?$",
        # Feed posts
        r"^https?://(?:www\.)?linkedin\.com/feed/update/urn:li:activity:[\d]+/?(?:\?.*)?$",
        # Article posts
        r"^https?://(?:www\.)?linkedin\.com/pulse/[\w\-]+(?:\?.*)?$",
    ]
    
    for pattern in post_patterns:
        if re.match(pattern, url):
            return True
    
    return False


def extract_linkedin_username(profile_url: str) -> Optional[str]:
    """
    Extract LinkedIn username from a profile URL.
    
    Args:
        profile_url: LinkedIn profile URL.
        
    Returns:
        Username if found, None otherwise.
    """
    if not is_valid_linkedin_profile_url(profile_url):
        return None
    
    # Extract username part from URL
    pattern = r"linkedin\.com/in/([\w\-%.]+)"
    match = re.search(pattern, profile_url)
    
    if match:
        return match.group(1)
    
    return None


def extract_linkedin_company_id(company_url: str) -> Optional[str]:
    """
    Extract LinkedIn company ID or slug from a company URL.
    
    Args:
        company_url: LinkedIn company URL.
        
    Returns:
        Company ID or slug if found, None otherwise.
    """
    if not is_valid_linkedin_company_url(company_url):
        return None
    
    # Extract company ID or slug from URL
    pattern = r"linkedin\.com/company/([\w\-%.]+)"
    match = re.search(pattern, company_url)
    
    if match:
        return match.group(1)
    
    return None


def validate_linkedin_profile_urls(urls: List[str]) -> List[str]:
    """
    Filter a list of URLs to only valid LinkedIn profile URLs.
    
    Args:
        urls: List of URLs to validate.
        
    Returns:
        List of valid LinkedIn profile URLs.
    """
    return [url for url in urls if is_valid_linkedin_profile_url(url)]


def validate_linkedin_company_urls(urls: List[str]) -> List[str]:
    """
    Filter a list of URLs to only valid LinkedIn company URLs.
    
    Args:
        urls: List of URLs to validate.
        
    Returns:
        List of valid LinkedIn company URLs.
    """
    return [url for url in urls if is_valid_linkedin_company_url(url)] 