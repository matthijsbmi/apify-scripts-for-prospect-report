"""
Unit tests for LinkedIn Profile Bulk Scraper actor.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from app.actors.linkedin.profile_scraper import LinkedInProfileScraper
from app.core.apify_client import ApifyService
from app.cost.manager import CostManager
from tests.fixtures import LINKEDIN_PROFILE_INPUT, LINKEDIN_PROFILE_OUTPUT, LINKEDIN_ERROR_SCENARIOS
from tests.utils import (
    assert_linkedin_profile_structure,
    validate_url_format,
    create_mock_run_result
)


class TestLinkedInProfileScraper:
    """Test suite for LinkedIn Profile Bulk Scraper."""

    @pytest.fixture
    def mock_apify_service(self):
        """Create mock Apify service for testing."""
        service = MagicMock(spec=ApifyService)
        service.is_available.return_value = True
        service.run_actor_async = AsyncMock()
        service.run_actor = MagicMock()
        return service

    @pytest.fixture
    def cost_manager(self):
        """Create cost manager for testing."""
        return CostManager()

    @pytest.fixture
    def scraper(self, mock_apify_service, cost_manager):
        """Create LinkedIn Profile Scraper instance."""
        return LinkedInProfileScraper(
            apify_service=mock_apify_service,
            cost_manager=cost_manager
        )

    @pytest.mark.unit
    def test_scraper_initialization(self, scraper):
        """Test scraper initializes correctly."""
        assert scraper.actor_id == "LpVuK3Zozwuipa5bp"
        assert scraper.name == "LinkedIn Profile Bulk Scraper"
        assert scraper.apify_service is not None
        assert scraper.cost_manager is not None

    @pytest.mark.unit
    def test_validate_input_valid(self, scraper):
        """Test input validation with valid data."""
        # Should not raise any exception
        scraper.validate_input(LINKEDIN_PROFILE_INPUT)

    @pytest.mark.unit
    def test_validate_input_missing_urls(self, scraper):
        """Test input validation with missing profile URLs."""
        invalid_input = {"includeSkills": True}
        
        with pytest.raises(ValueError, match="profileUrls is required"):
            scraper.validate_input(invalid_input)

    @pytest.mark.unit
    def test_validate_input_empty_urls(self, scraper):
        """Test input validation with empty profile URLs list."""
        invalid_input = {"profileUrls": []}
        
        with pytest.raises(ValueError, match="At least one profile URL is required"):
            scraper.validate_input(invalid_input)

    @pytest.mark.unit
    def test_validate_input_invalid_urls(self, scraper):
        """Test input validation with invalid URLs."""
        invalid_input = {
            "profileUrls": ["not-a-url", "https://facebook.com/profile"]
        }
        
        with pytest.raises(ValueError, match="Invalid LinkedIn URL"):
            scraper.validate_input(invalid_input)

    @pytest.mark.unit
    def test_validate_input_too_many_urls(self, scraper):
        """Test input validation with too many URLs."""
        invalid_input = {
            "profileUrls": [f"https://linkedin.com/in/user{i}" for i in range(101)]
        }
        
        with pytest.raises(ValueError, match="Maximum 100 profile URLs allowed"):
            scraper.validate_input(invalid_input)

    @pytest.mark.unit
    def test_estimate_cost(self, scraper):
        """Test cost estimation."""
        cost_estimate = scraper.estimate_cost(LINKEDIN_PROFILE_INPUT)
        
        assert cost_estimate["estimated_cost"] > 0
        assert cost_estimate["compute_units"] > 0
        assert cost_estimate["cost_breakdown"]["base_cost"] > 0
        assert "profiles" in cost_estimate["cost_breakdown"]

    @pytest.mark.unit
    def test_transform_output(self, scraper):
        """Test output transformation."""
        mock_raw_output = [
            {
                "profile": {
                    "fullName": "John Doe",
                    "headline": "Software Engineer",
                    "profileUrl": "https://linkedin.com/in/john-doe"
                },
                "experience": [],
                "education": [],
                "skills": []
            }
        ]
        
        transformed = scraper.transform_output(mock_raw_output)
        
        assert isinstance(transformed, list)
        assert len(transformed) == 1
        assert "profile" in transformed[0]
        assert "experience" in transformed[0]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_actor_success(self, scraper, mock_apify_service):
        """Test successful actor run."""
        # Mock successful run result
        mock_result = create_mock_run_result(
            status="SUCCEEDED",
            compute_units=0.25,
            items=LINKEDIN_PROFILE_OUTPUT
        )
        mock_apify_service.run_actor_async.return_value = mock_result
        
        result = await scraper.run_actor_async(LINKEDIN_PROFILE_INPUT)
        
        assert result["success"] is True
        assert len(result["items"]) == 2
        assert result["run"]["status"] == "SUCCEEDED"
        
        # Verify the call was made correctly
        mock_apify_service.run_actor_async.assert_called_once_with(
            actor_id="LpVuK3Zozwuipa5bp",
            run_input=LINKEDIN_PROFILE_INPUT,
            timeout=600
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_actor_failure(self, scraper, mock_apify_service):
        """Test actor run failure."""
        # Mock failed run result
        mock_result = create_mock_run_result(status="FAILED")
        mock_result["success"] = False
        mock_result["error"] = "Actor run failed"
        mock_apify_service.run_actor_async.return_value = mock_result
        
        result = await scraper.run_actor_async(LINKEDIN_PROFILE_INPUT)
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.unit
    def test_get_default_input(self, scraper):
        """Test default input generation."""
        default_input = scraper.get_default_input()
        
        assert "includeSkills" in default_input
        assert "includeEducation" in default_input
        assert "includeExperience" in default_input
        assert default_input["includeSkills"] is True
        assert default_input["includeEducation"] is True

    @pytest.mark.unit
    def test_output_structure_validation(self, scraper):
        """Test that output has correct structure."""
        for profile_data in LINKEDIN_PROFILE_OUTPUT:
            assert_linkedin_profile_structure(profile_data)

    @pytest.mark.unit 
    def test_url_validation_helper(self):
        """Test URL validation helper function."""
        valid_urls = [
            "https://www.linkedin.com/in/john-doe/",
            "https://linkedin.com/in/jane-smith",
            "http://www.linkedin.com/in/test-user/"
        ]
        
        invalid_urls = [
            "https://facebook.com/john.doe",
            "not-a-url",
            "https://twitter.com/johndoe",
            ""
        ]
        
        for url in valid_urls:
            assert validate_url_format(url, "linkedin.com") is True
            
        for url in invalid_urls:
            assert validate_url_format(url, "linkedin.com") is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_scenarios(self, scraper, mock_apify_service):
        """Test various error scenarios."""
        error_scenarios = LINKEDIN_ERROR_SCENARIOS
        
        for scenario_name, scenario_data in error_scenarios.items():
            if "expected_error" in scenario_data:
                # Mock error response
                mock_result = create_mock_run_result(status="FAILED")
                mock_result["success"] = False
                mock_result["error"] = scenario_data["expected_error"]
                mock_apify_service.run_actor_async.return_value = mock_result
                
                result = await scraper.run_actor_async(scenario_data["input"])
                
                assert result["success"] is False
                assert scenario_data["expected_error"] in result.get("error", "")
            
            elif "expected_result" in scenario_data:
                # Mock empty result for private profiles
                mock_result = create_mock_run_result(
                    status="SUCCEEDED",
                    items=scenario_data["expected_result"]
                )
                mock_apify_service.run_actor_async.return_value = mock_result
                
                result = await scraper.run_actor_async(scenario_data["input"])
                
                assert result["success"] is True
                assert len(result["items"]) == len(scenario_data["expected_result"])

    @pytest.mark.unit
    def test_cost_calculation_accuracy(self, scraper):
        """Test cost calculation accuracy."""
        # Test with different input sizes
        test_cases = [
            {"profileUrls": ["https://linkedin.com/in/test1"]},  # 1 profile
            {"profileUrls": [f"https://linkedin.com/in/test{i}" for i in range(10)]},  # 10 profiles
            {"profileUrls": [f"https://linkedin.com/in/test{i}" for i in range(50)]},  # 50 profiles
        ]
        
        previous_cost = 0
        for test_input in test_cases:
            cost_estimate = scraper.estimate_cost(test_input)
            current_cost = cost_estimate["estimated_cost"]
            
            # Cost should increase with more profiles
            assert current_cost > previous_cost
            assert cost_estimate["compute_units"] > 0
            
            previous_cost = current_cost

    @pytest.mark.unit
    def test_input_sanitization(self, scraper):
        """Test input data sanitization."""
        input_with_extra_fields = {
            **LINKEDIN_PROFILE_INPUT,
            "malicious_field": "<script>alert('xss')</script>",
            "api_key": "secret-key-123"
        }
        
        # Should not raise exception and should sanitize
        scraper.validate_input(input_with_extra_fields)
        
        # The sanitization would happen in the transform_input method if implemented
        # For now, we just ensure validation passes

    @pytest.mark.unit
    @pytest.mark.asyncio 
    async def test_concurrent_requests(self, scraper, mock_apify_service):
        """Test handling of concurrent requests."""
        mock_result = create_mock_run_result(
            status="SUCCEEDED",
            items=LINKEDIN_PROFILE_OUTPUT[:1]  # Return just one profile
        )
        mock_apify_service.run_actor_async.return_value = mock_result
        
        # Simulate multiple concurrent requests
        import asyncio
        tasks = [
            scraper.run_actor_async({"profileUrls": [f"https://linkedin.com/in/test{i}"]})
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert result["success"] is True
        
        # Should have made 3 calls
        assert mock_apify_service.run_actor_async.call_count == 3 