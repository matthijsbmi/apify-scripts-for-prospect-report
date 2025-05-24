# Apify Scripts for Prospect Report - App Structure Documentation

## Overview

This FastAPI application provides a comprehensive prospect analysis system using various Apify actors to collect data from LinkedIn, social media platforms, and company databases. The app is designed with a modular architecture that separates concerns into distinct layers.

## Directory Structure

```
app/
├── main.py                 # FastAPI application entry point
├── __init__.py            # Package initialization
├── actors/                # Actor integrations (data collectors)
├── api/                   # API endpoints and models
├── core/                  # Core utilities and configuration
├── cost/                  # Cost management and tracking
├── models/                # Data models and schemas
├── orchestration/         # Workflow orchestration
├── services/              # Business logic services
└── validation/            # Data validation and quality scoring
```

## Core Components

### 1. **main.py** - Application Entry Point
- **Purpose**: FastAPI application setup and configuration
- **Key Features**:
  - CORS middleware configuration
  - Request/response logging middleware
  - Global exception handlers
  - Application lifespan management
  - Structured logging configuration
  - API documentation setup (/docs, /redoc)

### 2. **actors/** - Data Collection Layer
This directory contains all Apify actor integrations for data collection from various sources.

#### **actors/base.py** (29KB, 725 lines)
- **Purpose**: Base class for all Apify actor integrations
- **Key Features**:
  - Authentication handling with Apify API
  - Retry logic for failed requests
  - Cost calculation and budget monitoring
  - Standardized response processing
  - Error handling and logging
  - Both sync and async operation support

#### **actors/config.py** (25KB, 631 lines)
- **Purpose**: Configuration for all actor integrations
- **Contains**: Actor IDs, cost models, input/output schemas

#### **actors/utils.py** (7.0KB, 260 lines)
- **Purpose**: Utility functions shared across actors
- **Features**: URL validation, data transformation helpers

#### **actors/linkedin/** - LinkedIn Data Collection
- **company_actor.py** (4.4KB): LinkedIn Company Profile Scraper integration
  - Actor: `sanjeta/linkedin-company-profile-scraper`
  - Extracts: Company info, employees, updates, locations, similar companies
  - Features: 26+ data fields per company, raw data format
- **profile_scraper.py** (8.9KB): LinkedIn Profile Bulk Scraper integration
  - Actor: `LpVuK3Zozwuipa5bp`
  - Extracts: Personal info, experience, education, skills
- **posts_scraper.py** (8.7KB): LinkedIn Posts Bulk Scraper integration
  - Actor: `A3cAPGpwBEG8RJwse`
  - Extracts: Recent posts, engagement metrics, content analysis
- **transformers.py** (10KB): Data transformation functions
- **validators.py** (3.9KB): URL and data validation
- **service.py** (9.5KB): LinkedIn service orchestration

#### **actors/company/** - Company Data Collection
- **erasmus_actor.py** (10KB): Academic/research institution data
- **crunchbase_actor.py** (7.6KB): Startup/company financial data
- **zoominfo_actor.py** (8.5KB): B2B company intelligence
- **duns_actor.py** (7.8KB): Dun & Bradstreet business data
- **service.py** (21KB): Company data orchestration
- **transformers.py** (11KB): Data standardization
- **validators.py** (11KB): Company data validation

#### **actors/social/** - Social Media Data Collection
- **twitter_actor.py** (15KB): Twitter/X data collection
- **facebook_actor.py** (7.0KB): Facebook page data
- **service.py** (12KB): Social media orchestration
- **transformers.py** (10KB): Social data processing
- **validators.py** (6.3KB): Social media validation

### 3. **api/** - API Layer

#### **api/v1/api.py** (2.9KB)
- **Purpose**: Main API router configuration
- **Features**: Includes all endpoint routers with proper tags and prefixes

#### **api/v1/endpoints/** - API Endpoints
- **prospect.py** (16KB): Core prospect analysis endpoints
  - `/api/v1/prospect/analyze` - Single prospect analysis
  - `/api/v1/prospect/batch` - Batch processing
  - `/api/v1/prospect/estimate-cost` - Cost estimation
- **linkedin.py** (14KB): LinkedIn-specific endpoints
  - `/api/v1/linkedin/profiles` - Profile scraping
  - `/api/v1/linkedin/posts` - Posts scraping
  - `/api/v1/linkedin/companies` - Company scraping
  - `/api/v1/linkedin/pricing` - Pricing information
- **company.py** (19KB): Company data endpoints
  - Erasmus, Crunchbase, ZoomInfo, D&B integrations
- **social.py** (24KB): Social media endpoints
  - Twitter and Facebook data collection
- **actors.py** (5.7KB): Actor management endpoints
- **health.py** (11KB): System health monitoring
- **validation.py** (11KB): Data validation endpoints

### 4. **models/** - Data Models

#### **models/data.py** (25KB, 494 lines)
- **Purpose**: Comprehensive data models using Pydantic
- **Key Models**:
  - `Prospect`: Core prospect information with validation
  - `LinkedInProfile`, `LinkedInCompany`: LinkedIn data structures
  - `CompanyData`: Financial, employee, and industry data
  - `SocialMediaData`: Twitter and Facebook data
  - `ProspectAnalysisResponse`: Complete analysis results
  - `CostBreakdown`: Cost tracking and budgeting
  - `AnalysisParameters`: Configurable analysis options

### 5. **core/** - Core Infrastructure

#### **core/config.py** (2.2KB)
- **Purpose**: Application configuration using Pydantic Settings
- **Settings**: API configuration, Apify credentials, logging, caching, budgets

#### **core/apify_client.py** (10KB)
- **Purpose**: Enhanced Apify client with additional features
- **Features**: Connection pooling, retry logic, cost tracking

#### **core/exceptions.py** (6.7KB)
- **Purpose**: Custom exception classes for the application

#### **core/logging.py** (2.2KB)
- **Purpose**: Structured logging configuration

### 6. **cost/** - Cost Management

#### **cost/manager.py** (34KB, 990 lines)
- **Purpose**: Comprehensive cost tracking and budget management
- **Features**:
  - Real-time cost monitoring
  - Budget enforcement
  - Cost estimation algorithms
  - Actor cost modeling
  - Spending analytics

#### **cost/service.py** (9.7KB)
- **Purpose**: Cost management service layer

#### **cost/controller.py** (8.5KB)
- **Purpose**: Cost management API controllers

### 7. **orchestration/** - Workflow Management

#### **orchestration/orchestrator.py** (27KB, 702 lines)
- **Purpose**: Main workflow orchestration engine
- **Features**:
  - Multi-actor workflow coordination
  - Dependency management
  - Error recovery and retries
  - Parallel execution optimization

#### **orchestration/processor.py** (24KB, 625 lines)
- **Purpose**: Data processing pipeline
- **Features**:
  - Data transformation workflows
  - Quality scoring
  - Result aggregation

#### **orchestration/service.py** (8.2KB)
- **Purpose**: Orchestration service layer

### 8. **services/** - Business Logic

#### **services/prospect_analysis.py** (21KB, 529 lines)
- **Purpose**: Core prospect analysis business logic
- **Features**:
  - Analysis workflow coordination
  - Data enrichment strategies
  - Result compilation and scoring

#### **services/storage.py** (26KB, 841 lines)
- **Purpose**: Data storage and caching
- **Features**:
  - Result caching strategies
  - Data persistence
  - Cache invalidation

### 9. **validation/** - Data Quality

#### **validation/validator.py** (36KB, 910 lines)
- **Purpose**: Comprehensive data validation
- **Features**:
  - Input data validation
  - Output data quality checks
  - Data consistency verification

#### **validation/quality_scorer.py** (31KB, 797 lines)
- **Purpose**: Data quality scoring algorithms
- **Features**:
  - Confidence score calculation
  - Data completeness assessment
  - Source reliability scoring

#### **validation/service.py** (23KB, 586 lines)
- **Purpose**: Validation service orchestration

## Key Features & Capabilities

### 1. **Multi-Source Data Collection**
- **LinkedIn**: Profiles, posts, company data (26+ fields)
- **Social Media**: Twitter/X handles, Facebook pages
- **Company Data**: Financial info, employee data, industry analysis
- **Academic**: Research institutions via Erasmus actor

### 2. **Cost Management**
- Real-time budget monitoring
- Cost estimation before execution
- Per-actor cost breakdown
- Budget enforcement and alerts

### 3. **Quality Assurance**
- Data validation at multiple levels
- Confidence scoring for all data
- Source reliability assessment
- Data completeness analysis

### 4. **Scalability**
- Async/await throughout the application
- Batch processing capabilities
- Parallel actor execution
- Efficient data caching

### 5. **Monitoring & Observability**
- Structured logging with correlation IDs
- Health monitoring for all actors
- Performance metrics tracking
- Error tracking and alerting

## API Endpoints Summary

### Core Analysis
- `POST /api/v1/prospect/analyze` - Single prospect analysis
- `POST /api/v1/prospect/batch` - Batch prospect analysis
- `GET /api/v1/prospect/estimate-cost` - Cost estimation

### LinkedIn
- `POST /api/v1/linkedin/profiles` - Profile scraping
- `POST /api/v1/linkedin/posts` - Posts scraping
- `POST /api/v1/linkedin/companies` - Company scraping

### Company Data
- `POST /api/v1/company/erasmus/domain` - Academic institution by domain
- `POST /api/v1/company/crunchbase` - Startup data
- `POST /api/v1/company/zoominfo` - B2B intelligence

### Social Media
- `POST /api/v1/social/twitter/handles` - Twitter data by handle
- `POST /api/v1/social/facebook` - Facebook page data

### System
- `GET /api/v1/health` - System health check
- `GET /api/v1/actors` - Available actors list

## Data Flow

1. **Request** → API endpoint validates input
2. **Analysis Parameters** → Cost estimation and budget validation
3. **Orchestration** → Determines required actors and execution plan
4. **Actor Execution** → Parallel data collection from multiple sources
5. **Data Processing** → Transformation, validation, and quality scoring
6. **Result Compilation** → Aggregation and confidence scoring
7. **Response** → Structured response with metadata and cost breakdown

## Configuration

The application uses environment variables for configuration:

- `APIFY_API_TOKEN` - Apify API authentication
- `DEFAULT_MAX_BUDGET` - Default budget limits
- `DEFAULT_TIMEOUT` - Default actor timeouts
- `LOG_LEVEL` - Logging verbosity
- `ENVIRONMENT` - Deployment environment

## Testing & Development

The application includes comprehensive test coverage with:
- Unit tests for individual actors
- Integration tests for API endpoints
- Mock data for development and testing
- Health checks for monitoring

This architecture provides a scalable, maintainable, and feature-rich prospect analysis system with strong separation of concerns and comprehensive error handling. 