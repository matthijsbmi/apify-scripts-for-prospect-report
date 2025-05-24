"""
Data quality scoring and analysis system.

This module provides advanced quality scoring including consistency analysis,
completeness assessment, and data enhancement recommendations.
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import Counter

import structlog

from app.validation.validator import DataValidator, ValidationResult


logger = structlog.get_logger(__name__)


class QualityReport:
    """Container for comprehensive quality analysis results."""
    
    def __init__(
        self,
        overall_score: float,
        completeness_score: float,
        consistency_score: float,
        freshness_score: float,
        validity_score: float,
        data_richness: Dict[str, Any],
        issues: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]],
    ):
        self.overall_score = overall_score
        self.completeness_score = completeness_score
        self.consistency_score = consistency_score
        self.freshness_score = freshness_score
        self.validity_score = validity_score
        self.data_richness = data_richness
        self.issues = issues
        self.recommendations = recommendations
        self.anomalies = anomalies
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert quality report to dictionary."""
        return {
            "overall_score": self.overall_score,
            "overall_grade": self._score_to_grade(self.overall_score),
            "component_scores": {
                "completeness": self.completeness_score,
                "consistency": self.consistency_score,
                "freshness": self.freshness_score,
                "validity": self.validity_score,
            },
            "data_richness": self.data_richness,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "anomalies": self.anomalies,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"


class DataQualityScorer:
    """
    Advanced data quality scoring system.
    
    Provides comprehensive analysis of data quality including completeness,
    consistency, freshness, and anomaly detection.
    """
    
    def __init__(self):
        """Initialize the quality scorer."""
        self.validator = DataValidator()
    
    def analyze_data_quality(
        self,
        data: Any,
        data_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityReport:
        """
        Perform comprehensive data quality analysis.
        
        Args:
            data: Data to analyze.
            data_type: Type of data being analyzed.
            context: Additional context for analysis.
            
        Returns:
            QualityReport with detailed analysis.
        """
        log = logger.bind(data_type=data_type)
        log.info("Performing data quality analysis")
        
        # Basic validation
        validation_result = self.validator.validate_data(data, data_type)
        
        # Component scoring
        completeness_score = self._assess_completeness(data, data_type, validation_result)
        consistency_score = self._assess_consistency(data, data_type, context)
        freshness_score = self._assess_freshness(data, data_type)
        validity_score = validation_result.confidence_score
        
        # Data richness analysis
        data_richness = self._analyze_data_richness(data, data_type)
        
        # Issue and anomaly detection
        issues = self._detect_issues(data, data_type, validation_result)
        anomalies = self._detect_anomalies(data, data_type)
        recommendations = self._generate_recommendations(
            data, data_type, validation_result, issues, anomalies
        )
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            completeness_score, consistency_score, freshness_score, validity_score
        )
        
        return QualityReport(
            overall_score=overall_score,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            freshness_score=freshness_score,
            validity_score=validity_score,
            data_richness=data_richness,
            issues=issues,
            recommendations=recommendations,
            anomalies=anomalies,
        )
    
    def _assess_completeness(
        self,
        data: Any,
        data_type: str,
        validation_result: ValidationResult
    ) -> float:
        """Assess data completeness."""
        required_fields = validation_result.required_fields
        optional_fields = validation_result.optional_fields
        
        # Base score from field validation
        required_score = required_fields["valid"] / required_fields["total"] if required_fields["total"] > 0 else 0
        optional_score = optional_fields["valid"] / optional_fields["total"] if optional_fields["total"] > 0 else 0
        
        # Weight required fields more heavily
        base_score = (required_score * 0.8) + (optional_score * 0.2)
        
        # Adjust based on data type specific completeness
        if data_type == "linkedin_profile":
            base_score = self._adjust_linkedin_profile_completeness(data, base_score)
        elif data_type == "company_data":
            base_score = self._adjust_company_data_completeness(data, base_score)
        elif data_type in ["facebook_data", "twitter_data"]:
            base_score = self._adjust_social_media_completeness(data, base_score)
        
        return min(base_score, 1.0)
    
    def _assess_consistency(
        self,
        data: Any,
        data_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Assess data consistency."""
        consistency_score = 1.0
        
        if data_type == "linkedin_profile":
            consistency_score = self._check_linkedin_profile_consistency(data)
        elif data_type == "company_data":
            consistency_score = self._check_company_data_consistency(data)
        elif data_type == "social_media_data":
            consistency_score = self._check_social_media_consistency(data)
        
        # Cross-reference consistency if context provided
        if context:
            cross_ref_score = self._check_cross_reference_consistency(data, data_type, context)
            consistency_score = (consistency_score + cross_ref_score) / 2
        
        return consistency_score
    
    def _assess_freshness(self, data: Any, data_type: str) -> float:
        """Assess data freshness/recency."""
        freshness_score = 0.5  # Default neutral score
        
        current_time = datetime.now()
        
        if data_type == "linkedin_posts":
            if hasattr(data, 'posts') and data.posts:
                freshness_score = self._calculate_posts_freshness(data.posts, current_time)
        elif data_type == "twitter_data":
            if hasattr(data, 'tweets') and data.tweets:
                freshness_score = self._calculate_posts_freshness(data.tweets, current_time)
        elif data_type == "facebook_data":
            if hasattr(data, 'posts') and data.posts:
                freshness_score = self._calculate_posts_freshness(data.posts, current_time)
        elif data_type == "company_data":
            # Check for recent news or updates
            if hasattr(data, 'news') and data.news:
                freshness_score = self._calculate_news_freshness(data.news, current_time)
        
        return freshness_score
    
    def _analyze_data_richness(self, data: Any, data_type: str) -> Dict[str, Any]:
        """Analyze data richness and depth."""
        richness = {
            "field_count": 0,
            "non_empty_fields": 0,
            "rich_fields": 0,
            "list_fields": 0,
            "nested_objects": 0,
            "text_content_length": 0,
            "unique_identifiers": 0,
        }
        
        if hasattr(data, '__dict__'):
            data_dict = data.__dict__
        elif isinstance(data, dict):
            data_dict = data
        else:
            return richness
        
        richness["field_count"] = len(data_dict)
        
        for field_name, field_value in data_dict.items():
            if field_value is not None:
                richness["non_empty_fields"] += 1
                
                if isinstance(field_value, list):
                    richness["list_fields"] += 1
                    if len(field_value) >= 3:  # Rich list
                        richness["rich_fields"] += 1
                elif isinstance(field_value, dict):
                    richness["nested_objects"] += 1
                    if len(field_value) >= 3:  # Rich object
                        richness["rich_fields"] += 1
                elif isinstance(field_value, str):
                    richness["text_content_length"] += len(field_value)
                    if len(field_value) >= 50:  # Rich text content
                        richness["rich_fields"] += 1
                    
                    # Check for unique identifiers (URLs, IDs, etc.)
                    if any(keyword in field_name.lower() for keyword in ['url', 'id', 'link']):
                        richness["unique_identifiers"] += 1
        
        # Calculate richness ratio
        richness["completeness_ratio"] = richness["non_empty_fields"] / richness["field_count"] if richness["field_count"] > 0 else 0
        richness["richness_ratio"] = richness["rich_fields"] / richness["field_count"] if richness["field_count"] > 0 else 0
        
        return richness
    
    def _detect_issues(
        self,
        data: Any,
        data_type: str,
        validation_result: ValidationResult
    ) -> List[Dict[str, Any]]:
        """Detect data quality issues."""
        issues = []
        
        # Add validation issues
        for issue in validation_result.issues:
            issues.append({
                "type": "validation",
                "severity": "high",
                "description": issue,
                "field": None,
            })
        
        # Data type specific issue detection
        if data_type == "linkedin_profile":
            issues.extend(self._detect_linkedin_profile_issues(data))
        elif data_type == "company_data":
            issues.extend(self._detect_company_data_issues(data))
        elif data_type in ["facebook_data", "twitter_data", "social_media_data"]:
            issues.extend(self._detect_social_media_issues(data))
        
        return issues
    
    def _detect_anomalies(self, data: Any, data_type: str) -> List[Dict[str, Any]]:
        """Detect data anomalies and suspicious patterns."""
        anomalies = []
        
        if data_type == "linkedin_profile":
            anomalies.extend(self._detect_linkedin_profile_anomalies(data))
        elif data_type == "company_data":
            anomalies.extend(self._detect_company_data_anomalies(data))
        elif data_type in ["facebook_data", "twitter_data"]:
            anomalies.extend(self._detect_social_media_anomalies(data))
        
        return anomalies
    
    def _generate_recommendations(
        self,
        data: Any,
        data_type: str,
        validation_result: ValidationResult,
        issues: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations for data improvement."""
        recommendations = []
        
        # Add validation recommendations
        for rec in validation_result.recommendations:
            recommendations.append({
                "type": "validation",
                "priority": "high",
                "description": rec,
                "action": "data_collection",
            })
        
        # Issue-based recommendations
        for issue in issues:
            if issue["severity"] == "high":
                recommendations.append({
                    "type": "issue_resolution",
                    "priority": "high",
                    "description": f"Resolve {issue['type']} issue: {issue['description']}",
                    "action": "data_cleaning",
                })
        
        # Anomaly-based recommendations
        for anomaly in anomalies:
            recommendations.append({
                "type": "anomaly_review",
                "priority": "medium",
                "description": f"Review {anomaly['type']} anomaly: {anomaly['description']}",
                "action": "manual_review",
            })
        
        # Data enrichment recommendations
        enrichment_recs = self._generate_enrichment_recommendations(data, data_type)
        recommendations.extend(enrichment_recs)
        
        return recommendations
    
    def _calculate_overall_score(
        self,
        completeness: float,
        consistency: float,
        freshness: float,
        validity: float
    ) -> float:
        """Calculate overall quality score from component scores."""
        # Weighted average of component scores
        weights = {
            "validity": 0.3,      # Most important - data must be valid
            "completeness": 0.3,  # Second most important
            "consistency": 0.25,  # Important for reliability
            "freshness": 0.15,    # Less important but still valuable
        }
        
        overall_score = (
            validity * weights["validity"] +
            completeness * weights["completeness"] +
            consistency * weights["consistency"] +
            freshness * weights["freshness"]
        )
        
        return min(overall_score, 1.0)
    
    # Data type specific completeness adjustments
    def _adjust_linkedin_profile_completeness(self, data: Any, base_score: float) -> float:
        """Adjust completeness score for LinkedIn profiles."""
        bonus = 0.0
        
        # Bonus for rich experience data
        if hasattr(data, 'experience') and data.experience:
            if len(data.experience) >= 3:
                bonus += 0.05
            # Check for detailed experience entries
            detailed_count = sum(1 for exp in data.experience 
                               if isinstance(exp, dict) and len(exp.get('description', '')) > 50)
            if detailed_count >= 2:
                bonus += 0.05
        
        # Bonus for education diversity
        if hasattr(data, 'education') and data.education:
            if len(data.education) >= 2:
                bonus += 0.03
        
        # Bonus for skill diversity
        if hasattr(data, 'skills') and data.skills:
            if len(data.skills) >= 10:
                bonus += 0.05
        
        return min(base_score + bonus, 1.0)
    
    def _adjust_company_data_completeness(self, data: Any, base_score: float) -> float:
        """Adjust completeness score for company data."""
        bonus = 0.0
        
        # Bonus for multiple data sources
        if hasattr(data, 'sources') and data.sources:
            if len(data.sources) >= 3:
                bonus += 0.1
            elif len(data.sources) >= 2:
                bonus += 0.05
        
        # Bonus for financial data
        if hasattr(data, 'financial') and data.financial:
            bonus += 0.05
        
        # Bonus for employee data
        if hasattr(data, 'employees') and data.employees:
            bonus += 0.03
        
        return min(base_score + bonus, 1.0)
    
    def _adjust_social_media_completeness(self, data: Any, base_score: float) -> float:
        """Adjust completeness score for social media data."""
        bonus = 0.0
        
        # Bonus for post volume
        if hasattr(data, 'posts') and data.posts:
            if len(data.posts) >= 20:
                bonus += 0.05
            elif len(data.posts) >= 10:
                bonus += 0.03
        
        # Bonus for tweets volume
        if hasattr(data, 'tweets') and data.tweets:
            if len(data.tweets) >= 20:
                bonus += 0.05
            elif len(data.tweets) >= 10:
                bonus += 0.03
        
        return min(base_score + bonus, 1.0)
    
    # Consistency checking methods
    def _check_linkedin_profile_consistency(self, data: Any) -> float:
        """Check LinkedIn profile data consistency."""
        consistency_score = 1.0
        
        # Check name consistency in experience
        if hasattr(data, 'full_name') and hasattr(data, 'experience') and data.experience:
            # Look for name variations in experience descriptions
            name_parts = data.full_name.lower().split() if data.full_name else []
            if len(name_parts) >= 2:
                # This is a simplified check - could be more sophisticated
                pass  # Placeholder for name consistency logic
        
        # Check date consistency in experience
        if hasattr(data, 'experience') and data.experience:
            date_issues = self._check_experience_date_consistency(data.experience)
            if date_issues > 0:
                consistency_score -= 0.1 * date_issues
        
        return max(consistency_score, 0.0)
    
    def _check_company_data_consistency(self, data: Any) -> float:
        """Check company data consistency."""
        consistency_score = 1.0
        
        # Check employee count consistency
        if hasattr(data, 'employees') and data.employees:
            if hasattr(data.employees, 'employee_count'):
                # Check if employee count matches company size description
                pass  # Placeholder for employee count consistency logic
        
        # Check funding vs financial data consistency
        if hasattr(data, 'funding') and hasattr(data, 'financial'):
            # Check if funding and financial data are consistent
            pass  # Placeholder for funding consistency logic
        
        return consistency_score
    
    def _check_social_media_consistency(self, data: Any) -> float:
        """Check social media data consistency."""
        consistency_score = 1.0
        
        # Check handle/name consistency
        if hasattr(data, 'facebook') and hasattr(data, 'twitter'):
            # Check if handles/names are consistent across platforms
            pass  # Placeholder for cross-platform consistency logic
        
        return consistency_score
    
    def _check_cross_reference_consistency(
        self,
        data: Any,
        data_type: str,
        context: Dict[str, Any]
    ) -> float:
        """Check consistency across different data sources."""
        consistency_score = 1.0
        
        # This would implement cross-reference validation
        # For example, checking if LinkedIn company name matches company data name
        
        return consistency_score
    
    # Freshness calculation methods
    def _calculate_posts_freshness(self, posts: List[Dict[str, Any]], current_time: datetime) -> float:
        """Calculate freshness score based on post timestamps."""
        if not posts:
            return 0.0
        
        recent_posts = 0
        total_posts = len(posts)
        
        # Define freshness thresholds
        very_recent = current_time - timedelta(days=30)  # 1 month
        recent = current_time - timedelta(days=90)       # 3 months
        
        for post in posts:
            created_at = post.get("created_at") or post.get("published_at")
            if created_at:
                try:
                    if isinstance(created_at, str):
                        post_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        post_time = datetime.fromtimestamp(float(created_at))
                    
                    if post_time >= very_recent:
                        recent_posts += 2  # Double weight for very recent
                    elif post_time >= recent:
                        recent_posts += 1
                
                except:
                    pass  # Skip invalid dates
        
        # Calculate freshness score
        max_score = total_posts * 2  # If all posts were very recent
        freshness_score = recent_posts / max_score if max_score > 0 else 0.0
        
        return min(freshness_score, 1.0)
    
    def _calculate_news_freshness(self, news: List[Dict[str, Any]], current_time: datetime) -> float:
        """Calculate freshness score based on news timestamps."""
        if not news:
            return 0.5  # Neutral score for no news
        
        # Similar logic to posts but with different thresholds for news
        recent_news = 0
        total_news = len(news)
        
        very_recent = current_time - timedelta(days=90)   # 3 months
        recent = current_time - timedelta(days=365)       # 1 year
        
        for article in news:
            published_at = article.get("published_at") or article.get("date")
            if published_at:
                try:
                    if isinstance(published_at, str):
                        news_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    else:
                        news_time = datetime.fromtimestamp(float(published_at))
                    
                    if news_time >= very_recent:
                        recent_news += 2
                    elif news_time >= recent:
                        recent_news += 1
                
                except:
                    pass
        
        max_score = total_news * 2
        freshness_score = recent_news / max_score if max_score > 0 else 0.0
        
        return min(freshness_score, 1.0)
    
    # Issue detection methods
    def _detect_linkedin_profile_issues(self, data: Any) -> List[Dict[str, Any]]:
        """Detect LinkedIn profile specific issues."""
        issues = []
        
        # Check for placeholder text
        if hasattr(data, 'summary') and data.summary:
            if any(placeholder in data.summary.lower() for placeholder in 
                   ['lorem ipsum', 'placeholder', 'coming soon', 'update soon']):
                issues.append({
                    "type": "placeholder_content",
                    "severity": "medium",
                    "description": "Profile summary contains placeholder text",
                    "field": "summary",
                })
        
        # Check for missing profile photo
        if not hasattr(data, 'profile_image') or not data.profile_image:
            issues.append({
                "type": "missing_content",
                "severity": "low",
                "description": "No profile image available",
                "field": "profile_image",
            })
        
        return issues
    
    def _detect_company_data_issues(self, data: Any) -> List[Dict[str, Any]]:
        """Detect company data specific issues."""
        issues = []
        
        # Check for conflicting employee counts
        if hasattr(data, 'employees') and data.employees:
            if hasattr(data.employees, 'employee_count'):
                count = data.employees.employee_count
                if count and count < 0:
                    issues.append({
                        "type": "invalid_data",
                        "severity": "high",
                        "description": "Negative employee count",
                        "field": "employees.employee_count",
                    })
        
        return issues
    
    def _detect_social_media_issues(self, data: Any) -> List[Dict[str, Any]]:
        """Detect social media specific issues."""
        issues = []
        
        # Check for very low engagement
        if hasattr(data, 'posts') and data.posts:
            total_engagement = 0
            post_count = len(data.posts)
            
            for post in data.posts:
                if isinstance(post, dict):
                    likes = post.get('likes', 0) or 0
                    comments = post.get('comments', 0) or 0
                    shares = post.get('shares', 0) or 0
                    total_engagement += likes + comments + shares
            
            avg_engagement = total_engagement / post_count if post_count > 0 else 0
            
            if avg_engagement < 1:  # Very low engagement
                issues.append({
                    "type": "low_engagement",
                    "severity": "medium",
                    "description": "Very low social media engagement detected",
                    "field": "posts",
                })
        
        return issues
    
    # Anomaly detection methods
    def _detect_linkedin_profile_anomalies(self, data: Any) -> List[Dict[str, Any]]:
        """Detect anomalies in LinkedIn profile data."""
        anomalies = []
        
        # Check for unusually high connection count
        if hasattr(data, 'connections_count') and data.connections_count:
            if data.connections_count > 30000:  # LinkedIn's limit is 30k+
                anomalies.append({
                    "type": "unusual_metric",
                    "severity": "medium",
                    "description": f"Unusually high connection count: {data.connections_count}",
                    "field": "connections_count",
                })
        
        # Check for job hopping pattern
        if hasattr(data, 'experience') and data.experience:
            if len(data.experience) > 10:  # Many jobs
                short_tenures = sum(1 for exp in data.experience 
                                  if isinstance(exp, dict) and 
                                  self._is_short_tenure(exp))
                
                if short_tenures / len(data.experience) > 0.7:  # 70% short tenures
                    anomalies.append({
                        "type": "pattern_anomaly",
                        "severity": "low",
                        "description": "Frequent job changes detected",
                        "field": "experience",
                    })
        
        return anomalies
    
    def _detect_company_data_anomalies(self, data: Any) -> List[Dict[str, Any]]:
        """Detect anomalies in company data."""
        anomalies = []
        
        # Check for extremely high valuation vs employee count
        if (hasattr(data, 'financial') and data.financial and 
            hasattr(data, 'employees') and data.employees):
            
            if (hasattr(data.financial, 'valuation') and data.financial.valuation and
                hasattr(data.employees, 'employee_count') and data.employees.employee_count):
                
                try:
                    valuation = float(re.sub(r'[^\d.]', '', str(data.financial.valuation)))
                    employee_count = data.employees.employee_count
                    
                    if employee_count > 0:
                        valuation_per_employee = valuation / employee_count
                        
                        if valuation_per_employee > 10000000:  # $10M per employee
                            anomalies.append({
                                "type": "unusual_ratio",
                                "severity": "medium",
                                "description": f"Unusually high valuation per employee: ${valuation_per_employee:,.0f}",
                                "field": "financial.valuation",
                            })
                except:
                    pass  # Skip if conversion fails
        
        return anomalies
    
    def _detect_social_media_anomalies(self, data: Any) -> List[Dict[str, Any]]:
        """Detect anomalies in social media data."""
        anomalies = []
        
        # Check for bot-like posting patterns
        if hasattr(data, 'posts') and data.posts:
            # Analyze posting frequency
            post_times = []
            for post in data.posts:
                if isinstance(post, dict):
                    created_at = post.get("created_at") or post.get("published_at")
                    if created_at:
                        try:
                            if isinstance(created_at, str):
                                post_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                post_times.append(post_time)
                        except:
                            pass
            
            if len(post_times) >= 10:
                # Check for unusually regular posting intervals
                intervals = []
                for i in range(1, len(post_times)):
                    interval = abs((post_times[i] - post_times[i-1]).total_seconds())
                    intervals.append(interval)
                
                if intervals:
                    # Check if most intervals are very similar (bot-like)
                    avg_interval = sum(intervals) / len(intervals)
                    similar_intervals = sum(1 for interval in intervals 
                                          if abs(interval - avg_interval) < avg_interval * 0.1)
                    
                    if similar_intervals / len(intervals) > 0.8:  # 80% similar intervals
                        anomalies.append({
                            "type": "pattern_anomaly",
                            "severity": "medium",
                            "description": "Unusually regular posting pattern detected",
                            "field": "posts",
                        })
        
        return anomalies
    
    # Helper methods
    def _is_short_tenure(self, experience: Dict[str, Any]) -> bool:
        """Check if a job tenure is unusually short."""
        # This would implement logic to check if employment duration is short
        # Based on start/end dates in the experience entry
        # Simplified implementation
        return False  # Placeholder
    
    def _check_experience_date_consistency(self, experience: List[Dict[str, Any]]) -> int:
        """Check for date inconsistencies in experience."""
        # This would implement logic to check for overlapping dates,
        # future dates, or other date inconsistencies
        # Return number of issues found
        return 0  # Placeholder
    
    def _generate_enrichment_recommendations(
        self,
        data: Any,
        data_type: str
    ) -> List[Dict[str, Any]]:
        """Generate data enrichment recommendations."""
        recommendations = []
        
        if data_type == "linkedin_profile":
            if not hasattr(data, 'profile_image') or not data.profile_image:
                recommendations.append({
                    "type": "enrichment",
                    "priority": "low",
                    "description": "Add profile image for better visual identification",
                    "action": "data_collection",
                })
        
        elif data_type == "company_data":
            if not hasattr(data, 'website') or not data.website:
                recommendations.append({
                    "type": "enrichment",
                    "priority": "medium",
                    "description": "Add company website for verification and additional data",
                    "action": "data_collection",
                })
        
        return recommendations 