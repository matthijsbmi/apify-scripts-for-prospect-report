"""
Integration tests for LinkedIn Profile Bulk Scraper actor.

These tests verify integration with the Apify API and service layer.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from app.actors.linkedin.profile_scraper import LinkedInProfileScraper
from app.core.apify_client import ApifyService
from app.cost.manager import CostManager
from app.services.storage import InMemoryStorageService
from tests.fixtures import LINKEDIN_PROFILE_INPUT, LINKEDIN_PROFILE_OUTPUT
from tests.utils import assert_linkedin_profile_structure


class TestLinkedInProfileScraperIntegration:
    """Integration test suite for LinkedIn Profile Scraper."""

    @pytest.fixture
    def storage_service(self):
        """Create storage service for integration testing."""
        return InMemoryStorageService()

    @pytest.fixture
    def cost_manager(self):
        """Create cost manager for integration testing."""
        return CostManager()

    @pytest.fixture
    def real_apify_service(self):
        """Create real Apify service if API token is available."""
        api_token = os.getenv("APIFY_API_TOKEN")
        if api_token:
            return ApifyService(api_token)
        else:
            pytest.skip("APIFY_API_TOKEN not available for integration testing")

    @pytest.fixture
    def mock_apify_service_integration(self):
        """Create a more realistic mock for integration testing."""
        service = MagicMock(spec=ApifyService)
        service.is_available.return_value = True
        
        # Mock realistic API responses
        def mock_run_actor_async(actor_id, run_input, timeout=600):
            """Mock that simulates real API behavior."""
            import asyncio
            import time
            
            async def simulate_run():
                # Simulate API delay
                await asyncio.sleep(0.1)
                
                # Return realistic response based on input
                profile_count = len(run_input.get("profileUrls", []))
                compute_units = profile_count * 0.05  # Realistic compute unit calculation
                
                return {
                    "run": {
                        "id": f"test_run_{int(time.time())}",
                        "actorId": actor_id,
                        "status": "SUCCEEDED",
                        "startedAt": "2024-01-01T10:00:00.000Z",
                        "finishedAt": "2024-01-01T10:05:00.000Z",
                        "computeUnits": compute_units,
                        "defaultDatasetId": "test_dataset_123"
                    },
                    "items": LINKEDIN_PROFILE_OUTPUT[:profile_count],  # Return appropriate number of profiles
                    "success": True
                }
            
            return simulate_run()
        
        service.run_actor_async.side_effect = mock_run_actor_async
        return service

    @pytest.fixture
    def scraper_with_real_service(self, real_apify_service, cost_manager):
        """Create scraper with real Apify service."""
        return LinkedInProfileScraper(
            apify_service=real_apify_service,
            cost_manager=cost_manager
        )

    @pytest.fixture
    def scraper_with_mock_service(self, mock_apify_service_integration, cost_manager):
        """Create scraper with realistic mock service."""
        return LinkedInProfileScraper(
            apify_service=mock_apify_service_integration,
            cost_manager=cost_manager
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_scraping_workflow_mock(self, scraper_with_mock_service, storage_service):
        """Test complete scraping workflow with mocked service."""
        scraper = scraper_with_mock_service
        
        # Step 1: Validate input
        scraper.validate_input(LINKEDIN_PROFILE_INPUT)
        
        # Step 2: Estimate cost
        cost_estimate = scraper.estimate_cost(LINKEDIN_PROFILE_INPUT)
        assert cost_estimate["estimated_cost"] > 0
        
        # Step 3: Run the actor
        result = await scraper.run_actor_async(LINKEDIN_PROFILE_INPUT)
        
        # Step 4: Verify result
        assert result["success"] is True
        assert len(result["items"]) > 0
        assert result["run"]["status"] == "SUCCEEDED"
        
        # Step 5: Validate output structure
        for profile_data in result["items"]:
            assert_linkedin_profile_structure(profile_data)
        
        # Step 6: Store results
        run_id = result["run"]["id"]
        await storage_service.store_actor_result(
            actor_id=scraper.actor_id,
            run_id=run_id,
            result=result
        )
        
        # Step 7: Retrieve and verify stored data
        stored_result = await storage_service.get_actor_result(scraper.actor_id, run_id)
        assert stored_result is not None
        assert stored_result["success"] is True

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_real_api_call(self, scraper_with_real_service):
        """Test with real Apify API call (requires API token)."""
        scraper = scraper_with_real_service
        
        # Use minimal input for real API test
        minimal_input = {
            "profileUrls": ["https://www.linkedin.com/in/williamhgates/"],  # Public profile
            "includeSkills": False,
            "includeEducation": False,
            "includeExperience": False
        }
        
        # Validate input first
        scraper.validate_input(minimal_input)
        
        # Run the actor
        result = await scraper.run_actor_async(minimal_input)
        
        # Verify basic result structure
        assert "success" in result
        assert "run" in result
        assert "items" in result
        
        if result["success"]:
            # If successful, verify output structure
            assert len(result["items"]) >= 0  # May be empty for private profiles
            for profile_data in result["items"]:
                assert "profile" in profile_data
                assert "profileUrl" in profile_data["profile"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cost_tracking_integration(self, scraper_with_mock_service):
        """Test cost tracking throughout the workflow."""
        scraper = scraper_with_mock_service
        cost_manager = scraper.cost_manager
        
        # Get initial cost
        initial_total = cost_manager.get_total_cost()
        
        # Estimate cost
        cost_estimate = scraper.estimate_cost(LINKEDIN_PROFILE_INPUT)
        estimated_amount = cost_estimate["estimated_cost"]
        
        # Run actor
        result = await scraper.run_actor_async(LINKEDIN_PROFILE_INPUT)
        
        # Verify cost was tracked
        if result["success"]:
            actual_cost = result["run"]["computeUnits"] * cost_manager.compute_unit_cost
            cost_manager.add_actor_cost(
                actor_id=scraper.actor_id,
                cost=actual_cost,
                compute_units=result["run"]["computeUnits"]
            )
            
            final_total = cost_manager.get_total_cost()
            assert final_total > initial_total
            
            # Cost should be reasonably close to estimate (within 50%)
            assert abs(actual_cost - estimated_amount) / estimated_amount < 0.5

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, mock_apify_service_integration, cost_manager):
        """Test error handling in integration context."""
        # Create scraper with service that will fail
        def mock_failing_run(*args, **kwargs):
            async def fail():
                return {
                    "run": {
                        "id": "failed_run_123",
                        "status": "FAILED",
                        "statusMessage": "Profile not found"
                    },
                    "items": [],
                    "success": False,
                    "error": "Profile not found"
                }
            return fail()
        
        mock_apify_service_integration.run_actor_async.side_effect = mock_failing_run
        
        scraper = LinkedInProfileScraper(
            apify_service=mock_apify_service_integration,
            cost_manager=cost_manager
        )
        
        # Test with invalid profile
        invalid_input = {
            "profileUrls": ["https://www.linkedin.com/in/nonexistent-profile-12345/"]
        }
        
        result = await scraper.run_actor_async(invalid_input)
        
        assert result["success"] is False
        assert "error" in result
        assert result["run"]["status"] == "FAILED"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_profiles_workflow(self, scraper_with_mock_service):
        """Test workflow with multiple profiles."""
        scraper = scraper_with_mock_service
        
        # Test with multiple profiles
        multi_profile_input = {
            "profileUrls": [
                "https://www.linkedin.com/in/profile1/",
                "https://www.linkedin.com/in/profile2/",
                "https://www.linkedin.com/in/profile3/"
            ],
            "includeSkills": True,
            "includeEducation": True,
            "includeExperience": True
        }
        
        # Validate input
        scraper.validate_input(multi_profile_input)
        
        # Estimate cost
        cost_estimate = scraper.estimate_cost(multi_profile_input)
        
        # Cost should scale with number of profiles
        single_profile_cost = scraper.estimate_cost({
            "profileUrls": ["https://www.linkedin.com/in/profile1/"]
        })["estimated_cost"]
        
        assert cost_estimate["estimated_cost"] > single_profile_cost
        
        # Run actor
        result = await scraper.run_actor_async(multi_profile_input)
        
        assert result["success"] is True
        # Should return up to 3 profiles (limited by our mock data)
        assert len(result["items"]) <= 3

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_service_availability_check(self, cost_manager):
        """Test service availability checking."""
        # Test with unavailable service
        unavailable_service = MagicMock(spec=ApifyService)
        unavailable_service.is_available.return_value = False
        
        scraper = LinkedInProfileScraper(
            apify_service=unavailable_service,
            cost_manager=cost_manager
        )
        
        # Should handle unavailable service gracefully
        with pytest.raises(Exception):
            await scraper.run_actor_async(LINKEDIN_PROFILE_INPUT)

    @pytest.mark.integration
    def test_configuration_integration(self, scraper_with_mock_service):
        """Test configuration and settings integration."""
        scraper = scraper_with_mock_service
        
        # Test actor configuration
        assert scraper.actor_id == "LpVuK3Zozwuipa5bp"
        assert scraper.name == "LinkedIn Profile Bulk Scraper"
        
        # Test default configuration
        default_input = scraper.get_default_input()
        assert isinstance(default_input, dict)
        assert "includeSkills" in default_input
        
        # Validate default input
        default_input["profileUrls"] = ["https://www.linkedin.com/in/test/"]
        scraper.validate_input(default_input)  # Should not raise 