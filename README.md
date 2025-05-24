# Apify Scripts for Prospect Report

A comprehensive collection of Apify actor integration scripts for generating prospect reports with data from LinkedIn, Erasmus+, Twitter, and other sources. **This project provides reusable scripts and components designed for integration into larger prospect analysis workflows and backend systems.**

## Project Purpose

This repository contains production-ready Apify actor integration scripts that can be embedded into larger prospect analysis platforms, CRM systems, or data processing pipelines. The scripts are designed to be modular, extensible, and easily integrated into existing backend architectures.

**Key Use Cases:**
- Integration into existing CRM systems
- Embedding in data processing pipelines
- Component library for prospect analysis platforms
- Building blocks for custom data collection workflows
- Backend services for prospect research applications

## Overview

This project provides a unified interface for running various Apify actors to collect prospect data. Each actor is wrapped in a Python class that handles input validation, cost estimation, data transformation, and error handling. The system is designed for integration into larger applications rather than standalone deployment.

## Data Storage Architecture

### MongoDB Storage Approach

The system is designed to store raw actor output data in MongoDB using the following architecture:

**Collection Structure:**
- **`actor_runs`**: Stores execution metadata and links related actor outputs
- **`linkedin_profiles`**: Raw LinkedIn profile data
- **`linkedin_posts`**: Raw LinkedIn posts data  
- **`linkedin_companies`**: Raw LinkedIn company data
- **`facebook_posts`**: Raw Facebook posts data
- **`twitter_posts`**: Raw Twitter/X posts data
- **`erasmus_organizations`**: Raw Erasmus+ organization data
- **`zoominfo_companies`**: Raw ZoomInfo company data
- **`duns_companies`**: Raw Dun & Bradstreet company data

**Document Structure Example:**
```json
{
  "_id": "ObjectId",
  "run_id": "uuid-linking-related-outputs",
  "actor_id": "LpVuK3Zozwuipa5bp", 
  "actor_name": "LinkedIn Profile Bulk Scraper",
  "execution_timestamp": "2024-01-15T10:30:00Z",
  "input_parameters": {...},
  "raw_output": {...},
  "cost_usd": 0.004,
  "execution_time_secs": 45.2,
  "status": "completed",
  "metadata": {...}
}
```

**Grouping by Execution Run:**
- All actors executed together share the same `run_id`
- Individual actor results stored in separate collections
- Metadata in `actor_runs` collection links related outputs
- Enables both individual actor queries and run-based grouping

### Storage Implementation Status

✅ **Raw Data Models**: All data structures designed for MongoDB compatibility
✅ **Actor Response Formats**: Standardized JSON output from all actors  
✅ **Cost and Metadata Tracking**: Comprehensive execution information captured
⚠️ **MongoDB Integration**: **Storage layer setup but requires configuration based on target backend implementation**

**Implementation Notes:**
- Raw JSON output from each actor is MongoDB-ready
- Document schemas align with Pydantic models for validation
- Storage service interface defined for multiple backend support
- Specific MongoDB connection and configuration depends on target system

## Quick Start

1. **Environment Setup**:
   ```bash
   cp env.example .env
   # Add your APIFY_API_TOKEN to .env
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run API Server**:
   ```bash
   python start_api.py
   ```

4. **Access Documentation**:
   - **Interactive API Docs**: http://localhost:8005/docs
   - **Alternative Docs**: http://localhost:8005/redoc
   - **API Info**: http://localhost:8005/api/v1/

## Implementation Status

🎉 **All 6 Primary Actors Completed and Production Ready!**

| Category | Actors | Status |
|----------|--------|--------|
| **LinkedIn** | Profile, Posts, Companies | ✅ Complete |
| **Company Intelligence** | Erasmus+, ZoomInfo, Dun & Bradstreet | ✅ Complete |
| **Social Media** | Facebook Posts, Twitter/X | ✅ Complete |

**Latest Update**: Dun & Bradstreet Scraper with advanced filtering (revenue, employees, country, industry) and 20+ fields per company

## Implemented Actors

### 1. LinkedIn Profile Bulk Scraper ✅
**Actor ID**: `LpVuK3Zozwuipa5bp`  
**Cost Model**: Pay-per-use ($0.004 per profile)  
**Max Profiles**: 100 per run

#### Input Format
```json
{
  "urls": [
    "https://www.linkedin.com/in/billgates/",
    "https://www.linkedin.com/in/elonmusk/"
  ]
}
```

#### Key Features
- ✅ Profile data extraction (name, headline, location, connections)
- ✅ Experience and education history
- ✅ Skills and certifications
- ✅ Data transformation to standardized format
- ✅ Cost tracking and validation

#### Usage Example
```python
from app.actors.linkedin.profile_scraper import LinkedInProfileScraper
from app.core.apify_client import ApifyService
from app.cost.manager import CostManager

scraper = LinkedInProfileScraper(
    apify_service=ApifyService(),
    cost_manager=CostManager()
)

result = await scraper.scrape_profiles([
    "https://www.linkedin.com/in/billgates/"
])
```

### 2. LinkedIn Posts Bulk Scraper ✅
**Actor ID**: `A3cAPGpwBEG8RJwse`  
**Cost Model**: Pay-per-use ($0.002 per post)  
**Max Posts**: 1000 per run

#### Input Format
```json
{
  "profileUrls": [
    "https://www.linkedin.com/in/billgates/"
  ],
  "maxPostsPerProfile": 10
}
```

#### Key Features
- ✅ Recent posts extraction from LinkedIn profiles
- ✅ Content, engagement metrics, and metadata
- ✅ Author information and posting dates
- ✅ Article links and media detection

#### Usage Example
```python
from app.actors.linkedin.posts_scraper import LinkedInPostsScraper

scraper = LinkedInPostsScraper(apify_service, cost_manager)
result = await scraper.scrape_posts([
    "https://www.linkedin.com/in/billgates/"
], max_posts=10)
```

### 3. Erasmus+ Organisation Scraper ✅
**Actor ID**: `5ms6D6gKCnJhZN61e`  
**Cost Model**: Pay-per-use  
**Search Types**: Domain, Name, Organization ID

#### Input Format (Domain Search - Recommended)
```json
{
  "websiteName": "www.uva.nl",
  "searchTerms": [],
  "debugMode": false,
  "proxyConfiguration": {
    "useApifyProxy": true
  }
}
```

#### Input Format (Name Search)
```json
{
  "searchTerms": ["University of Amsterdam"],
  "websiteName": "",
  "debugMode": false
}
```

#### Key Features
- ✅ Organization data from Erasmus+ database
- ✅ Legal names, business names, and registration info
- ✅ Location data (country, city)
- ✅ PIC codes and VAT numbers
- ✅ Website validation

#### Usage Example
```python
from app.actors.company.erasmus_actor import ErasmusActor

actor = ErasmusActor()

# Domain search (most effective)
result = await actor.scrape_by_domain("www.uva.nl")

# Name search
result = await actor.scrape_single_organization(
    organization_name="University of Amsterdam"
)
```

### 4. ZoomInfo Scraper ✅
**Actor ID**: `C6OyLbP5ixnfc5lYe`  
**Cost Model**: Pay-per-use (~$0.01-0.05 per company)  
**Input Types**: ZoomInfo URLs or company names

#### Input Format
```json
{
  "urls_or_companies_names": [
    "https://www.zoominfo.com/c/walmart-inc/155353090",
    "walmart",
    "microsoft"
  ],
  "include_similar_companies": true,
  "max_retries_per_url": 2
}
```

#### Key Features
- ✅ Comprehensive company data with 19+ fields per company
- ✅ Revenue details with currency and text format ($681 Billion)
- ✅ Complete address and contact information
- ✅ Founding year and industry classifications
- ✅ Similar companies with CEO information
- ✅ Complete funding history with investor details
- ✅ Social network URLs (LinkedIn, Twitter, Facebook)
- ✅ Stock symbols and business descriptions
- ✅ Employee counts and organizational data

#### Output Sample
```json
{
  "url": "https://www.zoominfo.com/c/walmart-inc/155353090",
  "id": "155353090",
  "name": "Walmart",
  "full_name": "Walmart Inc",
  "revenue": 680985000,
  "revenue_text": "$681 Billion",
  "website": "//corporate.walmart.com",
  "stock_symbol": "WMT",
  "address": {
    "street": "702 SW 8th St",
    "city": "Bentonville",
    "state": "Arkansas",
    "country": "United States"
  },
  "similar_company_urls": [...],
  "fundings": {...},
  "social_network_urls": [...]
}
```

#### Usage Example
```python
from app.actors.company.zoominfo_actor import ZoomInfoActor

actor = ZoomInfoActor()

# Search by company names (recommended)
result = await actor.scrape_companies([
    "walmart", "microsoft", "amazon"
])

# Search by ZoomInfo URLs
result = await actor.scrape_companies([
    "https://www.zoominfo.com/c/walmart-inc/155353090"
])

# Single company search
company = await actor.scrape_single_company("walmart")
```

### 5. Facebook Posts Scraper ✅
**Actor ID**: `KoJrdxJCTtpon81KY`  
**Cost Model**: Pay-per-use  
**Input Types**: Facebook page URLs

#### Input Format
```json
{
  "startUrls": [
    {"url": "https://www.facebook.com/nytimes"}
  ],
  "resultsLimit": 50,
  "proxy": {
    "useApifyProxy": true,
    "apifyProxyGroups": ["RESIDENTIAL"]
  },
  "maxRequestRetries": 10
}
```

#### Key Features
- ✅ Post content and engagement metrics (likes, comments, shares)
- ✅ Post metadata (timestamps, URLs, IDs)
- ✅ Page information (name, ID)
- ✅ Media content detection (images, videos)
- ✅ Complete post text and links
- ✅ Raw output with 15+ fields per post

#### Output Sample
```json
{
  "facebookUrl": "https://www.facebook.com/nytimes/",
  "pageId": "5281959998",
  "postId": "10153102379324999",
  "pageName": "The New York Times",
  "url": "https://www.facebook.com/nytimes/posts/pfbid02H3AMTEUUKeVQfHUxARkcz12qCNep8Xhta5czh5rGwVWKf15UdFksFEZiKJ5BiSRul",
  "time": "Thursday, 6 April 2023 at 07:10",
  "timestamp": 1680790202000,
  "likes": 9,
  "comments": 17,
  "shares": null,
  "text": "Vice President Kamala Harris's visit to Africa last week was designed to send a message — China is not your friend. The U.S. is.",
  "link": "https://nyti.ms/3m5ATQF",
  "thumb": "https://external.fbhx1-1.fna.fbcdn.net/..."
}
```

#### Usage Example
```python
from app.actors.social.facebook_actor import FacebookActor

actor = FacebookActor()

# Scrape posts from multiple pages (default: 50 posts total)
result = await actor.scrape_posts([
    "https://www.facebook.com/nytimes",
    "https://www.facebook.com/microsoft"
])

# Scrape posts from single page with custom limit
posts = await actor.scrape_single_page(
    "https://www.facebook.com/nytimes", 
    results_limit=25
)
```

### 6. Dun & Bradstreet Scraper ✅
**Actor ID**: `RIq8Fe9BdxSR4GUXY`  
**Cost Model**: Pay-per-use (~1 Compute unit per 1000 pages)  
**Input Types**: Company names or search terms (with optional advanced filters)

#### Primary Usage: Simple Company Name Search
```json
{
  "searchTerm": "Microsoft Corporation",
  "maxItems": 5
}
```

#### Advanced Usage: Search with Filters (Optional)
```json
{
  "searchTerm": "Apple",
  "revenueMin": 1000000,
  "numberOfEmployeesMin": 100,
  "yearStartFrom": 1980,
  "countryIn": "Australia, Germany, Russian, Spain, Japan, United, France",
  "industryIn": "Computer, Retail",
  "maxItems": 10,
  "proxyConfiguration": {
    "useApifyProxy": true,
    "apifyProxyCountry": "US"
  }
}
```

#### Key Features
- ✅ **Simple company name searches** (primary use case)
- ✅ Company profiles with 20+ fields per result
- ✅ Revenue and employee count data ($245.12B for Microsoft)
- ✅ Principal/executive information with roles (CEO: Satya Nadella)
- ✅ Complete address and contact details
- ✅ Industry classifications and business types
- ✅ Incorporation year and business structure
- ✅ Optional advanced filtering by revenue, employees, year, country, industry
- ✅ Raw output with comprehensive business data

#### Real Output Sample (Microsoft Corporation)
```json
{
  "url": "https://www.dnb.com/business-directory/company-profiles.microsoft_corporation.html",
  "name": "Microsoft Corporation",
  "website": "www.microsoft.com",
  "numberOfEmployees": null,
  "addressLocality": "Redmond",
  "addressCountry": "United States",
  "addressRegion": "WA",
  "streetAddress": "1 Microsoft Way",
  "postalCode": "98052-8300",
  "type": null,
  "role": null,
  "industry": [
    "Software Publishers",
    "Computer Systems Design and Related Services",
    "Computer and Peripheral Equipment Manufacturing",
    "Operating systems computer software",
    "Application computer software"
  ],
  "principals": [
    {
      "name": "Satya Nadella",
      "position": "Chairman of the Board and Chief Executive Officer"
    }
  ],
  "revenue": 245120000000,
  "fiscalYearEnd": "JUN",
  "yearStart": null,
  "incorporated": null
}
```

#### Usage Example
```python
from app.actors.company.duns_actor import DunsActor

actor = DunsActor()

# Simple company name search (recommended for most use cases)
results = await actor.search_companies(
    search_term="Microsoft Corporation",
    max_items=5
)

# Search with optional filters for more specific results
results = await actor.search_companies(
    search_term="Apple",
    revenue_min=1000000,
    number_of_employees_min=100,
    country_in="Australia, United States",
    industry_in="Computer, Technology",
    max_items=10
)

# Search single company
company = await actor.search_single_company(
    search_term="Microsoft Corporation"
)
```

### 7. Twitter/X Scraper ✅
**Actor ID**: `61RPP7dywgiy0JPD0`  
**Cost Model**: Pay-per-use  
**Search Types**: Twitter handles, Search terms, Combined

#### Input Format
```json
{
  "twitterHandles": ["elonmusk", "taylorswift13"],
  "searchTerms": ["web scraping", "scraping from:apify"],
  "maxItems": 1000,
  "sort": "Latest",
  "start": "2021-07-01",
  "end": "2021-07-02",
  "tweetLanguage": "en"
}
```

#### Key Features
- ✅ Tweet content and engagement metrics
- ✅ Author information and metadata
- ✅ Filtering by engagement, verified status, media type
- ✅ Date range and language filtering
- ✅ Advanced search operators support

#### Usage Example
```python
from app.actors.social.twitter_actor import TwitterActor

actor = TwitterActor()

# Scrape tweets from specific users
result = await actor.scrape_tweets(
    twitter_handles=["elonmusk", "apify"],
    max_items=10
)

# Scrape tweets by search terms
result = await actor.scrape_tweets(
    search_terms=["web scraping", "AI automation"],
    max_items=10
)
```

## API Documentation

### LinkedIn Endpoints

#### Profile Scraping
```bash
POST /api/v1/linkedin/profiles
```

**Request Body:**
```json
{
  "urls": ["https://www.linkedin.com/in/billgates/"],
  "max_budget_usd": 1.0,
  "timeout_secs": 300
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "name": "Bill Gates",
      "headline": "Co-chair, Bill & Melinda Gates Foundation",
      "location": "Seattle, Washington",
      "connections": 8,
      "experience": [...],
      "education": [...]
    }
  ],
  "metadata": {
    "execution_time": 45.2,
    "actor_id": "LpVuK3Zozwuipa5bp",
    "cost_usd": 0.004
  },
  "request_id": "uuid-here"
}
```

#### Posts Scraping
```bash
POST /api/v1/linkedin/posts
```

**Request Body:**
```json
{
  "profile_urls": ["https://www.linkedin.com/in/billgates/"],
  "max_posts_per_profile": 10,
  "max_budget_usd": 1.0,
  "timeout_secs": 600
}
```

#### Company Scraping
```bash
POST /api/v1/linkedin/companies
```

**Request Body:**
```json
{
  "company_urls": ["https://www.linkedin.com/company/microsoft/"],
  "max_budget_usd": 1.0,
  "timeout_secs": 600
}
```

#### Pricing Information
```bash
GET /api/v1/linkedin/pricing
```

#### Test Endpoint
```bash
GET /api/v1/linkedin/test?actor_type=profiles&sample_size=1
```

### Company/Organization Endpoints

#### Erasmus Domain Search
```bash
POST /api/v1/company/erasmus/domain
```

**Request Body:**
```json
{
  "domain": "www.uva.nl",
  "max_budget_usd": 1.0,
  "timeout_secs": 300
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "legalName": "Universiteit van Amsterdam",
      "businessName": "University of Amsterdam",
      "country": "Netherlands",
      "city": "Amsterdam",
      "pic": "999845440",
      "vatNumber": "NL001234567B01",
      "website": "www.uva.nl"
    }
  ],
  "metadata": {
    "execution_time": 23.1,
    "actor_id": "5ms6D6gKCnJhZN61e",
    "search_method": "domain"
  },
  "request_id": "uuid-here"
}
```

#### Erasmus Name Search
```bash
POST /api/v1/company/erasmus/name
```

**Request Body:**
```json
{
  "organization_names": ["University of Amsterdam", "Oxford University"],
  "max_budget_usd": 2.0,
  "timeout_secs": 600
}
```

#### ZoomInfo Search
```bash
POST /api/v1/company/zoominfo
```

**Request Body:**
```json
{
  "urls_or_names": [
    "walmart", 
    "microsoft",
    "https://www.zoominfo.com/c/walmart-inc/155353090"
  ],
  "include_similar_companies": true,
  "max_budget_usd": 3.0,
  "timeout_secs": 600
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "url": "https://www.zoominfo.com/c/walmart-inc/155353090",
      "id": "155353090",
      "name": "Walmart",
      "full_name": "Walmart Inc",
      "revenue": 680985000,
      "revenue_currency": "$",
      "revenue_text": "$681 Billion",
      "website": "//corporate.walmart.com",
      "stock_symbol": "WMT",
      "address": {
        "street": "702 SW 8th St",
        "city": "Bentonville",
        "state": "Arkansas",
        "country": "United States",
        "zip": "72716"
      },
      "phone_number": "(479) 273-4000",
      "founding_year": 1962,
      "industries": [
        "Department Stores, Shopping Centers & Superstores",
        "Retail"
      ],
      "similar_company_urls": [...],
      "fundings": {...},
      "social_network_urls": [...]
    }
  ],
  "metadata": {
    "execution_time": 45.2,
    "actor_id": "C6OyLbP5ixnfc5lYe",
    "companies_found": 1
  },
  "request_id": "uuid-here"
}
```

#### ZoomInfo Pricing
```bash
GET /api/v1/company/zoominfo/pricing
```

#### D&B DUNS Search
```bash
POST /api/v1/company/duns
```

**Simple Company Name Search (Recommended):**
```json
{
  "search_term": "Microsoft Corporation",
  "max_items": 5,
  "timeout_secs": 300
}
```

**Advanced Search with Filters (Optional):**
```json
{
  "search_term": "Apple",
  "revenue_min": 1000000,
  "number_of_employees_min": 100,
  "year_start_from": 1980,
  "country_in": "Australia, United States, Canada",
  "industry_in": "Computer, Technology, Retail",
  "max_items": 10,
  "proxy_configuration": {
    "useApifyProxy": true,
    "apifyProxyCountry": "US"
  },
  "max_budget_usd": 2.0,
  "timeout_secs": 600
}
```

**Response (Microsoft Corporation Example):**
```json
{
  "success": true,
  "data": [
    {
      "url": "https://www.dnb.com/business-directory/company-profiles.microsoft_corporation.html",
      "name": "Microsoft Corporation",
      "website": "www.microsoft.com",
      "numberOfEmployees": null,
      "addressLocality": "Redmond",
      "addressCountry": "United States",
      "addressRegion": "WA",
      "streetAddress": "1 Microsoft Way",
      "postalCode": "98052-8300",
      "type": null,
      "role": null,
      "industry": [
        "Software Publishers",
        "Computer Systems Design and Related Services",
        "Computer and Peripheral Equipment Manufacturing"
      ],
      "principals": [
        {
          "name": "Satya Nadella",
          "position": "Chairman of the Board and Chief Executive Officer"
        }
      ],
      "revenue": 245120000000,
      "fiscalYearEnd": "JUN",
      "yearStart": null,
      "incorporated": null
    }
  ],
  "metadata": {
    "execution_time": 135.4,
    "actor_id": "RIq8Fe9BdxSR4GUXY",
    "search_term": "Microsoft Corporation",
    "filters_applied": {
      "revenue_min": null,
      "employees_min": null,
      "year_start_from": null,
      "countries": null,
      "industries": null
    }
  },
  "request_id": "uuid-here"
}
```

#### D&B Business Intelligence
```bash
# Simple company name search (recommended)
curl -X POST "http://localhost:8005/api/v1/company/duns" \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "Microsoft Corporation",
    "max_items": 5,
    "timeout_secs": 300
  }'

# Advanced search with filters (optional)
curl -X POST "http://localhost:8005/api/v1/company/duns" \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "Apple",
    "revenue_min": 1000000,
    "number_of_employees_min": 100,
    "country_in": "Australia, United States",
    "industry_in": "Computer, Technology",
    "max_items": 5,
    "max_budget_usd": 2.0,
    "timeout_secs": 600
  }'
```

#### D&B Pricing
```bash
GET /api/v1/company/duns/pricing
```

#### Company Test Endpoint
```bash
GET /api/v1/company/test?actor_type=erasmus-domain&sample_size=1
```

### Social Media Endpoints

#### Twitter Handles Scraping
```bash
POST /api/v1/social/twitter/handles
```

**Request Body:**
```json
{
  "twitter_handles": ["elonmusk", "apify"],
  "max_items": 100,
  "sort": "Latest",
  "tweet_language": "en",
  "minimum_favorites": 1,
  "only_verified_users": false,
  "max_budget_usd": 2.0,
  "timeout_secs": 600
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "text": "Tweet content here...",
      "author": {
        "username": "elonmusk",
        "name": "Elon Musk",
        "verified": true
      },
      "likeCount": 1500,
      "retweetCount": 300,
      "createdAt": "2024-01-15T10:30:00Z"
    }
  ],
  "metadata": {
    "execution_time": 85.3,
    "actor_id": "61RPP7dywgiy0JPD0",
    "search_method": "handles"
  },
  "request_id": "uuid-here"
}
```

#### Twitter Search Terms
```bash
POST /api/v1/social/twitter/search
```

**Request Body:**
```json
{
  "search_terms": ["web scraping", "AI automation"],
  "max_items": 1000,
  "sort": "Latest",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "tweet_language": "en",
  "include_search_terms": true,
  "max_budget_usd": 5.0,
  "timeout_secs": 600
}
```

#### Twitter Combined Search
```bash
POST /api/v1/social/twitter/combined
```

**Request Body:**
```json
{
  "twitter_handles": ["apify"],
  "search_terms": ["web scraping"],
  "max_items": 500,
  "sort": "Latest",
  "tweet_language": "en",
  "minimum_favorites": 5,
  "max_budget_usd": 3.0,
  "timeout_secs": 600
}
```

#### Facebook Posts
```bash
POST /api/v1/social/facebook
```

**Request Body:**
```json
{
  "page_urls": [
    "https://www.facebook.com/nytimes",
    "https://www.facebook.com/microsoft"
  ],
  "results_limit": 50,
  "max_request_retries": 10,
  "proxy_configuration": {
    "useApifyProxy": true,
    "apifyProxyGroups": ["RESIDENTIAL"]
  },
  "max_budget_usd": 2.0,
  "timeout_secs": 600
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "facebookUrl": "https://www.facebook.com/nytimes/",
      "pageId": "5281959998",
      "postId": "10153102379324999",
      "pageName": "The New York Times",
      "text": "Vice President Kamala Harris's visit to Africa...",
      "likes": 9,
      "comments": 17,
      "shares": null,
      "timestamp": 1680790202000,
      "url": "https://www.facebook.com/nytimes/posts/pfbid02H3AM...",
      "link": "https://nyti.ms/3m5ATQF"
    }
  ],
  "metadata": {
    "execution_time": 45.2,
    "actor_id": "KoJrdxJCTtpon81KY",
    "posts_found": 1
  },
  "request_id": "uuid-here"
}
```

#### Facebook Pricing
```bash
GET /api/v1/social/facebook/pricing
```

#### Social Test Endpoint
```bash
GET /api/v1/social/test?actor_type=twitter-handles&sample_size=1
```

### General API Endpoints

#### System Health
```bash
GET /api/v1/health
```

#### Available Actors
```bash
GET /api/v1/actors
```

#### Specific Actor Info
```bash
GET /api/v1/actors/{actor_id}
```

#### API Information
```bash
GET /api/v1/
```

## Architecture

### Core Components

1. **BaseActor** (`app/actors/base.py`): Foundation class with common functionality
   - Retry logic and error handling
   - Cost calculation and budget validation
   - Standardized response processing
   - Apify client integration

2. **ApifyService** (`app/core/apify_client.py`): Direct Apify API integration
   - Raw actor execution
   - Dataset item retrieval
   - Run status monitoring

3. **CostManager** (`app/cost/manager.py`): Budget and cost tracking
   - Per-actor cost estimation
   - Budget validation
   - Usage reporting

4. **Data Models** (`app/models/data.py`): Standardized data structures
   - CompanyData, ProfileData, PostData, TwitterData
   - Validation and serialization
   - Type safety with Pydantic

### Data Transformation

Each actor includes a transformer that converts raw Apify output to standardized formats:

- **LinkedIn Profile**: Transforms nested profile data to `ProfileData` model
- **LinkedIn Posts**: Converts post arrays to structured `PostData` objects  
- **Erasmus**: Maps organization data to `CompanyData` format
- **Twitter**: Maps tweets to structured tweet objects with metadata

## Input Validation

### LinkedIn Profile Scraper
- Validates LinkedIn URL format (`linkedin.com/in/`)
- Checks URL accessibility
- Limits batch size to 100 profiles
- Validates profile URL patterns

### LinkedIn Posts Scraper  
- Validates profile URLs (`linkedin.com/in/`)
- Enforces post count limits (max 1000)
- Checks date ranges if provided

### Erasmus Organisation Scraper
- Domain cleaning (removes protocols, paths)
- Name normalization
- Organization ID validation
- Ensures at least one search parameter

### Twitter Actor
- Handle format validation (removes @ if present)
- Search term sanitization
- Date range validation (YYYY-MM-DD format)
- Language code validation
- At least one of handles or search terms required

## Error Handling

All actors implement comprehensive error handling:

1. **Input Validation Errors**: Clear messages for invalid parameters
2. **API Errors**: Retry logic with exponential backoff
3. **Timeout Handling**: Configurable timeouts per actor
4. **Cost Overruns**: Budget validation before execution
5. **Data Transformation Errors**: Graceful fallbacks with error logging

## Testing

Each actor includes comprehensive test scripts and API test endpoints:

- **Unit Tests**: Individual method validation
- **Integration Tests**: Full actor execution with real data
- **Input Format Tests**: Validation of various input combinations
- **Error Condition Tests**: Behavior under failure scenarios
- **API Test Endpoints**: Built-in testing with sample data

### Example Test Execution
```bash
# Test LinkedIn Profile Scraper
python test_linkedin_profile_scraper.py

# Test Twitter Actor
python test_twitter_actor.py

# Test via API
curl -X GET "http://localhost:8005/api/v1/linkedin/test?actor_type=profiles&sample_size=1"
curl -X GET "http://localhost:8005/api/v1/social/test?actor_type=twitter-handles&sample_size=1"
```

## Cost Management

### Per-Actor Pricing
- **LinkedIn Profile**: $0.004 per profile
- **LinkedIn Posts**: $0.002 per post  
- **LinkedIn Companies**: $0.01-0.05 per company
- **Erasmus**: Variable based on search complexity
- **ZoomInfo**: $0.01-0.05 per company (comprehensive data with 19+ fields)
- **Facebook Posts**: Pay-per-use (varies by page activity and post count)
- **Twitter**: Variable based on search volume and criteria

### Budget Controls
- Pre-execution cost estimation
- Maximum budget enforcement per request
- Real-time cost tracking
- Usage reporting and analytics
- Built-in cost estimation endpoints

## Configuration

### Environment Variables
```bash
APIFY_API_TOKEN=your_apify_token_here
LOG_LEVEL=INFO
DEFAULT_TIMEOUT=300
```

### Actor Configuration
Actor-specific settings are managed in `app/actors/config.py`:
- API endpoints and timeouts
- Cost models and pricing
- Input validation rules
- Output transformation settings

## API Integration Examples

### LinkedIn Profile Analysis
```bash
# Scrape multiple LinkedIn profiles
curl -X POST "http://localhost:8005/api/v1/linkedin/profiles" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.linkedin.com/in/billgates/",
      "https://www.linkedin.com/in/satyanadella/"
    ],
    "max_budget_usd": 0.5,
    "timeout_secs": 300
  }'
```

### LinkedIn Posts Collection
```bash
# Get recent posts from LinkedIn profiles
curl -X POST "http://localhost:8005/api/v1/linkedin/posts" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_urls": ["https://www.linkedin.com/in/billgates/"],
    "max_posts_per_profile": 20,
    "max_budget_usd": 1.0,
    "timeout_secs": 600
  }'
```

### Erasmus Organization Search
```bash
# Search organization by domain
curl -X POST "http://localhost:8005/api/v1/company/erasmus/domain" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "www.uva.nl",
    "max_budget_usd": 1.0,
    "timeout_secs": 300
  }'

# Search by organization names
curl -X POST "http://localhost:8005/api/v1/company/erasmus/name" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_names": ["University of Amsterdam"],
    "max_budget_usd": 1.0,
    "timeout_secs": 600
  }'
```

### Twitter Data Collection
```bash
# Scrape tweets from specific users
curl -X POST "http://localhost:8005/api/v1/social/twitter/handles" \
  -H "Content-Type: application/json" \
  -d '{
    "twitter_handles": ["elonmusk", "apify"],
    "max_items": 50,
    "sort": "Latest",
    "tweet_language": "en",
    "max_budget_usd": 2.0,
    "timeout_secs": 600
  }'

# Search tweets by keywords
curl -X POST "http://localhost:8005/api/v1/social/twitter/search" \
  -H "Content-Type: application/json" \
  -d '{
    "search_terms": ["web scraping", "AI automation"],
    "max_items": 100,
    "sort": "Latest",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "tweet_language": "en",
    "max_budget_usd": 3.0,
    "timeout_secs": 600
  }'
```

### Facebook Posts Collection
```bash
# Scrape Facebook posts from pages
curl -X POST "http://localhost:8005/api/v1/social/facebook" \
  -H "Content-Type: application/json" \
  -d '{
    "page_urls": [
      "https://www.facebook.com/nytimes",
      "https://www.facebook.com/microsoft"
    ],
    "results_limit": 50,
    "max_request_retries": 10,
    "max_budget_usd": 2.0,
    "timeout_secs": 600
  }'
```

### D&B Business Intelligence
```bash
# Search D&B database with filters
curl -X POST "http://localhost:8005/api/v1/company/duns" \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "Apple",
    "revenue_min": 1000000,
    "number_of_employees_min": 100,
    "country_in": "Australia, United States",
    "industry_in": "Computer, Technology",
    "max_items": 5,
    "max_budget_usd": 2.0,
    "timeout_secs": 600
  }'
```

### Company Intelligence Gathering
```bash
# ZoomInfo company profiles
curl -X POST "http://localhost:8005/api/v1/company/zoominfo" \
  -H "Content-Type: application/json" \
  -d '{
    "urls_or_names": ["walmart", "microsoft", "amazon"],
    "include_similar_companies": true,
    "max_budget_usd": 3.0,
    "timeout_secs": 600
  }'
```

## Final Project Status

**Script Collection Complete**: All 6 primary Apify actor integration scripts implemented and production-ready for embedding into larger systems:

| Category | Actors | Status | Integration Features |
|----------|--------|--------|---------------------|
| **LinkedIn** | Profile, Posts, Companies | ✅ Complete | Full profile data, recent posts, company insights |
| **Company Intelligence** | Erasmus+, ZoomInfo, Dun & Bradstreet | ✅ Complete | EU funding data, comprehensive company profiles, financial intelligence |
| **Social Media** | Facebook Posts, Twitter/X | ✅ Complete | Social engagement metrics, content analysis |

### Key Integration Features

**✅ Modular Actor Scripts:**
- LinkedIn Profile Scraper: $0.004/profile with comprehensive data extraction
- LinkedIn Posts Scraper: $0.002/post with engagement metrics  
- LinkedIn Company Scraper: Complete company profiles and employee insights
- Facebook Posts Scraper: 50 posts default, raw output with 20+ fields per post
- Twitter/X Scraper: Advanced search with filtering capabilities
- Erasmus+ Scraper: EU organization database with funding information
- ZoomInfo Scraper: 19+ fields per company including revenue, contacts, tech stack
- Dun & Bradstreet Scraper: Advanced filtering (revenue, employees, country, industry), 20+ fields per company

**✅ Integration-Ready Framework:**
- Standardized Python classes for all actors with consistent interfaces
- Complete input validation and error handling per actor
- Raw JSON output optimized for database storage (MongoDB-ready)
- Comprehensive cost tracking and budget management
- Modular design allowing selective actor integration

**✅ Data Storage Preparation:**
- MongoDB-compatible document structures for all actor outputs
- Execution run grouping with shared `run_id` for related actor calls
- Separate collections per actor type while maintaining run relationships
- Complete metadata preservation (cost, timing, execution status)
- Storage service interface designed for multiple backend implementations

**✅ Production-Ready Features:**
- Comprehensive error handling and validation for all actors
- Budget controls and timeout management
- Real-world validation with actual Apify actor calls
- Performance optimizations for concurrent execution
- Complete documentation with integration examples

### Integration Architecture

**Script Components:**
- Independent actor classes in `app/actors/` for each data source
- Shared base class architecture (`BaseActor`) for consistent functionality
- Validation and transformation utilities in `app/actors/*/validators.py` and `app/actors/*/transformers.py`
- Cost management utilities in `app/cost/manager.py`
- Storage interface definitions in `app/storage/`

**API Layer (Optional):**
- FastAPI implementation available for microservice deployment
- RESTful endpoints for all actors at `/api/v1/`
- OpenAPI/Swagger documentation for API integration
- Docker-ready for containerized deployment

**Database Integration:**
- Storage service interface supports multiple backends
- MongoDB document schemas defined and validated
- Raw data preservation with comprehensive metadata
- Run-based grouping for related actor executions

### Integration Guidance

**For CRM Integration:**
- Import actor classes directly into existing Python applications
- Use individual actor methods for targeted data collection
- Integrate cost management for budget-controlled execution
- Store results using provided storage interface adapters

**For Data Pipeline Integration:**
- Use actor classes as pipeline components
- Implement custom storage backends using provided interfaces  
- Leverage built-in validation and error handling
- Monitor costs and performance using metadata tracking

**For Microservice Architecture:**
- Deploy FastAPI application as prospect data microservice
- Use REST API endpoints for cross-service communication
- Implement authentication and rate limiting as needed
- Scale horizontally using containerization

### Development Status

The core actor integration scripts are complete and tested. The system provides:

1. **Complete Actor Library** (6 primary actors): All data sources implemented and validated
2. **Integration Framework**: Modular design ready for embedding in larger systems
3. **Storage Preparation**: MongoDB-ready with flexible backend support
4. **Documentation**: Comprehensive integration guides and API documentation

**Next Steps for Integration:**
- Configure storage backend for target system (MongoDB, PostgreSQL, etc.)
- Implement authentication layer appropriate for target environment
- Add custom validation rules specific to integration requirements
- Configure monitoring and alerting for production deployment

The scripts are ready for integration into larger prospect analysis platforms, CRM systems, or data processing pipelines.

## Development

### Adding New Actors

1. Create actor class inheriting from `BaseActor`
2. Implement input validation and transformation
3. Add cost estimation logic
4. Create comprehensive tests
5. Add API endpoints in appropriate router
6. Update configuration and documentation

### Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

## License

[Add your license information here]

## Support

For questions or issues:
- Create an issue in the repository
- Check the test scripts for usage examples
- Review the actor documentation in `/app/actors/`
- Use the built-in API test endpoints for debugging 

**Technical Documentation:**
- [MongoDB Storage Guide](MONGODB_STORAGE_GUIDE.md) - Complete guide for storing actor outputs in MongoDB
- [API Documentation](http://localhost:8005/docs) - Interactive Swagger documentation  
- [Alternative Docs](http://localhost:8005/redoc) - ReDoc format documentation

## Data Storage Integration

### MongoDB Storage Ready

All actor outputs can be efficiently stored in MongoDB with proper separation and linking. See the **[MongoDB Storage Guide](MONGODB_STORAGE_GUIDE.md)** for:

✅ **Collection Structure**: Separate collections per actor type  
✅ **Document Examples**: Real data samples from each actor  
✅ **Integration Code**: Node.js and Python implementation examples  
✅ **Schema Design**: Indexing and performance optimization  
✅ **Run Linking**: Connect related actor outputs from same execution  

**Storage Configuration Note**: The exact storage implementation depends on your backend architecture. The guide provides the foundation and examples that can be adapted to your specific database setup and requirements.

## Implementation Status 