"""
Test configuration and shared fixtures for Apify Actor testing.
"""

import os
import pytest
import asyncio
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock

from app.core.apify_client import ApifyService
from app.core.config import settings
from app.cost.manager import CostManager
from app.services.storage import InMemoryStorageService


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_apify_service():
    """Create a mock Apify service for testing."""
    service = MagicMock(spec=ApifyService)
    service.is_available.return_value = True
    service.run_actor_async = AsyncMock()
    service.run_actor = MagicMock()
    service.get_actor_info.return_value = {
        "id": "test_actor",
        "name": "Test Actor",
        "description": "Test actor for unit testing"
    }
    return service


@pytest.fixture
def real_apify_service():
    """Create a real Apify service for integration testing."""
    # Only create if API token is available
    api_token = os.getenv("APIFY_API_TOKEN")
    if api_token:
        return ApifyService(api_token)
    else:
        pytest.skip("APIFY_API_TOKEN not available for integration testing")


@pytest.fixture
def cost_manager():
    """Create a cost manager instance for testing."""
    return CostManager()


@pytest.fixture
def storage_service():
    """Create an in-memory storage service for testing."""
    return InMemoryStorageService()


@pytest.fixture
def sample_linkedin_profile_input():
    """Sample input data for LinkedIn Profile Scraper."""
    return {
        "profileUrls": [
            "https://www.linkedin.com/in/sample-profile/",
            "https://www.linkedin.com/in/another-profile/"
        ],
        "includeSkills": True,
        "includeEducation": True,
        "includeExperience": True
    }


@pytest.fixture
def sample_linkedin_profile_output():
    """Sample output data for LinkedIn Profile Scraper."""
    return [
        {
            "profile": {
                "fullName": "John Doe",
                "headline": "Software Engineer at TechCorp",
                "location": "San Francisco, CA",
                "profileUrl": "https://www.linkedin.com/in/sample-profile/",
                "connectionsCount": 500,
                "followersCount": 1200
            },
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "TechCorp",
                    "startDate": "2022-01",
                    "endDate": None,
                    "location": "San Francisco, CA",
                    "description": "Developing web applications"
                }
            ],
            "education": [
                {
                    "school": "University of Technology",
                    "degree": "Bachelor of Science",
                    "field": "Computer Science",
                    "startDate": "2018",
                    "endDate": "2022"
                }
            ],
            "skills": [
                {"name": "Python", "endorsements": 25},
                {"name": "JavaScript", "endorsements": 18},
                {"name": "React", "endorsements": 12}
            ]
        }
    ]


@pytest.fixture
def mock_actor_run_result():
    """Mock result for successful actor run."""
    return {
        "run": {
            "id": "test_run_123",
            "actorId": "test_actor",
            "status": "SUCCEEDED",
            "startedAt": "2023-01-01T10:00:00.000Z",
            "finishedAt": "2023-01-01T10:05:00.000Z",
            "computeUnits": 0.1,
            "defaultDatasetId": "test_dataset_456"
        },
        "items": [],
        "success": True
    }


@pytest.fixture
def mock_failed_actor_run():
    """Mock result for failed actor run."""
    return {
        "run": {
            "id": "test_run_456",
            "actorId": "test_actor",
            "status": "FAILED",
            "startedAt": "2023-01-01T10:00:00.000Z",
            "finishedAt": "2023-01-01T10:02:00.000Z",
            "statusMessage": "Actor run failed due to timeout"
        },
        "items": [],
        "success": False,
        "error": "Actor run failed due to timeout"
    }


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Clean up after each test."""
    yield
    # Any cleanup code here


# Test environment configuration
@pytest.fixture(scope="session", autouse=True)
def configure_test_environment():
    """Configure test environment settings."""
    # Set test-specific environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "WARNING"  # Reduce log noise in tests
    
    yield
    
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"] 