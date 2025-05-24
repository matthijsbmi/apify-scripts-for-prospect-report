"""
CompanyDataService for unified company data collection.

This service coordinates data collection from multiple
company data sources (Dun & Bradstreet, ZoomInfo, Erasmus+) in a coordinated manner.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog

from app.actors.company.duns_actor import DunsActor
from app.actors.company.zoominfo_actor import ZoomInfoActor
from app.actors.company.erasmus_actor import ErasmusActor
from app.actors.company.validators import validate_company_identifiers
from app.models.data import CompanyData


logger = structlog.get_logger(__name__)


class CompanyDataService:
    """
    Service for collecting comprehensive company data.
    
    Coordinates data collection from multiple company data sources.
    """
    
    def __init__(self):
        """Initialize the company data service."""
        self.duns_actor = DunsActor()
        self.zoominfo_actor = ZoomInfoActor()
        self.erasmus_actor = ErasmusActor()
    
    async def collect_company_data(
        self,
        company_names: Optional[List[str]] = None,
        duns_numbers: Optional[List[str]] = None,
        website_urls: Optional[List[str]] = None,
        email_domains: Optional[List[str]] = None,
        erasmus_org_ids: Optional[List[str]] = None,
        proxy_configuration: Optional[Dict[str, Any]] = None,
        max_budget_usd: Optional[float] = None,
        include_financial_details: bool = True,
        include_tech_stack: bool = True,
        include_contacts: bool = True,
        max_contacts_per_company: int = 10,
    ) -> Dict[str, List[CompanyData]]:
        """
        Collect comprehensive company data from multiple sources.
        
        Args:
            company_names: List of company names to search.
            duns_numbers: List of DUNS numbers.
            website_urls: List of company website URLs.
            email_domains: List of email addresses for domain extraction.
            erasmus_org_ids: List of Erasmus+ organization IDs.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget in USD for all sources.
            include_financial_details: Whether to include financial information.
            include_tech_stack: Whether to include technology stack information.
            include_contacts: Whether to include contact information.
            max_contacts_per_company: Maximum contacts per company.
            
        Returns:
            Dictionary with data from each source.
            
        Raises:
            ValueError: If no valid company identifiers are provided.
        """
        # Validate inputs
        validation_result = validate_company_identifiers(
            company_names=company_names,
            duns_numbers=duns_numbers,
            website_urls=website_urls,
            email_domains=email_domains,
        )
        
        if not any(validation_result["valid"].values()):
            raise ValueError("No valid company identifiers provided")
        
        log = logger.bind(
            valid_names=len(validation_result["valid"]["company_names"]),
            valid_duns=len(validation_result["valid"]["duns_numbers"]),
            valid_websites=len(validation_result["valid"]["website_urls"]),
            valid_domains=len(validation_result["valid"]["domains"]),
        )
        log.info("Collecting comprehensive company data")
        
        # Calculate budget distribution
        budget_distribution = self._calculate_budget_distribution(
            max_budget_usd,
            has_duns=bool(validation_result["valid"]["duns_numbers"]) or bool(validation_result["valid"]["company_names"]),
            has_zoominfo=bool(validation_result["valid"]["domains"]) or bool(validation_result["valid"]["company_names"]),
            has_erasmus=bool(erasmus_org_ids) or bool(validation_result["valid"]["company_names"]),
        )
        
        # Prepare tasks for parallel execution
        tasks = []
        task_names = []
        
        # Dun & Bradstreet data collection
        if validation_result["valid"]["duns_numbers"] or validation_result["valid"]["company_names"]:
            tasks.append(
                self._collect_duns_data(
                    duns_numbers=validation_result["normalized"]["duns_numbers"],
                    company_names=validation_result["normalized"]["company_names"],
                    include_financials=include_financial_details,
                    proxy_configuration=proxy_configuration,
                    max_budget_usd=budget_distribution.get("duns"),
                )
            )
            task_names.append("duns")
        
        # ZoomInfo data collection
        if validation_result["valid"]["domains"] or validation_result["valid"]["company_names"]:
            # Prepare contact info for ZoomInfo
            contact_info = email_domains if email_domains else None
            company_info = (validation_result["normalized"]["website_urls"] + 
                          validation_result["normalized"]["company_names"])
            
            tasks.append(
                self._collect_zoominfo_data(
                    contact_info=contact_info,
                    company_info=company_info,
                    max_contacts_per_company=max_contacts_per_company if include_contacts else 0,
                    include_tech_stack=include_tech_stack,
                    proxy_configuration=proxy_configuration,
                    max_budget_usd=budget_distribution.get("zoominfo"),
                )
            )
            task_names.append("zoominfo")
        
        # Erasmus+ data collection
        if erasmus_org_ids or validation_result["valid"]["company_names"]:
            tasks.append(
                self._collect_erasmus_data(
                    organization_ids=erasmus_org_ids,
                    organization_names=validation_result["normalized"]["company_names"],
                    proxy_configuration=proxy_configuration,
                    max_budget_usd=budget_distribution.get("erasmus"),
                )
            )
            task_names.append("erasmus")
        
        if not tasks:
            raise ValueError("No data collection tasks could be prepared")
        
        # Execute tasks in parallel
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            company_data = {
                "duns": [],
                "zoominfo": [],
                "erasmus": [],
                "combined": [],
            }
            
            for i, result in enumerate(results):
                source = task_names[i]
                
                if isinstance(result, Exception):
                    log.error(
                        f"Error collecting {source} data",
                        error=str(result),
                    )
                elif isinstance(result, list):
                    company_data[source] = result
                    company_data["combined"].extend(result)
            
            # Deduplicate and merge combined data
            company_data["combined"] = self._merge_company_data(company_data["combined"])
            
            log.info(
                "Company data collection completed",
                duns_count=len(company_data["duns"]),
                zoominfo_count=len(company_data["zoominfo"]),
                erasmus_count=len(company_data["erasmus"]),
                combined_count=len(company_data["combined"]),
            )
            
            return company_data
        
        except Exception as e:
            log.error("Error in company data collection", error=str(e))
            raise
    
    async def _collect_duns_data(
        self,
        duns_numbers: List[str],
        company_names: List[str],
        include_financials: bool,
        proxy_configuration: Optional[Dict[str, Any]],
        max_budget_usd: Optional[float],
    ) -> List[CompanyData]:
        """
        Collect Dun & Bradstreet data.
        
        Args:
            duns_numbers: List of DUNS numbers.
            company_names: List of company names.
            include_financials: Whether to include financial details.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget for D&B data.
            
        Returns:
            List of company data or empty list if collection fails.
        """
        try:
            result = await self.duns_actor.scrape_companies(
                company_identifiers=duns_numbers if duns_numbers else None,
                company_names=company_names if company_names else None,
                include_financials=include_financials,
                include_risk_scores=True,
                proxy_configuration=proxy_configuration,
                max_budget_usd=max_budget_usd,
            )
            
            return result.get("data", [])
        
        except Exception as e:
            logger.error(
                "Failed to collect Dun & Bradstreet data",
                duns_numbers=duns_numbers,
                company_names=company_names,
                error=str(e),
            )
            return []
    
    async def _collect_zoominfo_data(
        self,
        contact_info: Optional[List[str]],
        company_info: List[str],
        max_contacts_per_company: int,
        include_tech_stack: bool,
        proxy_configuration: Optional[Dict[str, Any]],
        max_budget_usd: Optional[float],
    ) -> List[CompanyData]:
        """
        Collect ZoomInfo data.
        
        Args:
            contact_info: List of contact information.
            company_info: List of company information.
            max_contacts_per_company: Maximum contacts per company.
            include_tech_stack: Whether to include tech stack.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget for ZoomInfo data.
            
        Returns:
            List of company data or empty list if collection fails.
        """
        try:
            result = await self.zoominfo_actor.scrape_companies(
                contact_info=contact_info,
                company_info=company_info if company_info else None,
                max_contacts_per_company=max_contacts_per_company,
                include_tech_stack=include_tech_stack,
                proxy_configuration=proxy_configuration,
                max_budget_usd=max_budget_usd,
            )
            
            return result.get("data", [])
        
        except Exception as e:
            logger.error(
                "Failed to collect ZoomInfo data",
                contact_info=contact_info,
                company_info=company_info,
                error=str(e),
            )
            return []
    
    async def _collect_erasmus_data(
        self,
        organization_ids: Optional[List[str]],
        organization_names: List[str],
        proxy_configuration: Optional[Dict[str, Any]],
        max_budget_usd: Optional[float],
    ) -> List[CompanyData]:
        """
        Collect Erasmus+ data.
        
        Args:
            organization_ids: List of organization IDs.
            organization_names: List of organization names.
            proxy_configuration: Optional proxy configuration.
            max_budget_usd: Maximum budget for Erasmus+ data.
            
        Returns:
            List of company data or empty list if collection fails.
        """
        try:
            result = await self.erasmus_actor.scrape_organizations(
                organization_ids=organization_ids,
                organization_names=organization_names if organization_names else None,
                proxy_configuration=proxy_configuration,
                max_budget_usd=max_budget_usd,
            )
            
            return result.get("data", [])
        
        except Exception as e:
            logger.error(
                "Failed to collect Erasmus+ data",
                organization_ids=organization_ids,
                organization_names=organization_names,
                error=str(e),
            )
            return []
    
    def _calculate_budget_distribution(
        self,
        max_budget_usd: Optional[float],
        has_duns: bool = True,
        has_zoominfo: bool = True,
        has_erasmus: bool = True,
    ) -> Dict[str, float]:
        """
        Calculate budget distribution across data sources.
        
        Args:
            max_budget_usd: Maximum budget in USD.
            has_duns: Whether D&B data is being collected.
            has_zoominfo: Whether ZoomInfo data is being collected.
            has_erasmus: Whether Erasmus+ data is being collected.
            
        Returns:
            Dictionary with budget allocation per source.
        """
        if not max_budget_usd:
            return {}
        
        # Count active sources
        sources = []
        if has_duns:
            sources.append("duns")
        if has_zoominfo:
            sources.append("zoominfo")
        if has_erasmus:
            sources.append("erasmus")
        
        if not sources:
            return {}
        
        # Budget distribution based on typical data source costs and value
        distribution = {}
        
        if len(sources) == 1:
            # Single source gets all budget
            distribution[sources[0]] = max_budget_usd
        else:
            # Multiple sources - weight by typical value/cost
            weights = {
                "duns": 0.30,        # High value for financial/risk data
                "zoominfo": 0.25,    # Good value for contacts/tech stack
                "erasmus": 0.10,     # Lower cost/specialized data
            }
            
            # Normalize weights for active sources
            total_weight = sum(weights[source] for source in sources)
            for source in sources:
                distribution[source] = max_budget_usd * (weights[source] / total_weight)
        
        return distribution
    
    def _merge_company_data(self, company_data_list: List[CompanyData]) -> List[CompanyData]:
        """
        Merge company data from different sources, deduplicating by company name.
        
        Args:
            company_data_list: List of company data from various sources.
            
        Returns:
            Deduplicated and merged company data.
        """
        if not company_data_list:
            return []
        
        # Group by company name (case-insensitive)
        companies_by_name = {}
        for company_data in company_data_list:
            key = company_data.name.lower().strip()
            if key not in companies_by_name:
                companies_by_name[key] = []
            companies_by_name[key].append(company_data)
        
        # Merge data for each company
        merged_companies = []
        for company_name, data_list in companies_by_name.items():
            if len(data_list) == 1:
                # Single source, use as-is
                merged_companies.append(data_list[0])
            else:
                # Multiple sources, merge data
                merged_data = self._merge_single_company_data(data_list)
                merged_companies.append(merged_data)
        
        return merged_companies
    
    def _merge_single_company_data(self, data_list: List[CompanyData]) -> CompanyData:
        """
        Merge data for a single company from multiple sources.
        
        Args:
            data_list: List of CompanyData for the same company.
            
        Returns:
            Merged CompanyData.
        """
        # Use the first entry as base
        merged = data_list[0]
        
        # Merge sources
        all_sources = set(merged.sources or [])
        for data in data_list[1:]:
            if data.sources:
                all_sources.update(data.sources)
        
        # Merge other fields (take non-None values, prefer later sources)
        for data in data_list[1:]:
            if data.website and not merged.website:
                merged.website = data.website
            if data.financial and not merged.financial:
                merged.financial = data.financial
            if data.industry:
                if merged.industry:
                    merged.industry.update(data.industry)
                else:
                    merged.industry = data.industry
            if data.employees and not merged.employees:
                merged.employees = data.employees
            if data.technologies:
                if merged.technologies:
                    merged.technologies.extend(data.technologies)
                else:
                    merged.technologies = data.technologies
            if data.competitors:
                if merged.competitors:
                    merged.competitors.extend(data.competitors)
                else:
                    merged.competitors = data.competitors
            if data.news:
                if merged.news:
                    merged.news.extend(data.news)
                else:
                    merged.news = data.news
        
        # Update sources
        merged.sources = list(all_sources)
        
        # Deduplicate lists
        if merged.technologies:
            merged.technologies = list(set(merged.technologies))
        if merged.competitors:
            merged.competitors = list(set(merged.competitors))
        
        return merged 