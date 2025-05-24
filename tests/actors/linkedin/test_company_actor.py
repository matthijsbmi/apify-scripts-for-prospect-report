"""
Unit tests for LinkedIn Company Profile Scraper actor.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from app.actors.linkedin.company_actor import LinkedInCompanyActor
from app.actors.base import ActorRunResult
from tests.fixtures import LINKEDIN_COMPANY_INPUT, LINKEDIN_COMPANY_OUTPUT
from tests.utils import create_mock_run_result


class TestLinkedInCompanyActor:
    """Test suite for LinkedIn Company Profile Scraper."""

    @pytest.fixture
    def company_actor(self):
        """Create LinkedIn Company Actor instance."""
        return LinkedInCompanyActor()

    @pytest.mark.unit
    def test_actor_initialization(self, company_actor):
        """Test actor initializes correctly."""
        assert company_actor.actor_id == "sanjeta/linkedin-company-profile-scraper"

    @pytest.mark.unit
    def test_validate_single_url_valid(self, company_actor):
        """Test URL validation with valid company URL."""
        valid_url = "https://www.linkedin.com/company/apifytech"
        
        # This should not raise any exception
        from app.actors.linkedin.validators import is_valid_linkedin_company_url
        assert is_valid_linkedin_company_url(valid_url) == True

    @pytest.mark.unit
    def test_validate_single_url_invalid(self, company_actor):
        """Test URL validation with invalid URLs."""
        from app.actors.linkedin.validators import is_valid_linkedin_company_url
        
        invalid_urls = [
            "https://facebook.com/company/test",
            "https://linkedin.com/in/profile",  # profile URL, not company
            "not-a-url",
            "https://linkedin.com/company/123456",  # ID-based URL
            "",
            None
        ]
        
        for url in invalid_urls:
            assert is_valid_linkedin_company_url(url) == False

    @pytest.mark.unit
    def test_validate_multiple_urls_valid(self, company_actor):
        """Test URL validation with multiple valid URLs."""
        from app.actors.linkedin.validators import validate_linkedin_company_urls
        
        valid_urls = [
            "https://www.linkedin.com/company/apifytech",
            "https://linkedin.com/company/google",
            "https://www.linkedin.com/company/microsoft/"
        ]
        
        result = validate_linkedin_company_urls(valid_urls)
        assert len(result) == 3
        assert all(url in result for url in valid_urls)

    @pytest.mark.unit
    def test_validate_multiple_urls_mixed(self, company_actor):
        """Test URL validation with mix of valid and invalid URLs."""
        from app.actors.linkedin.validators import validate_linkedin_company_urls
        
        mixed_urls = [
            "https://www.linkedin.com/company/apifytech",  # valid
            "https://facebook.com/company/test",  # invalid
            "https://linkedin.com/company/google",  # valid
            "not-a-url"  # invalid
        ]
        
        result = validate_linkedin_company_urls(mixed_urls)
        assert len(result) == 2
        assert "https://www.linkedin.com/company/apifytech" in result
        assert "https://linkedin.com/company/google" in result

    @pytest.mark.unit
    def test_validate_empty_urls(self, company_actor):
        """Test URL validation with empty URL list."""
        from app.actors.linkedin.validators import validate_linkedin_company_urls
        
        result = validate_linkedin_company_urls([])
        assert result == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_scrape_companies_success(self, company_actor):
        """Test successful company scraping."""
        with patch.object(company_actor, 'run_async') as mock_run:
            # Mock successful run result
            mock_result = create_mock_run_result(
                status="SUCCEEDED",
                compute_units=0.5,
                items=LINKEDIN_COMPANY_OUTPUT
            )
            mock_run.return_value = mock_result
            
            result = await company_actor.scrape_companies(
                company_urls=LINKEDIN_COMPANY_INPUT,
                max_budget_usd=10.0
            )
            
            # Result should only contain metadata key (no duplication)
            assert "companies" not in result
            assert "metadata" in result
            
            # Check that metadata contains raw data (no duplication)
            metadata = result["metadata"]
            assert metadata is not None
            assert len(metadata.items) == 2
            
            first_company = metadata.items[0]
            assert isinstance(first_company, dict)
            assert first_company["company_name"] == "Apify"
            assert first_company["universal_name_id"] == "apifytech"
            assert first_company["industry"] == "IT Services and IT Consulting"
            assert len(first_company["employees"]) == 2
            assert len(first_company["locations"]) == 1
            
            # Verify the call was made correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            expected_input = {
                "urls": LINKEDIN_COMPANY_INPUT,
                "proxy": {"useApifyProxy": True}
            }
            assert call_args[1]["input_data"] == expected_input
            assert call_args[1]["max_budget"] == 10.0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_scrape_companies_no_valid_urls(self, company_actor):
        """Test scraping with no valid URLs."""
        invalid_urls = [
            "https://facebook.com/company/test",
            "not-a-url"
        ]
        
        with pytest.raises(ValueError, match="No valid LinkedIn company URLs provided"):
            await company_actor.scrape_companies(
                company_urls=invalid_urls,
                max_budget_usd=5.0
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_scrape_companies_actor_failure(self, company_actor):
        """Test handling of actor run failure."""
        with patch.object(company_actor, 'run_async') as mock_run:
            # Mock failed run result
            mock_result = create_mock_run_result(status="FAILED")
            mock_run.return_value = mock_result
            
            result = await company_actor.scrape_companies(
                company_urls=LINKEDIN_COMPANY_INPUT,
                max_budget_usd=5.0
            )
            
            # Should return metadata with no items
            assert "companies" not in result
            assert "metadata" in result
            assert result["metadata"].items is None or len(result["metadata"].items) == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_scrape_single_company_success(self, company_actor):
        """Test successful single company scraping."""
        with patch.object(company_actor, 'scrape_companies') as mock_scrape:
            # Mock the scrape_companies method with raw data in metadata
            mock_company_data = {
                "company_name": "Apify",
                "universal_name_id": "apifytech",
                "industry": "IT Services and IT Consulting"
            }
            mock_result = create_mock_run_result(
                status="SUCCEEDED",
                items=[mock_company_data]
            )
            mock_scrape.return_value = {
                "metadata": mock_result
            }
            
            result = await company_actor.scrape_company(
                company_url="https://www.linkedin.com/company/apifytech",
                max_budget_usd=5.0
            )
            
            assert result is not None
            assert isinstance(result, dict)
            assert result["company_name"] == "Apify"
            assert result["universal_name_id"] == "apifytech"
            
            # Verify the call was made correctly
            mock_scrape.assert_called_once_with(
                company_urls=["https://www.linkedin.com/company/apifytech"],
                proxy_configuration=None,
                max_budget_usd=5.0
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_scrape_single_company_invalid_url(self, company_actor):
        """Test single company scraping with invalid URL."""
        invalid_url = "https://facebook.com/company/test"
        
        with pytest.raises(ValueError, match="Invalid LinkedIn company URL"):
            await company_actor.scrape_company(
                company_url=invalid_url,
                max_budget_usd=5.0
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_scrape_single_company_not_found(self, company_actor):
        """Test single company scraping when company is not found."""
        with patch.object(company_actor, 'scrape_companies') as mock_scrape:
            # Mock empty result
            mock_result = create_mock_run_result(
                status="SUCCEEDED",
                items=[]
            )
            mock_scrape.return_value = {
                "metadata": mock_result
            }
            
            result = await company_actor.scrape_company(
                company_url="https://www.linkedin.com/company/nonexistent",
                max_budget_usd=5.0
            )
            
            assert result is None

    @pytest.mark.unit
    def test_raw_company_data_structure(self, company_actor):
        """Test that raw company data has expected structure."""
        raw_data = LINKEDIN_COMPANY_OUTPUT[0]  # Apify company data
        
        # Verify raw data structure
        assert isinstance(raw_data, dict)
        assert "company_name" in raw_data
        assert "universal_name_id" in raw_data
        assert "industry" in raw_data
        assert raw_data["company_name"] == "Apify"
        assert raw_data["universal_name_id"] == "apifytech"
        assert raw_data["industry"] == "IT Services and IT Consulting"
        assert raw_data["company_size"] == "51-200 employees"
        assert raw_data["founded"] == "2015"
        assert len(raw_data["employees"]) == 2
        assert len(raw_data["locations"]) == 1
        assert len(raw_data["updates"]) == 1
        assert len(raw_data["similar_companies"]) == 1
        
        # Check employee data structure
        first_employee = raw_data["employees"][0]
        assert first_employee["employee_name"] == "Jan Čurn"
        assert first_employee["employee_position"] == "CEO of Apify, a leading platform for web scraping and data for AI."
        
        # Check location data structure
        first_location = raw_data["locations"][0]
        assert first_location["is_hq"] == True
        assert first_location["office_address_line_1"] == "Stepanska 704/61"

    @pytest.mark.unit
    def test_raw_company_data_minimal(self, company_actor):
        """Test raw company data structure with minimal data."""
        minimal_data = {
            "company_name": "Test Company",
            "universal_name_id": "test-company"
        }
        
        # Should handle minimal data gracefully
        assert isinstance(minimal_data, dict)
        assert minimal_data["company_name"] == "Test Company"
        assert minimal_data["universal_name_id"] == "test-company"
        assert minimal_data.get("industry") is None
        assert len(minimal_data.get("employees", [])) == 0
        assert len(minimal_data.get("locations", [])) == 0

    @pytest.mark.unit
    def test_company_data_structure_validation(self, company_actor):
        """Test that raw company data has correct structure."""
        for company_data in LINKEDIN_COMPANY_OUTPUT:
            # Check required fields exist
            assert "company_name" in company_data
            assert "universal_name_id" in company_data
            assert "employees" in company_data
            assert "locations" in company_data
            assert "updates" in company_data
            assert "similar_companies" in company_data
            
            # Check types
            assert isinstance(company_data["employees"], list)
            assert isinstance(company_data["locations"], list)
            assert isinstance(company_data["updates"], list)
            assert isinstance(company_data["similar_companies"], list)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_proxy_configuration(self, company_actor):
        """Test scraping with proxy configuration."""
        proxy_config = {
            "useApifyProxy": True,
            "groups": ["RESIDENTIAL"]
        }
        
        with patch.object(company_actor, 'run_async') as mock_run:
            mock_result = create_mock_run_result(
                status="SUCCEEDED",
                items=LINKEDIN_COMPANY_OUTPUT
            )
            mock_run.return_value = mock_result
            
            await company_actor.scrape_companies(
                company_urls=LINKEDIN_COMPANY_INPUT,
                proxy_configuration=proxy_config,
                max_budget_usd=10.0
            )
            
            # Proxy configuration should be handled in run options
            mock_run.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_timeout_configuration(self, company_actor):
        """Test scraping with custom timeout."""
        with patch.object(company_actor, 'run_async') as mock_run:
            mock_result = create_mock_run_result(
                status="SUCCEEDED",
                items=LINKEDIN_COMPANY_OUTPUT
            )
            mock_run.return_value = mock_result
            
            await company_actor.scrape_companies(
                company_urls=LINKEDIN_COMPANY_INPUT,
                timeout_secs=900,  # 15 minutes
                max_budget_usd=10.0
            )
            
            # Check that timeout was set correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[1]["options"].timeout_secs == 900

    @pytest.mark.unit
    def test_url_format_edge_cases(self, company_actor):
        """Test URL validation with edge cases."""
        from app.actors.linkedin.validators import is_valid_linkedin_company_url
        
        edge_cases = [
            ("https://www.linkedin.com/company/test-company/", True),  # trailing slash
            ("https://linkedin.com/company/test-company", True),  # no www
            ("http://www.linkedin.com/company/test-company", True),  # http
            ("https://LINKEDIN.COM/company/test-company", True),  # uppercase
            ("https://www.linkedin.com/company/test-company/about/", False),  # extra path
            ("https://www.linkedin.com/company/", False),  # no company name
            ("https://www.linkedin.com/company/123456", False),  # ID-based
        ]
        
        for url, expected in edge_cases:
            assert is_valid_linkedin_company_url(url) == expected, f"Failed for URL: {url}"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_handling_empty_result(self, company_actor):
        """Test error handling when no data is returned."""
        with patch.object(company_actor, 'run_async') as mock_run:
            # Mock result with no items
            mock_result = create_mock_run_result(
                status="SUCCEEDED",
                items=[]
            )
            mock_run.return_value = mock_result
            
            result = await company_actor.scrape_companies(
                company_urls=LINKEDIN_COMPANY_INPUT,
                max_budget_usd=5.0
            )
            
            # Should return metadata with empty items list
            assert "companies" not in result
            assert "metadata" in result
            assert result["metadata"].items == []

    @pytest.mark.unit
    @pytest.mark.asyncio 
    async def test_budget_limit_handling(self, company_actor):
        """Test handling of budget limits."""
        with patch.object(company_actor, 'run_async') as mock_run:
            mock_result = create_mock_run_result(
                status="SUCCEEDED",
                items=LINKEDIN_COMPANY_OUTPUT
            )
            mock_run.return_value = mock_result
            
            budget_limit = 25.5
            await company_actor.scrape_companies(
                company_urls=LINKEDIN_COMPANY_INPUT,
                max_budget_usd=budget_limit
            )
            
            # Verify budget was passed correctly
            call_args = mock_run.call_args
            assert call_args[1]["max_budget"] == budget_limit 