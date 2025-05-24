"""
Validation functions for company data identifiers.

This module provides utilities for validating and extracting company identifiers
from various sources like DUNS numbers, Crunchbase URLs, ZoomInfo, etc.
"""

import re
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urlparse


def is_valid_duns_number(duns: str) -> bool:
    """
    Validate DUNS (Data Universal Numbering System) number.
    
    DUNS numbers are 9-digit identifiers used by Dun & Bradstreet.
    
    Args:
        duns: DUNS number to validate.
        
    Returns:
        True if valid DUNS number.
    """
    if not isinstance(duns, str):
        return False
    
    # Remove any hyphens or spaces
    clean_duns = re.sub(r'[-\s]', '', duns)
    
    # Must be exactly 9 digits
    return bool(re.match(r'^\d{9}$', clean_duns))


def normalize_duns_number(duns: str) -> Optional[str]:
    """
    Normalize DUNS number to standard format.
    
    Args:
        duns: DUNS number to normalize.
        
    Returns:
        Normalized DUNS number or None if invalid.
    """
    if not is_valid_duns_number(duns):
        return None
    
    # Remove any formatting and return 9 digits
    return re.sub(r'[-\s]', '', duns)


def is_valid_crunchbase_url(url: str) -> bool:
    """
    Validate Crunchbase company URL.
    
    Args:
        url: URL to validate.
        
    Returns:
        True if valid Crunchbase URL.
    """
    if not isinstance(url, str):
        return False
    
    try:
        parsed = urlparse(url)
        
        # Check domain
        valid_domains = ['crunchbase.com', 'www.crunchbase.com']
        if parsed.netloc not in valid_domains:
            return False
        
        # Check path for organization format
        path_pattern = r'^/organization/[a-zA-Z0-9\-]+/?$'
        return bool(re.match(path_pattern, parsed.path))
    
    except Exception:
        return False


def extract_crunchbase_company_slug(url: str) -> Optional[str]:
    """
    Extract company slug from Crunchbase URL.
    
    Args:
        url: Crunchbase URL.
        
    Returns:
        Company slug or None if invalid URL.
    """
    if not is_valid_crunchbase_url(url):
        return None
    
    try:
        parsed = urlparse(url)
        match = re.match(r'^/organization/([a-zA-Z0-9\-]+)/?$', parsed.path)
        return match.group(1) if match else None
    
    except Exception:
        return None


def is_valid_company_name(name: str) -> bool:
    """
    Validate company name format.
    
    Args:
        name: Company name to validate.
        
    Returns:
        True if valid company name.
    """
    if not isinstance(name, str):
        return False
    
    # Basic validation: not empty, reasonable length, contains letters
    name = name.strip()
    if not name or len(name) < 2 or len(name) > 200:
        return False
    
    # Must contain at least one letter
    return bool(re.search(r'[a-zA-Z]', name))


def normalize_company_name(name: str) -> Optional[str]:
    """
    Normalize company name for consistent processing.
    
    Args:
        name: Company name to normalize.
        
    Returns:
        Normalized company name or None if invalid.
    """
    if not is_valid_company_name(name):
        return None
    
    # Basic normalization
    normalized = name.strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def is_valid_email_domain(email: str) -> bool:
    """
    Validate email format and extract domain.
    
    Args:
        email: Email address to validate.
        
    Returns:
        True if valid email format.
    """
    if not isinstance(email, str):
        return False
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def extract_domain_from_email(email: str) -> Optional[str]:
    """
    Extract domain from email address.
    
    Args:
        email: Email address.
        
    Returns:
        Domain or None if invalid email.
    """
    if not is_valid_email_domain(email):
        return None
    
    return email.split('@')[1].lower()


def is_valid_website_url(url: str) -> bool:
    """
    Validate website URL format.
    
    Args:
        url: URL to validate.
        
    Returns:
        True if valid website URL.
    """
    if not isinstance(url, str):
        return False
    
    try:
        parsed = urlparse(url)
        
        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Valid schemes
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Basic domain validation
        domain_pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(domain_pattern, parsed.netloc))
    
    except Exception:
        return False


def normalize_website_url(url: str) -> Optional[str]:
    """
    Normalize website URL to standard format.
    
    Args:
        url: URL to normalize.
        
    Returns:
        Normalized URL or None if invalid.
    """
    if not isinstance(url, str):
        return None
    
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    if not is_valid_website_url(url):
        return None
    
    try:
        parsed = urlparse(url)
        
        # Rebuild URL with normalized components
        normalized = f"{parsed.scheme}://{parsed.netloc.lower()}"
        
        if parsed.path and parsed.path != '/':
            normalized += parsed.path.rstrip('/')
        
        return normalized
    
    except Exception:
        return None


def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from.
        
    Returns:
        Domain or None if invalid URL.
    """
    normalized_url = normalize_website_url(url)
    if not normalized_url:
        return None
    
    try:
        parsed = urlparse(normalized_url)
        return parsed.netloc.lower()
    
    except Exception:
        return None


def validate_company_identifiers(
    company_names: Optional[List[str]] = None,
    duns_numbers: Optional[List[str]] = None,
    crunchbase_urls: Optional[List[str]] = None,
    website_urls: Optional[List[str]] = None,
    email_domains: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validate multiple types of company identifiers.
    
    Args:
        company_names: List of company names.
        duns_numbers: List of DUNS numbers.
        crunchbase_urls: List of Crunchbase URLs.
        website_urls: List of website URLs.
        email_domains: List of email addresses for domain extraction.
        
    Returns:
        Validation results with normalized identifiers.
    """
    results = {
        "valid": {
            "company_names": [],
            "duns_numbers": [],
            "crunchbase_urls": [],
            "website_urls": [],
            "domains": set(),
        },
        "invalid": {
            "company_names": [],
            "duns_numbers": [],
            "crunchbase_urls": [],
            "website_urls": [],
            "email_domains": [],
        },
        "normalized": {
            "company_names": [],
            "duns_numbers": [],
            "crunchbase_company_slugs": [],
            "website_urls": [],
            "domains": [],
        }
    }
    
    # Validate company names
    if company_names:
        for name in company_names:
            normalized = normalize_company_name(name)
            if normalized:
                results["valid"]["company_names"].append(name)
                results["normalized"]["company_names"].append(normalized)
            else:
                results["invalid"]["company_names"].append(name)
    
    # Validate DUNS numbers
    if duns_numbers:
        for duns in duns_numbers:
            normalized = normalize_duns_number(duns)
            if normalized:
                results["valid"]["duns_numbers"].append(duns)
                results["normalized"]["duns_numbers"].append(normalized)
            else:
                results["invalid"]["duns_numbers"].append(duns)
    
    # Validate Crunchbase URLs
    if crunchbase_urls:
        for url in crunchbase_urls:
            if is_valid_crunchbase_url(url):
                slug = extract_crunchbase_company_slug(url)
                results["valid"]["crunchbase_urls"].append(url)
                if slug:
                    results["normalized"]["crunchbase_company_slugs"].append(slug)
            else:
                results["invalid"]["crunchbase_urls"].append(url)
    
    # Validate website URLs
    if website_urls:
        for url in website_urls:
            normalized = normalize_website_url(url)
            if normalized:
                results["valid"]["website_urls"].append(url)
                results["normalized"]["website_urls"].append(normalized)
                
                # Extract domain
                domain = extract_domain_from_url(normalized)
                if domain:
                    results["valid"]["domains"].add(domain)
            else:
                results["invalid"]["website_urls"].append(url)
    
    # Validate email domains
    if email_domains:
        for email in email_domains:
            domain = extract_domain_from_email(email)
            if domain:
                results["valid"]["domains"].add(domain)
            else:
                results["invalid"]["email_domains"].append(email)
    
    # Convert domain set to list
    results["normalized"]["domains"] = list(results["valid"]["domains"])
    results["valid"]["domains"] = list(results["valid"]["domains"])
    
    return results


def is_valid_ein_number(ein: str) -> bool:
    """
    Validate EIN (Employer Identification Number) format.
    
    Args:
        ein: EIN to validate.
        
    Returns:
        True if valid EIN format.
    """
    if not isinstance(ein, str):
        return False
    
    # Remove any hyphens
    clean_ein = ein.replace('-', '')
    
    # Must be exactly 9 digits
    if not re.match(r'^\d{9}$', clean_ein):
        return False
    
    # First two digits must be valid prefixes (10-99, excluding some)
    prefix = int(clean_ein[:2])
    invalid_prefixes = {7, 8, 9, 17, 18, 19, 28, 29, 49, 69, 70, 78, 79, 89}
    
    return 10 <= prefix <= 99 and prefix not in invalid_prefixes


def normalize_ein_number(ein: str) -> Optional[str]:
    """
    Normalize EIN number to standard format (XX-XXXXXXX).
    
    Args:
        ein: EIN to normalize.
        
    Returns:
        Normalized EIN or None if invalid.
    """
    if not is_valid_ein_number(ein):
        return None
    
    clean_ein = ein.replace('-', '')
    return f"{clean_ein[:2]}-{clean_ein[2:]}" 