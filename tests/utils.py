"""
Utility functions for testing Apify actors.
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime


def assert_actor_output_structure(output: List[Dict[str, Any]], expected_fields: List[str]):
    """
    Assert that actor output has the expected structure.
    
    Args:
        output: The actor output data
        expected_fields: List of required fields in each output item
    """
    assert isinstance(output, list), "Output should be a list"
    
    if output:  # Only check structure if there are items
        for item in output:
            assert isinstance(item, dict), "Each output item should be a dictionary"
            for field in expected_fields:
                assert field in item, f"Required field '{field}' missing from output"


def assert_linkedin_profile_structure(profile_data: Dict[str, Any]):
    """Assert LinkedIn profile data has correct structure."""
    required_fields = ["profile", "experience", "education", "skills"]
    
    for field in required_fields:
        assert field in profile_data, f"Required field '{field}' missing"
    
    # Check profile section
    profile = profile_data["profile"]
    profile_required = ["fullName", "headline", "profileUrl"]
    for field in profile_required:
        assert field in profile, f"Required profile field '{field}' missing"
    
    # Check arrays are lists
    assert isinstance(profile_data["experience"], list), "Experience should be a list"
    assert isinstance(profile_data["education"], list), "Education should be a list"
    assert isinstance(profile_data["skills"], list), "Skills should be a list"


def assert_social_media_post_structure(post_data: Dict[str, Any]):
    """Assert social media post data has correct structure."""
    required_fields = ["id", "text", "url", "timestamp", "author"]
    
    for field in required_fields:
        assert field in post_data, f"Required field '{field}' missing"
    
    # Check author section if present
    if "author" in post_data and post_data["author"]:
        author = post_data["author"]
        author_required = ["name", "username"]
        for field in author_required:
            assert field in author, f"Required author field '{field}' missing"


def assert_company_data_structure(company_data: Dict[str, Any]):
    """Assert company data has correct structure."""
    required_fields = ["name", "website", "industry"]
    
    for field in required_fields:
        assert field in company_data, f"Required field '{field}' missing"


def validate_url_format(url: str, expected_domain: Optional[str] = None) -> bool:
    """
    Validate URL format and optionally check domain.
    
    Args:
        url: URL to validate
        expected_domain: Expected domain (e.g., "linkedin.com")
    
    Returns:
        True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    if not url.startswith(("http://", "https://")):
        return False
    
    if expected_domain and expected_domain not in url:
        return False
    
    return True


def validate_date_format(date_str: str) -> bool:
    """
    Validate date string format (YYYY-MM or YYYY).
    
    Args:
        date_str: Date string to validate
    
    Returns:
        True if valid format, False otherwise
    """
    if not date_str or not isinstance(date_str, str):
        return False
    
    # Accept YYYY format
    if len(date_str) == 4 and date_str.isdigit():
        return True
    
    # Accept YYYY-MM format
    if len(date_str) == 7 and date_str[4] == "-":
        year, month = date_str.split("-")
        if year.isdigit() and month.isdigit():
            return 1 <= int(month) <= 12
    
    return False


def create_mock_run_result(
    status: str = "SUCCEEDED",
    compute_units: float = 0.1,
    items: Optional[List[Dict[str, Any]]] = None
) -> Any:
    """
    Create a mock actor run result for testing.
    
    Args:
        status: Run status (SUCCEEDED, FAILED, RUNNING, etc.)
        compute_units: Compute units consumed
        items: Output items
    
    Returns:
        Mock ActorRunResult object
    """
    from app.actors.base import ActorRunResult
    from datetime import datetime
    from decimal import Decimal
    
    if items is None:
        items = []
    
    return ActorRunResult(
        run_id=f"test_run_{datetime.now().timestamp()}",
        actor_id="test_actor",
        status=status,
        started_at=datetime.now(),
        finished_at=datetime.now() if status in ["SUCCEEDED", "FAILED"] else None,
        items=items,
        items_count=len(items),
        duration_secs=300.0 if status in ["SUCCEEDED", "FAILED"] else None,
        cost=Decimal(str(compute_units * 0.001)),
        error_message=None if status == "SUCCEEDED" else "Test error",
        success=status == "SUCCEEDED",
        metadata={"computeUnits": compute_units}
    )


def sanitize_test_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize test data by removing sensitive information.
    
    Args:
        data: Data to sanitize
    
    Returns:
        Sanitized data
    """
    sanitized = data.copy()
    
    # Remove potentially sensitive fields
    sensitive_fields = ["email", "phone", "address", "api_key", "token"]
    
    def remove_sensitive(obj):
        if isinstance(obj, dict):
            return {k: remove_sensitive(v) for k, v in obj.items() 
                   if k.lower() not in sensitive_fields}
        elif isinstance(obj, list):
            return [remove_sensitive(item) for item in obj]
        else:
            return obj
    
    return remove_sensitive(sanitized)


def compare_actor_outputs(actual: List[Dict[str, Any]], expected: List[Dict[str, Any]], 
                         ignore_fields: Optional[List[str]] = None) -> bool:
    """
    Compare actor outputs while ignoring specified fields.
    
    Args:
        actual: Actual output
        expected: Expected output
        ignore_fields: Fields to ignore in comparison
    
    Returns:
        True if outputs match (ignoring specified fields)
    """
    if ignore_fields is None:
        ignore_fields = ["timestamp", "scrapedAt", "runId"]
    
    def clean_item(item):
        if isinstance(item, dict):
            return {k: clean_item(v) for k, v in item.items() 
                   if k not in ignore_fields}
        elif isinstance(item, list):
            return [clean_item(i) for i in item]
        else:
            return item
    
    cleaned_actual = [clean_item(item) for item in actual]
    cleaned_expected = [clean_item(item) for item in expected]
    
    return cleaned_actual == cleaned_expected 