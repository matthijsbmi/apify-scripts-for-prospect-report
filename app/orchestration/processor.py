"""
Analysis result processor.

This module provides functionality for processing actor results into a
comprehensive analysis result for a prospect.
"""

import asyncio
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import structlog
from pydantic import BaseModel

from app.actors.config import ActorCategory, get_actor_configurations
from app.models.data import (
    Analysis, ActorExecution, AnalysisParameters, Prospect,
    ProspectAnalysisResponse, AnalysisSummary, LinkedInData, SocialMediaData,
    CompanyData, LinkedInProfile, LinkedInPost, LinkedInCompany,
    FacebookData, TwitterData, CostBreakdown, ExecutionMetadata,
    ConfidenceScores, KeyInsight
)
from app.services.storage import get_storage_service
from app.orchestration.orchestrator import ExecutionPlan


logger = structlog.get_logger(__name__)


class AnalysisProcessor:
    """
    Processor for analysis results.
    
    Generates comprehensive analysis results from actor execution results.
    """
    
    def __init__(self, storage_service = None):
        """
        Initialize the processor.
        
        Args:
            storage_service: Optional storage service. If None, use the singleton.
        """
        self.storage_service = storage_service or get_storage_service()
        self.actor_configurations = get_actor_configurations()
        
    async def process_analysis(
        self,
        analysis_id: str,
        plan: ExecutionPlan,
    ) -> ProspectAnalysisResponse:
        """
        Process analysis results into a comprehensive response.
        
        Args:
            analysis_id: ID of the analysis.
            plan: Execution plan with results.
            
        Returns:
            Processed analysis results.
            
        Raises:
            ValueError: If analysis is not found.
        """
        # Get the analysis
        analysis = self.storage_service.get_analysis(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis not found: {analysis_id}")
        
        # Get the prospect
        prospect = self.storage_service.get_prospect(analysis.prospect_id)
        if not prospect:
            raise ValueError(f"Prospect not found: {analysis.prospect_id}")
        
        # Get execution results
        executions = self.storage_service.filter_executions_by_analysis(analysis_id)
        
        # Process results by category
        linkedin_data = await self._process_linkedin_data(executions)
        social_media_data = await self._process_social_media_data(executions)
        company_data = await self._process_company_data(executions)
        
        # Calculate cost breakdown
        cost_breakdown = self._calculate_cost_breakdown(executions)
        
        # Calculate confidence scores
        confidence_scores = self._calculate_confidence_scores(
            linkedin_data, social_media_data, company_data)
        
        # Generate execution metadata
        execution_metadata = self._generate_execution_metadata(plan, executions)
        
        # Generate data sources list
        data_sources = self._generate_data_sources(executions)
        
        # Generate analysis summary
        analysis_summary = await self._generate_analysis_summary(
            prospect, linkedin_data, social_media_data, company_data)
        
        # Create response
        response = ProspectAnalysisResponse(
            prospect_id=prospect.id,
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            input_data=prospect,
            linkedin_data=linkedin_data,
            social_media_data=social_media_data,
            company_data=company_data,
            analysis_summary=analysis_summary,
            cost_breakdown=cost_breakdown,
            data_sources=data_sources,
            confidence_scores=confidence_scores,
            execution_metadata=execution_metadata,
        )
        
        # Save response
        self.storage_service.save_analysis_result(response)
        
        return response

    async def _process_linkedin_data(
        self, executions: List[ActorExecution]
    ) -> Optional[LinkedInData]:
        """
        Process LinkedIn data from executions.
        
        Args:
            executions: List of actor executions.
            
        Returns:
            Processed LinkedIn data or None if no data.
        """
        # Initialize result
        result = LinkedInData()
        has_data = False
        
        # Get LinkedIn actor executions
        linkedin_actors = {
            actor_id: config
            for actor_id, config in self.actor_configurations.get_actors_by_category(
                ActorCategory.LINKEDIN).items()
        }
        
        # Process each LinkedIn actor execution
        for execution in executions:
            if execution.actor_id in linkedin_actors:
                # Get raw actor data
                actor_execution = self.storage_service.get_execution(execution.run_id)
                if not actor_execution:
                    continue
                
                # Process based on actor type
                if execution.actor_id == "LpVuK3Zozwuipa5bp":  # LinkedIn Profile Bulk Scraper
                    # Usually the first item is the profile
                    if execution.output_summary.get("items_count", 0) > 0:
                        # In our example implementation we don't have actual data yet, 
                        # so we create placeholder data
                        result.profile = LinkedInProfile(
                            profile_url=actor_execution.input_summary.get(
                                "profileUrls", [""])[0],
                            full_name="Placeholder Name",
                            headline="Placeholder Headline",
                            extracted_at=datetime.now(),
                        )
                        has_data = True
                
                elif execution.actor_id == "A3cAPGpwBEG8RJwse":  # LinkedIn Posts Bulk Scraper
                    # In our example implementation we don't have actual post data yet,
                    # so we create placeholder posts
                    if execution.output_summary.get("items_count", 0) > 0:
                        post_count = min(execution.output_summary.get("items_count", 0), 5)
                        result.posts = []
                        for i in range(post_count):
                            result.posts.append(
                                LinkedInPost(
                                    post_url=f"https://www.linkedin.com/posts/example-{i}",
                                    content=f"Placeholder post content {i}",
                                    published_at=datetime.now(),
                                    extracted_at=datetime.now(),
                                )
                            )
                        has_data = True
                
                elif execution.actor_id == "3rgDeYgLhr6XrVnjs":  # LinkedIn Company Profile Scraper
                    # In our example implementation we don't have actual company data yet,
                    # so we create placeholder company data
                    if execution.output_summary.get("items_count", 0) > 0:
                        result.company = LinkedInCompany(
                            company_url=actor_execution.input_summary.get(
                                "companyUrls", [""])[0],
                            name="Placeholder Company",
                            industry="Placeholder Industry",
                            extracted_at=datetime.now(),
                        )
                        has_data = True
        
        return result if has_data else None

    async def _process_social_media_data(
        self, executions: List[ActorExecution]
    ) -> Optional[SocialMediaData]:
        """
        Process social media data from executions.
        
        Args:
            executions: List of actor executions.
            
        Returns:
            Processed social media data or None if no data.
        """
        # Initialize result
        result = SocialMediaData()
        has_data = False
        
        # Get social media actor executions
        social_actors = {
            actor_id: config
            for actor_id, config in self.actor_configurations.get_actors_by_category(
                ActorCategory.SOCIAL_MEDIA).items()
        }
        
        # Process each social media actor execution
        for execution in executions:
            if execution.actor_id in social_actors:
                # Get raw actor data
                actor_execution = self.storage_service.get_execution(execution.run_id)
                if not actor_execution:
                    continue
                
                # Process based on actor type
                if execution.actor_id == "KoJrdxJCTtpon81KY":  # Facebook Posts Scraper
                    # In our example implementation we don't have actual data yet,
                    # so we create placeholder data
                    if execution.output_summary.get("items_count", 0) > 0:
                        result.facebook = FacebookData(
                            page_url=actor_execution.input_summary.get(
                                "pageUrls", [""])[0],
                            name="Placeholder Facebook Page",
                            posts=[{"content": "Placeholder post content"}],
                            page_info={"followers": 1000, "likes": 900},
                            extracted_at=datetime.now(),
                        )
                        has_data = True
                
                elif execution.actor_id == "61RPP7dywgiy0JPD0":  # Twitter/X Scraper
                    # In our example implementation we don't have actual data yet,
                    # so we create placeholder data
                    if execution.output_summary.get("items_count", 0) > 0:
                        result.twitter = TwitterData(
                            handle=actor_execution.input_summary.get(
                                "usernames", [""])[0],
                            profile_info={"bio": "Placeholder bio"},
                            tweets=[{"content": "Placeholder tweet content"}],
                            followers_count=500,
                            following_count=200,
                            extracted_at=datetime.now(),
                        )
                        has_data = True
        
        return result if has_data else None

    async def _process_company_data(
        self, executions: List[ActorExecution]
    ) -> Optional[CompanyData]:
        """
        Process company data from executions.
        
        Args:
            executions: List of actor executions.
            
        Returns:
            Processed company data or None if no data.
        """
        # Initialize result
        result = CompanyData(
            name="Placeholder Company Name",
            financial={},
            funding={},
            industry={},
            technologies=[],
            competitors=[],
            news=[],
            sources=[],
        )
        has_data = False
        
        # Get company data actor executions
        company_actors = {
            actor_id: config
            for actor_id, config in self.actor_configurations.get_actors_by_category(
                ActorCategory.COMPANY_DATA).items()
        }
        
        # Process each company data actor execution
        for execution in executions:
            if execution.actor_id in company_actors:
                # Get raw actor data
                actor_execution = self.storage_service.get_execution(execution.run_id)
                if not actor_execution:
                    continue
                
                # Process based on actor type
                if execution.actor_id == "RIq8Fe9BdxSR4GUXY":  # Dun & Bradstreet Scraper
                    # In our example implementation we don't have actual data yet,
                    # so we create placeholder data
                    if execution.output_summary.get("items_count", 0) > 0:
                        result.financial = {
                            "revenue": "$10M-$50M",
                            "employees": "50-200",
                            "founded": "2010",
                        }
                        result.sources.append("Dun & Bradstreet")
                        has_data = True
                
                elif execution.actor_id == "BBfgvSNWcySEk1jQO":  # Crunchbase Scraper
                    # In our example implementation we don't have actual data yet,
                    # so we create placeholder data
                    if execution.output_summary.get("items_count", 0) > 0:
                        result.funding = {
                            "total_funding": "$5M",
                            "last_round": "Series A",
                            "last_round_date": "2022-01-15",
                        }
                        result.sources.append("Crunchbase")
                        has_data = True
                
                elif execution.actor_id == "C6OyLbP5ixnfc5lYe":  # ZoomInfo Scraper
                    # In our example implementation we don't have actual data yet,
                    # so we create placeholder data
                    if execution.output_summary.get("items_count", 0) > 0:
                        result.technologies = ["Java", "AWS", "React", "PostgreSQL"]
                        result.industry = {
                            "sector": "Technology",
                            "vertical": "SaaS",
                        }
                        result.sources.append("ZoomInfo")
                        has_data = True
                
                elif execution.actor_id == "5ms6D6gKCnJhZN61e":  # Erasmus+ Organisation
                    # In our example implementation we don't have actual data yet,
                    # so we create placeholder data
                    if execution.output_summary.get("items_count", 0) > 0:
                        result.funding["eu_funding"] = {
                            "total": "€2.5M",
                            "projects": 3,
                        }
                        result.sources.append("Erasmus+")
                        has_data = True
        
        return result if has_data else None

    def _calculate_cost_breakdown(
        self, executions: List[ActorExecution]
    ) -> CostBreakdown:
        """
        Calculate cost breakdown from executions.
        
        Args:
            executions: List of actor executions.
            
        Returns:
            Cost breakdown.
        """
        total_cost = Decimal('0')
        per_actor_cost = {}
        
        for execution in executions:
            cost = execution.cost or Decimal('0')
            total_cost += cost
            
            # Group by actor name
            actor_name = execution.actor_name
            if actor_name not in per_actor_cost:
                per_actor_cost[actor_name] = cost
            else:
                per_actor_cost[actor_name] += cost
        
        return CostBreakdown(
            total=total_cost,
            per_actor=per_actor_cost,
        )

    def _calculate_confidence_scores(
        self,
        linkedin_data: Optional[LinkedInData],
        social_media_data: Optional[SocialMediaData],
        company_data: Optional[CompanyData],
    ) -> ConfidenceScores:
        """
        Calculate confidence scores for the analysis.
        
        Args:
            linkedin_data: Processed LinkedIn data.
            social_media_data: Processed social media data.
            company_data: Processed company data.
            
        Returns:
            Confidence scores.
        """
        # Calculate scores based on data completeness
        linkedin_score = 0.0
        social_media_score = 0.0
        company_data_score = 0.0
        
        # LinkedIn score
        if linkedin_data:
            score_components = []
            if linkedin_data.profile:
                score_components.append(0.7)  # Profile data is valuable
            if linkedin_data.posts and len(linkedin_data.posts) > 0:
                score_components.append(0.5)  # Posts data is moderately valuable
            if linkedin_data.company:
                score_components.append(0.6)  # Company data is valuable
            
            linkedin_score = sum(score_components) / max(len(score_components), 1) if score_components else 0.0
        
        # Social media score
        if social_media_data:
            score_components = []
            if social_media_data.facebook:
                score_components.append(0.6)  # Facebook data is valuable
            if social_media_data.twitter:
                score_components.append(0.5)  # Twitter data is moderately valuable
            
            social_media_score = sum(score_components) / max(len(score_components), 1) if score_components else 0.0
        
        # Company data score
        if company_data:
            score_components = []
            if company_data.financial:
                score_components.append(0.8)  # Financial data is very valuable
            if company_data.funding:
                score_components.append(0.7)  # Funding data is valuable
            if company_data.industry:
                score_components.append(0.5)  # Industry data is moderately valuable
            if company_data.technologies:
                score_components.append(0.6)  # Technologies data is valuable
            
            company_data_score = sum(score_components) / max(len(score_components), 1) if score_components else 0.0
        
        # Calculate overall score
        data_points = [
            (linkedin_score, 0.4),  # LinkedIn data is weighted more
            (social_media_score, 0.3),  # Social media data is weighted normally
            (company_data_score, 0.3),  # Company data is weighted normally
        ]
        
        overall_score = sum(
            score * weight for score, weight in data_points if score > 0
        ) / sum(weight for _, weight in data_points if _ > 0) if any(score > 0 for score, _ in data_points) else 0.0
        
        return ConfidenceScores(
            linkedin=linkedin_score if linkedin_score > 0 else None,
            social_media=social_media_score if social_media_score > 0 else None,
            company_data=company_data_score if company_data_score > 0 else None,
            overall=overall_score,
        )

    def _generate_execution_metadata(
        self,
        plan: ExecutionPlan,
        executions: List[ActorExecution],
    ) -> ExecutionMetadata:
        """
        Generate execution metadata.
        
        Args:
            plan: Execution plan.
            executions: List of actor executions.
            
        Returns:
            Execution metadata.
        """
        # Calculate duration
        start_time = plan.start_time or datetime.now()
        end_time = plan.end_time or datetime.now()
        duration_secs = (end_time - start_time).total_seconds()
        
        # Get actor IDs
        actors_used = [execution.actor_id for execution in executions]
        
        # Calculate success rate
        total_nodes = len(plan.nodes)
        successful_nodes = sum(
            1 for node in plan.nodes.values()
            if node.status.value == "completed"
        )
        success_rate = (successful_nodes / total_nodes * 100) if total_nodes > 0 else 0
        
        return ExecutionMetadata(
            duration_secs=duration_secs,
            actors_used=actors_used,
            success_rate=success_rate,
            started_at=start_time,
            completed_at=end_time,
            trace_id=str(plan.plan_id),
        )

    def _generate_data_sources(self, executions: List[ActorExecution]) -> List[str]:
        """
        Generate list of data sources.
        
        Args:
            executions: List of actor executions.
            
        Returns:
            List of data sources.
        """
        sources = []
        
        # Map actor IDs to source names
        actor_to_source = {
            "LpVuK3Zozwuipa5bp": "LinkedIn Profiles",
            "A3cAPGpwBEG8RJwse": "LinkedIn Posts",
            "3rgDeYgLhr6XrVnjs": "LinkedIn Company",
            "KoJrdxJCTtpon81KY": "Facebook",
            "61RPP7dywgiy0JPD0": "Twitter/X",
            "RIq8Fe9BdxSR4GUXY": "Dun & Bradstreet",
            "BBfgvSNWcySEk1jQO": "Crunchbase",
            "C6OyLbP5ixnfc5lYe": "ZoomInfo",
            "5ms6D6gKCnJhZN61e": "Erasmus+",
        }
        
        # Add sources for successful executions
        for execution in executions:
            if execution.actor_id in actor_to_source:
                source_name = actor_to_source[execution.actor_id]
                if source_name not in sources:
                    sources.append(source_name)
        
        return sources

    async def _generate_analysis_summary(
        self,
        prospect: Prospect,
        linkedin_data: Optional[LinkedInData],
        social_media_data: Optional[SocialMediaData],
        company_data: Optional[CompanyData],
    ) -> Optional[AnalysisSummary]:
        """
        Generate analysis summary from collected data.
        
        Args:
            prospect: Prospect information.
            linkedin_data: Processed LinkedIn data.
            social_media_data: Processed social media data.
            company_data: Processed company data.
            
        Returns:
            Analysis summary or None if insufficient data.
        """
        # In a real implementation this would use AI to generate insights
        # Here we'll just create placeholder insights
        
        insights = []
        
        # Some placeholder insights based on data availability
        if linkedin_data and linkedin_data.profile:
            insights.append(
                KeyInsight(
                    category="Professional Background",
                    title="LinkedIn Profile Available",
                    description="Prospect has a complete LinkedIn profile with professional experience information.",
                    source="LinkedIn",
                    confidence=0.9,
                )
            )
        
        if linkedin_data and linkedin_data.posts and len(linkedin_data.posts) > 0:
            insights.append(
                KeyInsight(
                    category="Content & Engagement",
                    title="Active on LinkedIn",
                    description="Prospect is actively posting on LinkedIn, suggesting they are engaged with their professional network.",
                    source="LinkedIn Posts",
                    confidence=0.8,
                )
            )
        
        if social_media_data and social_media_data.twitter:
            insights.append(
                KeyInsight(
                    category="Social Presence",
                    title="Active Twitter/X User",
                    description="Prospect maintains an active Twitter/X presence, which could provide additional communication channels.",
                    source="Twitter/X",
                    confidence=0.7,
                )
            )
        
        if company_data and company_data.funding and "total_funding" in company_data.funding:
            insights.append(
                KeyInsight(
                    category="Company Status",
                    title="Recently Funded",
                    description="Prospect's company has secured recent funding, suggesting they may be in a growth phase.",
                    source="Crunchbase",
                    confidence=0.85,
                )
            )
        
        if company_data and company_data.technologies and len(company_data.technologies) > 0:
            insights.append(
                KeyInsight(
                    category="Technical Stack",
                    title="Technology Insights",
                    description=f"Company uses several key technologies including {', '.join(company_data.technologies[:3])}.",
                    source="ZoomInfo",
                    confidence=0.75,
                )
            )
        
        if not insights:
            return None
        
        return AnalysisSummary(
            key_insights=insights,
            risk_factors=[],  # Would be populated in a real implementation
            opportunities=[],  # Would be populated in a real implementation
            summary_text=f"Prospect analysis for {prospect.name} at {prospect.company}. "
                         f"{len(insights)} key insights were discovered across "
                         f"multiple data sources."
        ) 