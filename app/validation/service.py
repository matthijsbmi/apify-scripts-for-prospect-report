"""
Validation service for comprehensive data quality assessment.

This module provides a unified interface for validating and scoring
data quality across all supported data types.
"""

from typing import Any, Dict, List, Optional, Union

import structlog

from app.validation.validator import DataValidator, ValidationResult
from app.validation.quality_scorer import DataQualityScorer, QualityReport
from app.models.data import (
    LinkedInProfileData, LinkedInPostsData, LinkedInCompanyData,
    FacebookData, TwitterData, SocialMediaData, CompanyData
)


logger = structlog.get_logger(__name__)


class ValidationService:
    """
    Unified validation service for all data types.
    
    Provides comprehensive validation, quality scoring, and reporting
    for LinkedIn, social media, and company data.
    """
    
    def __init__(self):
        """Initialize the validation service."""
        self.validator = DataValidator()
        self.quality_scorer = DataQualityScorer()
    
    def validate_and_score(
        self,
        data: Any,
        data_type: str,
        strict_mode: bool = False,
        include_quality_analysis: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive validation and quality scoring.
        
        Args:
            data: Data to validate and score.
            data_type: Type of data being processed.
            strict_mode: Whether to use strict validation rules.
            include_quality_analysis: Whether to include detailed quality analysis.
            context: Additional context for cross-reference validation.
            
        Returns:
            Dictionary containing validation results and quality scores.
        """
        log = logger.bind(
            data_type=data_type,
            strict_mode=strict_mode,
            include_quality=include_quality_analysis
        )
        log.info("Starting validation and quality scoring")
        
        result = {
            "data_type": data_type,
            "validation": None,
            "quality_report": None,
            "summary": None,
        }
        
        try:
            # Basic validation
            validation_result = self.validator.validate_data(data, data_type, strict_mode)
            result["validation"] = validation_result.to_dict()
            
            # Quality analysis if requested
            if include_quality_analysis:
                quality_report = self.quality_scorer.analyze_data_quality(data, data_type, context)
                result["quality_report"] = quality_report.to_dict()
            
            # Generate summary
            result["summary"] = self._generate_summary(validation_result, quality_report if include_quality_analysis else None)
            
            log.info(
                "Validation and scoring completed",
                is_valid=validation_result.is_valid,
                confidence_score=validation_result.confidence_score,
                overall_score=quality_report.overall_score if include_quality_analysis else None,
            )
            
            return result
        
        except Exception as e:
            log.error("Validation and scoring failed", error=str(e))
            result["validation"] = {
                "is_valid": False,
                "confidence_score": 0.0,
                "issues": [f"Validation service error: {str(e)}"],
                "recommendations": ["Contact support for assistance"],
            }
            result["summary"] = {
                "status": "error",
                "message": f"Validation failed: {str(e)}",
            }
            return result
    
    def validate_multiple(
        self,
        data_items: List[Dict[str, Any]],
        strict_mode: bool = False,
        include_quality_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Validate multiple data items of potentially different types.
        
        Args:
            data_items: List of dictionaries with 'data', 'data_type', and optional 'id' keys.
            strict_mode: Whether to use strict validation rules.
            include_quality_analysis: Whether to include detailed quality analysis.
            
        Returns:
            Dictionary containing results for all items and aggregate statistics.
        """
        log = logger.bind(item_count=len(data_items))
        log.info("Starting batch validation")
        
        results = {
            "items": [],
            "statistics": {
                "total_items": len(data_items),
                "valid_items": 0,
                "invalid_items": 0,
                "average_confidence": 0.0,
                "average_quality_score": 0.0,
                "data_type_distribution": {},
                "common_issues": [],
            },
        }
        
        total_confidence = 0.0
        total_quality = 0.0
        all_issues = []
        
        for i, item in enumerate(data_items):
            item_id = item.get("id", f"item_{i}")
            data = item.get("data")
            data_type = item.get("data_type")
            context = item.get("context")
            
            if not data or not data_type:
                results["items"].append({
                    "id": item_id,
                    "error": "Missing data or data_type",
                })
                results["statistics"]["invalid_items"] += 1
                continue
            
            try:
                # Validate and score individual item
                item_result = self.validate_and_score(
                    data=data,
                    data_type=data_type,
                    strict_mode=strict_mode,
                    include_quality_analysis=include_quality_analysis,
                    context=context,
                )
                
                item_result["id"] = item_id
                results["items"].append(item_result)
                
                # Update statistics
                validation = item_result.get("validation", {})
                if validation.get("is_valid", False):
                    results["statistics"]["valid_items"] += 1
                else:
                    results["statistics"]["invalid_items"] += 1
                
                total_confidence += validation.get("confidence_score", 0.0)
                
                if include_quality_analysis:
                    quality_report = item_result.get("quality_report", {})
                    total_quality += quality_report.get("overall_score", 0.0)
                
                # Track data type distribution
                data_type_stats = results["statistics"]["data_type_distribution"]
                data_type_stats[data_type] = data_type_stats.get(data_type, 0) + 1
                
                # Collect issues
                all_issues.extend(validation.get("issues", []))
                
            except Exception as e:
                log.error(f"Failed to process item {item_id}", error=str(e))
                results["items"].append({
                    "id": item_id,
                    "error": str(e),
                })
                results["statistics"]["invalid_items"] += 1
        
        # Calculate averages
        valid_count = max(len(data_items), 1)  # Avoid division by zero
        results["statistics"]["average_confidence"] = total_confidence / valid_count
        
        if include_quality_analysis:
            results["statistics"]["average_quality_score"] = total_quality / valid_count
        
        # Identify common issues
        results["statistics"]["common_issues"] = self._identify_common_issues(all_issues)
        
        log.info(
            "Batch validation completed",
            valid_items=results["statistics"]["valid_items"],
            invalid_items=results["statistics"]["invalid_items"],
        )
        
        return results
    
    def compare_data_quality(
        self,
        data_items: List[Dict[str, Any]],
        comparison_criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare data quality across multiple items.
        
        Args:
            data_items: List of data items to compare.
            comparison_criteria: Specific criteria to focus on for comparison.
            
        Returns:
            Dictionary containing comparison results and rankings.
        """
        if not comparison_criteria:
            comparison_criteria = ["overall_score", "completeness_score", "validity_score"]
        
        log = logger.bind(
            item_count=len(data_items),
            criteria=comparison_criteria
        )
        log.info("Starting data quality comparison")
        
        # Validate and score all items
        scored_items = []
        for i, item in enumerate(data_items):
            item_id = item.get("id", f"item_{i}")
            result = self.validate_and_score(
                data=item.get("data"),
                data_type=item.get("data_type"),
                include_quality_analysis=True,
                context=item.get("context"),
            )
            
            if result.get("quality_report"):
                scored_items.append({
                    "id": item_id,
                    "scores": result["quality_report"]["component_scores"],
                    "overall_score": result["quality_report"]["overall_score"],
                    "grade": result["quality_report"]["overall_grade"],
                })
        
        # Generate rankings
        rankings = {}
        for criterion in comparison_criteria:
            if criterion == "overall_score":
                sorted_items = sorted(scored_items, key=lambda x: x["overall_score"], reverse=True)
            else:
                sorted_items = sorted(
                    scored_items,
                    key=lambda x: x["scores"].get(criterion, 0.0),
                    reverse=True
                )
            
            rankings[criterion] = [
                {
                    "rank": idx + 1,
                    "id": item["id"],
                    "score": item["scores"].get(criterion, item.get("overall_score", 0.0)),
                    "grade": item["grade"],
                }
                for idx, item in enumerate(sorted_items)
            ]
        
        # Calculate statistics
        if scored_items:
            best_overall = max(scored_items, key=lambda x: x["overall_score"])
            worst_overall = min(scored_items, key=lambda x: x["overall_score"])
            avg_score = sum(item["overall_score"] for item in scored_items) / len(scored_items)
        else:
            best_overall = worst_overall = None
            avg_score = 0.0
        
        comparison_result = {
            "rankings": rankings,
            "statistics": {
                "total_items": len(scored_items),
                "average_score": avg_score,
                "best_item": {
                    "id": best_overall["id"] if best_overall else None,
                    "score": best_overall["overall_score"] if best_overall else 0.0,
                } if best_overall else None,
                "worst_item": {
                    "id": worst_overall["id"] if worst_overall else None,
                    "score": worst_overall["overall_score"] if worst_overall else 0.0,
                } if worst_overall else None,
            },
            "recommendations": self._generate_comparison_recommendations(scored_items),
        }
        
        log.info("Data quality comparison completed")
        return comparison_result
    
    def generate_quality_report(
        self,
        data_items: List[Dict[str, Any]],
        report_format: str = "detailed"
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive quality report.
        
        Args:
            data_items: List of data items to include in the report.
            report_format: Format of the report ('summary', 'detailed', 'executive').
            
        Returns:
            Dictionary containing the formatted quality report.
        """
        log = logger.bind(
            item_count=len(data_items),
            format=report_format
        )
        log.info("Generating quality report")
        
        # Process all items
        batch_results = self.validate_multiple(data_items, include_quality_analysis=True)
        
        if report_format == "executive":
            return self._generate_executive_report(batch_results)
        elif report_format == "summary":
            return self._generate_summary_report(batch_results)
        else:  # detailed
            return self._generate_detailed_report(batch_results)
    
    def _generate_summary(
        self,
        validation_result: ValidationResult,
        quality_report: Optional[QualityReport] = None
    ) -> Dict[str, Any]:
        """Generate a summary of validation and quality results."""
        summary = {
            "status": "valid" if validation_result.is_valid else "invalid",
            "confidence_level": validation_result._interpret_score(validation_result.confidence_score),
            "confidence_score": validation_result.confidence_score,
            "primary_issues": validation_result.issues[:3],  # Top 3 issues
            "key_recommendations": validation_result.recommendations[:3],  # Top 3 recommendations
        }
        
        if quality_report:
            summary.update({
                "overall_grade": quality_report._score_to_grade(quality_report.overall_score),
                "overall_score": quality_report.overall_score,
                "data_richness_level": self._assess_richness_level(quality_report.data_richness),
                "anomaly_count": len(quality_report.anomalies),
            })
        
        return summary
    
    def _identify_common_issues(self, all_issues: List[str]) -> List[Dict[str, Any]]:
        """Identify the most common issues across all validated items."""
        from collections import Counter
        
        issue_counts = Counter(all_issues)
        common_issues = []
        
        for issue, count in issue_counts.most_common(5):  # Top 5 common issues
            common_issues.append({
                "issue": issue,
                "frequency": count,
                "percentage": (count / len(all_issues)) * 100 if all_issues else 0,
            })
        
        return common_issues
    
    def _assess_richness_level(self, data_richness: Dict[str, Any]) -> str:
        """Assess the richness level of data."""
        richness_ratio = data_richness.get("richness_ratio", 0.0)
        
        if richness_ratio >= 0.8:
            return "very high"
        elif richness_ratio >= 0.6:
            return "high"
        elif richness_ratio >= 0.4:
            return "medium"
        elif richness_ratio >= 0.2:
            return "low"
        else:
            return "very low"
    
    def _generate_comparison_recommendations(
        self,
        scored_items: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on quality comparison."""
        recommendations = []
        
        if not scored_items:
            return ["No items to compare"]
        
        avg_score = sum(item["overall_score"] for item in scored_items) / len(scored_items)
        
        low_quality_items = [item for item in scored_items if item["overall_score"] < 0.6]
        
        if low_quality_items:
            recommendations.append(
                f"Focus on improving {len(low_quality_items)} low-quality items "
                f"({len(low_quality_items)/len(scored_items)*100:.1f}% of total)"
            )
        
        if avg_score < 0.7:
            recommendations.append("Overall data quality is below acceptable threshold - consider data enrichment")
        
        best_item = max(scored_items, key=lambda x: x["overall_score"])
        recommendations.append(f"Use item '{best_item['id']}' as a quality benchmark for other items")
        
        return recommendations
    
    def _generate_executive_report(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an executive summary report."""
        stats = batch_results["statistics"]
        
        return {
            "report_type": "executive_summary",
            "overview": {
                "total_data_items": stats["total_items"],
                "data_quality_score": f"{stats['average_quality_score']:.1%}",
                "data_validity_rate": f"{stats['valid_items']/stats['total_items']:.1%}" if stats['total_items'] > 0 else "0%",
                "confidence_level": stats["average_confidence"],
            },
            "key_findings": [
                f"Processed {stats['total_items']} data items across {len(stats['data_type_distribution'])} data types",
                f"{stats['valid_items']} items passed validation ({stats['valid_items']/stats['total_items']*100:.1f}%)" if stats['total_items'] > 0 else "No valid items",
                f"Average quality score: {stats['average_quality_score']:.1%}",
            ],
            "action_items": [
                f"Address {len(stats['common_issues'])} common data quality issues",
                "Implement data enrichment for low-scoring items",
                "Establish regular data quality monitoring",
            ],
            "data_distribution": stats["data_type_distribution"],
        }
    
    def _generate_summary_report(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary report."""
        stats = batch_results["statistics"]
        
        return {
            "report_type": "summary",
            "statistics": stats,
            "top_issues": stats["common_issues"][:3],
            "recommendations": [
                "Focus on resolving the most common issues first",
                "Implement validation at data collection points",
                "Consider automated data quality monitoring",
            ],
            "quality_distribution": {
                "high_quality": len([item for item in batch_results["items"] 
                                   if item.get("quality_report", {}).get("overall_score", 0) >= 0.8]),
                "medium_quality": len([item for item in batch_results["items"] 
                                     if 0.6 <= item.get("quality_report", {}).get("overall_score", 0) < 0.8]),
                "low_quality": len([item for item in batch_results["items"] 
                                  if item.get("quality_report", {}).get("overall_score", 0) < 0.6]),
            },
        }
    
    def _generate_detailed_report(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed report."""
        return {
            "report_type": "detailed",
            "full_results": batch_results,
            "analysis": {
                "data_type_analysis": self._analyze_by_data_type(batch_results),
                "quality_trends": self._analyze_quality_trends(batch_results),
                "issue_analysis": self._analyze_issues(batch_results),
            },
            "recommendations": {
                "immediate": self._get_immediate_recommendations(batch_results),
                "short_term": self._get_short_term_recommendations(batch_results),
                "long_term": self._get_long_term_recommendations(batch_results),
            },
        }
    
    def _analyze_by_data_type(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze results by data type."""
        type_analysis = {}
        
        for item in batch_results["items"]:
            if "error" in item:
                continue
                
            data_type = item["data_type"]
            if data_type not in type_analysis:
                type_analysis[data_type] = {
                    "count": 0,
                    "avg_quality": 0.0,
                    "avg_confidence": 0.0,
                    "common_issues": [],
                }
            
            type_analysis[data_type]["count"] += 1
            
            quality_score = item.get("quality_report", {}).get("overall_score", 0.0)
            confidence_score = item.get("validation", {}).get("confidence_score", 0.0)
            
            type_analysis[data_type]["avg_quality"] += quality_score
            type_analysis[data_type]["avg_confidence"] += confidence_score
        
        # Calculate averages
        for data_type, analysis in type_analysis.items():
            if analysis["count"] > 0:
                analysis["avg_quality"] /= analysis["count"]
                analysis["avg_confidence"] /= analysis["count"]
        
        return type_analysis
    
    def _analyze_quality_trends(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze quality trends across the dataset."""
        scores = []
        for item in batch_results["items"]:
            if "error" not in item and "quality_report" in item:
                scores.append(item["quality_report"]["overall_score"])
        
        if not scores:
            return {"message": "No quality scores available for analysis"}
        
        return {
            "distribution": {
                "excellent": len([s for s in scores if s >= 0.9]),
                "good": len([s for s in scores if 0.7 <= s < 0.9]),
                "fair": len([s for s in scores if 0.5 <= s < 0.7]),
                "poor": len([s for s in scores if s < 0.5]),
            },
            "statistics": {
                "mean": sum(scores) / len(scores),
                "median": sorted(scores)[len(scores) // 2],
                "min": min(scores),
                "max": max(scores),
            },
        }
    
    def _analyze_issues(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze common issues and patterns."""
        return {
            "most_common": batch_results["statistics"]["common_issues"],
            "severity_distribution": {
                "high": 0,  # Would need to implement severity tracking
                "medium": 0,
                "low": 0,
            },
            "recommendations": [
                "Implement data validation at collection points",
                "Create data quality monitoring dashboards",
                "Establish data quality SLAs",
            ],
        }
    
    def _get_immediate_recommendations(self, batch_results: Dict[str, Any]) -> List[str]:
        """Get immediate action recommendations."""
        return [
            "Fix critical validation failures",
            "Address high-severity data quality issues",
            "Implement basic data cleaning procedures",
        ]
    
    def _get_short_term_recommendations(self, batch_results: Dict[str, Any]) -> List[str]:
        """Get short-term recommendations."""
        return [
            "Implement automated data validation pipelines",
            "Create data quality monitoring dashboards",
            "Establish data quality metrics and KPIs",
        ]
    
    def _get_long_term_recommendations(self, batch_results: Dict[str, Any]) -> List[str]:
        """Get long-term recommendations."""
        return [
            "Implement machine learning-based anomaly detection",
            "Create comprehensive data governance framework",
            "Establish data quality SLAs and governance policies",
        ] 