"""
Utility functions for working with Apify actors.

This module provides helper functions for working with Apify actors,
such as input validation, URL parsing, and dataset handling.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import structlog

logger = structlog.get_logger(__name__)


def validate_linkedin_url(url: str) -> bool:
    """
    Validate if a URL is a valid LinkedIn URL.
    
    Args:
        url: URL to validate.
        
    Returns:
        True if the URL is a valid LinkedIn URL, False otherwise.
    """
    # Basic LinkedIn URL pattern
    linkedin_pattern = r"^(https?://)?(www\.)?linkedin\.com/.*$"
    return bool(re.match(linkedin_pattern, url))


def validate_facebook_url(url: str) -> bool:
    """
    Validate if a URL is a valid Facebook URL.
    
    Args:
        url: URL to validate.
        
    Returns:
        True if the URL is a valid Facebook URL, False otherwise.
    """
    # Basic Facebook URL pattern
    facebook_pattern = r"^(https?://)?(www\.)?facebook\.com/.*$"
    return bool(re.match(facebook_pattern, url))


def validate_twitter_handle(handle: str) -> bool:
    """
    Validate if a string is a valid Twitter/X handle.
    
    Args:
        handle: Twitter handle to validate (with or without '@').
        
    Returns:
        True if the handle is valid, False otherwise.
    """
    # Remove '@' if present
    if handle.startswith('@'):
        handle = handle[1:]
        
    # Twitter handle pattern (1-15 characters, alphanumeric and underscore)
    twitter_pattern = r"^[A-Za-z0-9_]{1,15}$"
    return bool(re.match(twitter_pattern, handle))


def extract_linkedin_username(url: str) -> Optional[str]:
    """
    Extract LinkedIn username from a LinkedIn URL.
    
    Args:
        url: LinkedIn URL.
        
    Returns:
        LinkedIn username or None if not found.
    """
    # Handle various LinkedIn URL formats
    patterns = [
        r"linkedin\.com/in/([^/]+)",  # Personal profile
        r"linkedin\.com/company/([^/]+)",  # Company page
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def extract_facebook_page_name(url: str) -> Optional[str]:
    """
    Extract Facebook page name from a Facebook URL.
    
    Args:
        url: Facebook URL.
        
    Returns:
        Facebook page name or None if not found.
    """
    # Basic Facebook page pattern
    match = re.search(r"facebook\.com/([^/\?]+)", url)
    if match:
        return match.group(1)
    
    return None


def normalize_twitter_handle(handle: str) -> str:
    """
    Normalize a Twitter handle by removing '@' and ensuring correct format.
    
    Args:
        handle: Twitter handle to normalize.
        
    Returns:
        Normalized Twitter handle.
    """
    # Remove '@' if present and any leading/trailing whitespace
    return handle.strip().lstrip('@')


def format_iso_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Format an ISO date string to a Python datetime object.
    
    Args:
        date_str: ISO date string.
        
    Returns:
        Datetime object or None if the input is None or invalid.
    """
    if not date_str:
        return None
        
    try:
        # Handle both with and without 'Z' timezone designator
        if date_str.endswith('Z'):
            date_str = date_str[:-1] + '+00:00'
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        logger.warning(f"Failed to parse ISO date: {date_str}")
        return None


def batch_items(items: List[Any], batch_size: int = 50) -> List[List[Any]]:
    """
    Split a list of items into batches.
    
    Args:
        items: List of items to split.
        batch_size: Size of each batch.
        
    Returns:
        List of batches.
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def merge_dataset_items(items_list: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Merge multiple lists of dataset items into a single list.
    
    Args:
        items_list: List of lists of dataset items.
        
    Returns:
        Merged list of dataset items.
    """
    result = []
    for items in items_list:
        result.extend(items)
    return result


def preprocess_actor_input_data(
    input_data: Dict[str, Any], 
    required_fields: List[str],
    max_items_per_field: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Preprocess and validate actor input data.
    
    Args:
        input_data: Input data to preprocess.
        required_fields: List of required fields.
        max_items_per_field: Dictionary mapping field names to maximum number of items.
        
    Returns:
        Preprocessed input data.
    
    Raises:
        ValueError: If required fields are missing or invalid.
    """
    # Create a copy to avoid modifying the original
    processed_data = input_data.copy()
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in processed_data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Apply max items per field if specified
    if max_items_per_field:
        for field, max_items in max_items_per_field.items():
            if field in processed_data and isinstance(processed_data[field], list):
                if len(processed_data[field]) > max_items:
                    logger.warning(
                        f"Field {field} exceeds maximum items limit ({len(processed_data[field])} > {max_items}). "
                        f"Truncating to {max_items} items."
                    )
                    processed_data[field] = processed_data[field][:max_items]
    
    return processed_data


def deduplicate_items(items: List[Dict[str, Any]], key_field: str) -> List[Dict[str, Any]]:
    """
    Deduplicate items based on a key field.
    
    Args:
        items: List of items to deduplicate.
        key_field: Field to use for deduplication.
        
    Returns:
        Deduplicated list of items.
    """
    seen_keys = set()
    result = []
    
    for item in items:
        key = item.get(key_field)
        if key and key not in seen_keys:
            seen_keys.add(key)
            result.append(item)
    
    return result


def safe_get_nested_value(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get a nested value from a dictionary using a dot notation path.
    
    Args:
        data: Dictionary to get the value from.
        path: Path to the value using dot notation (e.g., 'a.b.c').
        default: Default value to return if the path doesn't exist.
        
    Returns:
        Value at the path or default if not found.
    """
    keys = path.split('.')
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value 