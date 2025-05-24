"""
Apify actor configuration management.

This module provides a centralized system for managing actor configurations,
including costs, input/output schemas, and execution parameters.
"""

import json
import os
from decimal import Decimal
from enum import Enum, auto
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Type, Union

import yaml
from pydantic import BaseModel, Field, HttpUrl, validator
from app.core.config import settings

import structlog

logger = structlog.get_logger(__name__)


class ActorCategory(str, Enum):
    """Categories of Apify actors."""
    
    LINKEDIN = "linkedin"
    SOCIAL_MEDIA = "social_media"
    COMPANY_DATA = "company_data"
    UTILITY = "utility"


class CostModel(str, Enum):
    """Cost models for Apify actors."""
    
    FIXED = "fixed"  # Fixed cost per run
    PER_UNIT = "per_unit"  # Cost per unit (e.g., per 1000 profiles)
    BASE_PLUS_UNIT = "base_plus_unit"  # Fixed base cost plus per-unit cost
    MONTHLY_SUBSCRIPTION = "monthly_subscription"  # Monthly subscription cost


class ActorConfig(BaseModel):
    """Configuration for an Apify actor."""
    
    id: str = Field(..., description="Apify actor ID")
    name: str = Field(..., description="Actor name")
    description: Optional[str] = Field(default=None, description="Actor description")
    category: ActorCategory = Field(..., description="Actor category")
    
    # Cost structure
    cost_model: CostModel = Field(..., description="Cost model")
    cost_fixed: Decimal = Field(default=Decimal('0'), description="Fixed cost component")
    cost_variable: Decimal = Field(default=Decimal('0'), description="Variable cost component")
    cost_unit: Optional[str] = Field(default=None, description="Unit for variable cost (e.g., 'profiles')")
    cost_unit_size: int = Field(default=1, description="Unit size for variable cost (e.g., 1000)")
    
    # Input schema
    input_schema: Dict[str, Dict[str, Any]] = Field(..., description="Input schema")
    required_fields: List[str] = Field(default_factory=list, description="Required input fields")
    default_values: Dict[str, Any] = Field(default_factory=dict, description="Default values for input fields")
    
    # Output schema
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="Output schema")
    
    # Execution parameters
    default_timeout_secs: int = Field(default=300, description="Default timeout in seconds")
    memory_mbytes: Optional[int] = Field(default=None, description="Memory limit in megabytes")
    max_items_per_batch: Optional[int] = Field(default=None, 
                                           description="Maximum items to process in one batch")
    
    # API rate limiting
    rate_limit_requests_per_min: Optional[int] = Field(default=None, 
                                                  description="Maximum requests per minute")
    
    # Actor meta information
    version: str = Field(default="1.0.0", description="Actor configuration version")
    deprecated: bool = Field(default=False, description="Whether the actor is deprecated")
    alternative_actor_id: Optional[str] = Field(default=None, 
                                            description="Alternative actor ID if deprecated")

    @validator('required_fields')
    def validate_required_fields(cls, v: List[str], values: Dict[str, Any]) -> List[str]:
        """Validate that required fields exist in input schema."""
        input_schema = values.get('input_schema', {})
        for field in v:
            if field not in input_schema:
                raise ValueError(f"Required field '{field}' not found in input schema")
        return v

    @validator('default_values')
    def validate_default_values(cls, v: Dict[str, Any], values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that default values match input schema."""
        input_schema = values.get('input_schema', {})
        for field, value in v.items():
            if field not in input_schema:
                raise ValueError(f"Default value for '{field}' provided but field not in input schema")
        return v


class ActorConfigurations:
    """
    Manager for Apify actor configurations.
    
    Provides access to actor configurations, cost estimation, and input validation.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize actor configurations.
        
        Args:
            config_dir: Directory containing actor configuration files.
                       If None, use built-in configurations.
        """
        self.actors: Dict[str, ActorConfig] = {}
        self.actors_by_category: Dict[ActorCategory, Dict[str, ActorConfig]] = {
            category: {} for category in ActorCategory
        }
        self.config_dir = config_dir
        
        # Either load from files or use built-in configurations
        if self.config_dir and os.path.exists(self.config_dir):
            self._load_from_files()
        else:
            self._load_built_in_configs()
    
    def _load_from_files(self) -> None:
        """Load actor configurations from files in config_dir."""
        for filename in os.listdir(self.config_dir):
            if filename.endswith(('.yaml', '.yml', '.json')):
                file_path = os.path.join(self.config_dir, filename)
                
                try:
                    # Load configuration data
                    if filename.endswith('.json'):
                        with open(file_path, 'r') as f:
                            actor_data = json.load(f)
                    else:
                        with open(file_path, 'r') as f:
                            actor_data = yaml.safe_load(f)
                    
                    # Create actor config and add to collections
                    actor_config = ActorConfig.model_validate(actor_data)
                    self._add_actor_config(actor_config)
                    
                except Exception as e:
                    print(f"Error loading actor configuration from {file_path}: {e}")
    
    def _load_built_in_configs(self) -> None:
        """Load built-in actor configurations."""
        # LinkedIn actors
        self._add_actor_config(ActorConfig(
            id="LpVuK3Zozwuipa5bp",
            name="LinkedIn Profile Bulk Scraper",
            description="Extracts data from LinkedIn user profiles in bulk",
            category=ActorCategory.LINKEDIN,
            cost_model=CostModel.PER_UNIT,
            cost_fixed=Decimal('0'),
            cost_variable=Decimal('4.0'),
            cost_unit="profiles",
            cost_unit_size=1000,
            input_schema={
                "profileUrls": {"type": "array", "description": "LinkedIn profile URLs to scrape"},
                "includeSkills": {"type": "boolean", "description": "Include skills section"},
                "includeEducation": {"type": "boolean", "description": "Include education section"},
                "includeExperience": {"type": "boolean", "description": "Include experience section"},
                "proxyConfiguration": {"type": "object", "description": "Proxy configuration"},
            },
            required_fields=["profileUrls"],
            default_values={
                "includeSkills": True,
                "includeEducation": True,
                "includeExperience": True,
            },
            output_schema={
                "profile": "object",
                "skills": "array",
                "education": "array",
                "experience": "array",
            },
            default_timeout_secs=600,
            max_items_per_batch=1000,
        ))
        
        self._add_actor_config(ActorConfig(
            id="A3cAPGpwBEG8RJwse",
            name="LinkedIn Posts Bulk Scraper",
            description="Extracts recent posts from LinkedIn profiles or companies",
            category=ActorCategory.LINKEDIN,
            cost_model=CostModel.PER_UNIT,
            cost_fixed=Decimal('0'),
            cost_variable=Decimal('2.0'),
            cost_unit="posts",
            cost_unit_size=1000,
            input_schema={
                "profileUrls": {"type": "array", "description": "LinkedIn profile URLs to scrape posts from"},
                "maxPostsPerProfile": {"type": "integer", "description": "Maximum number of posts per profile"},
                "includeComments": {"type": "boolean", "description": "Include post comments"},
                "proxyConfiguration": {"type": "object", "description": "Proxy configuration"},
            },
            required_fields=["profileUrls"],
            default_values={
                "maxPostsPerProfile": 10,
                "includeComments": False,
            },
            output_schema={
                "posts": "array",
                "profile": "object",
            },
            default_timeout_secs=300,
            max_items_per_batch=500,
        ))
        
        self._add_actor_config(ActorConfig(
            id="3rgDeYgLhr6XrVnjs",
            name="LinkedIn Company Profile Scraper",
            description="Extracts detailed information from LinkedIn company profiles",
            category=ActorCategory.LINKEDIN,
            cost_model=CostModel.BASE_PLUS_UNIT,
            cost_fixed=Decimal('10.0'),
            cost_variable=Decimal('0.1'),
            cost_unit="companies",
            cost_unit_size=1,
            input_schema={
                "companyUrls": {"type": "array", "description": "LinkedIn company URLs to scrape"},
                "includeJobs": {"type": "boolean", "description": "Include job listings"},
                "includePeople": {"type": "boolean", "description": "Include people/employees"},
                "proxyConfiguration": {"type": "object", "description": "Proxy configuration"},
            },
            required_fields=["companyUrls"],
            default_values={
                "includeJobs": False,
                "includePeople": True,
            },
            output_schema={
                "company": "object",
                "employees": "array",
                "jobs": "array",
            },
            default_timeout_secs=300,
        ))
        
        # Social media actors
        self._add_actor_config(ActorConfig(
            id="KoJrdxJCTtpon81KY",
            name="Facebook Posts Scraper",
            description="Extracts posts and engagement metrics from Facebook pages",
            category=ActorCategory.SOCIAL_MEDIA,
            cost_model=CostModel.BASE_PLUS_UNIT,
            cost_fixed=Decimal('35.0'),
            cost_variable=Decimal('0.5'),
            cost_unit="pages",
            cost_unit_size=1,
            input_schema={
                "pageUrls": {"type": "array", "description": "Facebook page URLs to scrape"},
                "maxPostsPerPage": {"type": "integer", "description": "Maximum number of posts per page"},
                "includeComments": {"type": "boolean", "description": "Include post comments"},
                "proxyConfiguration": {"type": "object", "description": "Proxy configuration"},
            },
            required_fields=["pageUrls"],
            default_values={
                "maxPostsPerPage": 20,
                "includeComments": False,
            },
            output_schema={
                "posts": "array",
                "page": "object",
            },
            default_timeout_secs=600,
        ))
        
        self._add_actor_config(ActorConfig(
            id="61RPP7dywgiy0JPD0",
            name="Twitter/X Scraper",
            description="Extracts tweets and engagement metrics from Twitter/X profiles",
            category=ActorCategory.SOCIAL_MEDIA,
            cost_model=CostModel.PER_UNIT,
            cost_fixed=Decimal('0'),
            cost_variable=Decimal('0.4'),
            cost_unit="tweets",
            cost_unit_size=1000,
            input_schema={
                "usernames": {"type": "array", "description": "Twitter/X usernames to scrape"},
                "maxTweetsPerUser": {"type": "integer", "description": "Maximum number of tweets per user"},
                "includeReplies": {"type": "boolean", "description": "Include replies to tweets"},
                "includeRetweets": {"type": "boolean", "description": "Include retweets"},
                "proxyConfiguration": {"type": "object", "description": "Proxy configuration"},
            },
            required_fields=["usernames"],
            default_values={
                "maxTweetsPerUser": 20,
                "includeReplies": False,
                "includeRetweets": False,
            },
            output_schema={
                "tweets": "array",
                "profile": "object",
            },
            default_timeout_secs=300,
        ))
        
        # Company data actors
        self._add_actor_config(ActorConfig(
            id="5ms6D6gKCnJhZN61e",
            name="Erasmus+ Organisation Scraper",
            description="Extracts EU funding data and project participation from Erasmus+",
            category=ActorCategory.COMPANY_DATA,
            cost_model=CostModel.PER_UNIT,
            cost_fixed=Decimal('0'),
            cost_variable=Decimal('0.1'),
            cost_unit="queries",
            cost_unit_size=1,
            input_schema={
                "organizationIds": {"type": "array", "description": "Organization identifiers to search"},
                "organizationNames": {"type": "array", "description": "Organization names to search"},
                "maxResults": {"type": "integer", "description": "Maximum number of results"},
            },
            required_fields=["organizationIds"],
            default_values={
                "maxResults": 50,
            },
            output_schema={
                "organizations": "array",
                "projects": "array",
                "funding": "object",
            },
            default_timeout_secs=180,
        ))
        
        self._add_actor_config(ActorConfig(
            id="RIq8Fe9BdxSR4GUXY",
            name="Dun & Bradstreet Scraper",
            description="Extracts financial data, credit ratings, and industry classification",
            category=ActorCategory.COMPANY_DATA,
            cost_model=CostModel.BASE_PLUS_UNIT,
            cost_fixed=Decimal('30.0'),
            cost_variable=Decimal('0.2'),
            cost_unit="companies",
            cost_unit_size=1,
            input_schema={
                "companyIdentifiers": {"type": "array", "description": "Company DUNS numbers or other identifiers"},
                "companyNames": {"type": "array", "description": "Company names to search"},
                "includeFinancials": {"type": "boolean", "description": "Include detailed financial information"},
                "includeRiskScores": {"type": "boolean", "description": "Include risk scores and metrics"},
            },
            required_fields=["companyIdentifiers"],
            default_values={
                "includeFinancials": True,
                "includeRiskScores": True,
            },
            output_schema={
                "company": "object",
                "financials": "object",
                "risk": "object",
                "industry": "object",
            },
            default_timeout_secs=300,
        ))
        
        self._add_actor_config(ActorConfig(
            id="C6OyLbP5ixnfc5lYe",
            name="ZoomInfo Scraper",
            description="Extracts contact data, company insights, and technology stack information",
            category=ActorCategory.COMPANY_DATA,
            cost_model=CostModel.FIXED,
            cost_fixed=Decimal('20.0'),
            cost_variable=Decimal('0.1'),
            cost_unit="contacts",
            cost_unit_size=1,
            input_schema={
                "contactInfo": {"type": "array", "description": "Contact information to search"},
                "companyInfo": {"type": "array", "description": "Company information to search"},
                "maxContactsPerCompany": {"type": "integer", "description": "Maximum contacts per company"},
                "includeTechStack": {"type": "boolean", "description": "Include technology stack information"},
            },
            required_fields=["contactInfo"],
            default_values={
                "maxContactsPerCompany": 10,
                "includeTechStack": True,
            },
            output_schema={
                "contacts": "array",
                "company": "object",
                "technologies": "array",
            },
            default_timeout_secs=300,
        ))
        
        self._add_actor_config(ActorConfig(
            id="BBfgvSNWcySEk1jQO",
            name="Crunchbase Scraper",
            description="Extracts funding data, investors, and company timeline information",
            category=ActorCategory.COMPANY_DATA,
            cost_model=CostModel.MONTHLY_SUBSCRIPTION,
            cost_fixed=Decimal('30.0'),
            cost_variable=Decimal('0.05'),
            cost_unit="companies",
            cost_unit_size=1,
            input_schema={
                "companyNames": {"type": "array", "description": "Company names to search"},
                "companyUrls": {"type": "array", "description": "Company URLs to search"},
                "includeFundingRounds": {"type": "boolean", "description": "Include funding rounds information"},
                "includeInvestors": {"type": "boolean", "description": "Include investors information"},
                "maxInvestors": {"type": "integer", "description": "Maximum number of investors to include"},
            },
            required_fields=["companyNames"],
            default_values={
                "includeFundingRounds": True,
                "includeInvestors": True,
                "maxInvestors": 20,
            },
            output_schema={
                "company": "object",
                "funding": "array",
                "investors": "array",
                "timeline": "array",
            },
            default_timeout_secs=300,
        ))
    
    def _add_actor_config(self, config: ActorConfig) -> None:
        """
        Add an actor configuration to the collections.
        
        Args:
            config: Actor configuration to add.
        """
        self.actors[config.id] = config
        self.actors_by_category[config.category][config.id] = config
    
    def get_actor_config(self, actor_id: str) -> Optional[ActorConfig]:
        """
        Get an actor configuration by ID.
        
        Args:
            actor_id: Apify actor ID.
            
        Returns:
            Actor configuration if found, None otherwise.
        """
        return self.actors.get(actor_id)
    
    def get_actors_by_category(self, category: ActorCategory) -> Dict[str, ActorConfig]:
        """
        Get all actor configurations in a category.
        
        Args:
            category: Actor category.
            
        Returns:
            Dictionary mapping actor IDs to configurations.
        """
        return self.actors_by_category.get(category, {})
    
    def list_actors(self) -> List[ActorConfig]:
        """
        Get all actor configurations.
        
        Returns:
            List of all actor configurations.
        """
        return list(self.actors.values())
    
    def list_actors_by_category(self) -> Dict[ActorCategory, List[ActorConfig]]:
        """
        Get all actor configurations grouped by category.
        
        Returns:
            Dictionary mapping categories to lists of actor configurations.
        """
        return {
            category: list(actors.values())
            for category, actors in self.actors_by_category.items()
            if actors
        }
    
    def validate_actor_input(self, actor_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input data for an actor against its schema.
        
        Args:
            actor_id: Apify actor ID.
            input_data: Input data to validate.
            
        Returns:
            Validated and normalized input data with defaults applied.
            
        Raises:
            ValueError: If actor is not found or input data is invalid.
        """
        actor_config = self.get_actor_config(actor_id)
        if not actor_config:
            raise ValueError(f"Actor not found: {actor_id}")
        
        # Check required fields
        missing_fields = [
            field for field in actor_config.required_fields
            if field not in input_data
        ]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Apply default values for missing fields
        result = dict(actor_config.default_values)
        result.update(input_data)
        
        # Basic type validation
        for field, schema in actor_config.input_schema.items():
            if field not in result:
                continue
            
            field_type = schema.get("type")
            value = result[field]
            
            # Skip None values
            if value is None:
                continue
            
            # Validate field type
            if field_type == "array" and not isinstance(value, list):
                raise ValueError(f"Field '{field}' must be an array")
            elif field_type == "object" and not isinstance(value, dict):
                raise ValueError(f"Field '{field}' must be an object")
            elif field_type == "boolean" and not isinstance(value, bool):
                # Convert string "true"/"false" to boolean
                if isinstance(value, str):
                    if value.lower() == "true":
                        result[field] = True
                    elif value.lower() == "false":
                        result[field] = False
                    else:
                        raise ValueError(f"Field '{field}' must be a boolean")
                else:
                    raise ValueError(f"Field '{field}' must be a boolean")
            elif field_type == "integer" and not isinstance(value, int):
                # Try to convert to int
                try:
                    result[field] = int(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Field '{field}' must be an integer")
            elif field_type == "number" and not isinstance(value, (int, float)):
                # Try to convert to float
                try:
                    result[field] = float(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Field '{field}' must be a number")
            elif field_type == "string" and not isinstance(value, str):
                # Try to convert to string
                try:
                    result[field] = str(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Field '{field}' must be a string")
        
        return result
    
    def estimate_cost(self, actor_id: str, input_data: Dict[str, Any]) -> Decimal:
        """
        Estimate the cost of running an actor with the given input data.
        
        Args:
            actor_id: Apify actor ID.
            input_data: Input data for the actor.
            
        Returns:
            Estimated cost in USD as a Decimal.
            
        Raises:
            ValueError: If actor is not found.
        """
        actor_config = self.get_actor_config(actor_id)
        if not actor_config:
            raise ValueError(f"Actor not found: {actor_id}")
        
        # Fixed cost
        if actor_config.cost_model == CostModel.FIXED:
            return actor_config.cost_fixed
        
        # Monthly subscription
        if actor_config.cost_model == CostModel.MONTHLY_SUBSCRIPTION:
            return actor_config.cost_fixed
        
        # Per-unit cost calculation
        if actor_config.cost_model in (CostModel.PER_UNIT, CostModel.BASE_PLUS_UNIT):
            item_count = 0
            
            # Find the appropriate field to count based on the required fields
            for field in actor_config.required_fields:
                if field in input_data and isinstance(input_data[field], list):
                    item_count = len(input_data[field])
                    break
            
            # Calculate variable cost
            variable_cost = actor_config.cost_variable * Decimal(item_count) / Decimal(actor_config.cost_unit_size)
            
            # Add fixed cost for BASE_PLUS_UNIT model
            if actor_config.cost_model == CostModel.BASE_PLUS_UNIT:
                return actor_config.cost_fixed + variable_cost
            
            return variable_cost
        
        # Default fallback
        return actor_config.cost_fixed


# Singleton instance
_actor_configurations: Optional[ActorConfigurations] = None


def get_actor_configurations() -> ActorConfigurations:
    """
    Get the singleton actor configurations instance.
    
    Returns:
        Actor configurations instance.
    """
    global _actor_configurations
    
    if _actor_configurations is None:
        config_dir = None
        
        # Check if custom configuration directory is specified in settings
        if hasattr(settings, 'actor_config_dir') and settings.actor_config_dir:
            config_dir = settings.actor_config_dir
        
        _actor_configurations = ActorConfigurations(config_dir)
    
    return _actor_configurations


# Export the singleton instance for easy access
ACTOR_CONFIGS = get_actor_configurations() 