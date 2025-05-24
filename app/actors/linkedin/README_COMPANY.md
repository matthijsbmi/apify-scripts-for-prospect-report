# LinkedIn Company Profile Scraper

This actor integrates with the **sanjeta/linkedin-company-profile-scraper** Apify actor to extract comprehensive company information from LinkedIn company pages.

## Actor Details

- **Actor ID**: `sanjeta/linkedin-company-profile-scraper`
- **Purpose**: Scrape detailed company information from LinkedIn company profiles
- **Input Format**: Array of LinkedIn company URLs (slug-based format only)
- **Output Format**: Raw company data including employees, updates, locations, and similar companies

## Supported URL Formats

### ✅ Supported (Slug-based URLs)
```
https://www.linkedin.com/company/apifytech
https://linkedin.com/company/google
https://www.linkedin.com/company/microsoft
```

### ❌ Not Supported (ID-based URLs)
```
https://linkedin.com/company/10038644
```

> **Note**: To convert ID-based URLs to slug-based format, use the **LinkedIn Company Profile Id To Slug Finder** actor.

## Input Schema

The actor expects an array of LinkedIn company URLs:

```json
[
  "https://www.linkedin.com/company/apifytech",
  "https://www.linkedin.com/company/google",
  "https://www.linkedin.com/company/microsoft"
]
```

## Output Structure

The actor returns a clean structure with **no data duplication**:

```json
{
  "metadata": {
    "run_id": "fCyy4GvcGp62zQW1Y",
    "actor_id": "sanjeta/linkedin-company-profile-scraper",
    "status": "SUCCEEDED",
    "started_at": "2025-05-24T10:39:35.721000Z",
    "finished_at": "2025-05-24T10:39:42.408000Z",
    "items": [
      // Raw company data objects here
    ],
    "items_count": 2,
    "duration_secs": 6.687,
    "cost": "0.000",
    "success": true
  }
}
```

## Sample Company Data

Each company in `metadata.items` contains **26+ rich fields** of raw data:

```json
{
  "company_name": "Apify",
  "universal_name_id": "apifytech",
  "logo_image_url": "https://media.licdn.com/dms/image/v2/D4E0BAQEyOuiuTYXsaQ/company-logo_200_200/...",
  "background_cover_image_url": "https://media.licdn.com/dms/image/v2/D4E3DAQHr8Vokak8s5w/...",
  "linkedin_internal_id": "",
  "industry": "Software Development",
  "location": "",
  "follower_count": "12,736",
  "tagline": "On a mission to make the web more open and programmable.",
  "company_size_on_linkedin": 138,
  "about": "Apify is a full-stack web scraping and browser automation platform...",
  "website": "https://www.linkedin.com/redir/redirect?url=https%3A%2F%2Fapify%2Ecom%2F&urlhash=kGKH&trk=about_website",
  "industries": "",
  "company_size": "51-200 employees",
  "headquarters": "Prague",
  "type": "Privately Held",
  "founded": "2015",
  "specialties": "",
  "locations": [
    {
      "is_hq": true,
      "office_address_line_1": "Vodickova 704/36",
      "office_address_line_2": "Prague, 11100, CZ",
      "office_location_link": "https://www.bing.com/maps?where=Vodickova+704%2F36+Prague+11100+CZ&trk=org-locations_url"
    },
    {
      "is_hq": false,
      "office_address_line_1": "San Francisco, CA, US",
      "office_address_line_2": "",
      "office_location_link": "https://www.bing.com/maps?where=San+Francisco+CA+US&trk=org-locations_url"
    }
  ],
  "employees": [
    {
      "employee_photo": "https://media.licdn.com/dms/image/v2/C4E03AQHmtgVOIg7GeQ/...",
      "employee_name": "Jan Čurn",
      "employee_position": "CEO at Apify | Building a full-stack platform for web scraping and data for AI.",
      "employee_profile_url": "https://www.linkedin.com/in/jancurn?trk=org-employees"
    }
    // More employees...
  ],
  "updates": [
    {
      "text": "#PragueCrawl2025 talks are live. All of them. 🎥\n\nCouldn't come? Catch all Prague Crawl talks on YouTube...",
      "articlePostedDate": "1w",
      "totalLikes": "23"
    }
    // More updates...
  ],
  "similar_companies": [
    {
      "link": "https://cz.linkedin.com/company/itsmakehq?trk=similar-pages",
      "name": "Make",
      "summary": "Software Development",
      "location": "Prague, Praha 8"
    }
    // More similar companies...
  ],
  "affiliated_companies": [],
  "inputURL": "https://www.linkedin.com/company/apifytech",
  "follower_count_num": 12736,
  "status": "success"
}
```

## Data Fields Available

### Basic Company Information
- `company_name`: Official company name
- `universal_name_id`: LinkedIn URL slug identifier
- `linkedin_internal_id`: Internal LinkedIn identifier
- `tagline`: Company tagline/motto
- `about`: Company description/about section
- `website`: Company website URL
- `logo_image_url`: Company logo URL
- `background_cover_image_url`: Cover image URL
- `inputURL`: Original input URL used for scraping
- `status`: Scraping status ("success", "failed", etc.)

### Industry & Classification
- `industry`: Primary industry
- `industries`: All industries (may include multiple)
- `type`: Company type (e.g., "Privately Held", "Public Company")
- `specialties`: Company specialties/focus areas

### Size & Location
- `company_size`: Employee count range (e.g., "51-200 employees")
- `company_size_on_linkedin`: Exact employee count on LinkedIn
- `location`: Primary location
- `headquarters`: Headquarters location
- `founded`: Year founded
- `follower_count`: Number of LinkedIn followers (string)
- `follower_count_num`: Number of LinkedIn followers (integer)

### Locations Array
- `is_hq`: Whether this is the headquarters
- `office_address_line_1`: Address line 1
- `office_address_line_2`: Address line 2 (includes city, state, postal code, country)
- `office_location_link`: Map link to the location

### Employees Array
- `employee_photo`: Profile photo URL
- `employee_name`: Employee full name
- `employee_position`: Job title/position
- `employee_profile_url`: LinkedIn profile URL

### Company Updates/Posts Array
- `text`: Update content/text
- `articlePostedDate`: When the update was posted (relative format like "4mo")
- `totalLikes`: Number of likes on the update

### Similar Companies Array
- `link`: LinkedIn URL of similar company
- `name`: Company name
- `summary`: Industry/business summary
- `location`: Company location

### Affiliated Companies Array
- `link`: LinkedIn URL of affiliated company
- `name`: Company name
- `industry`: Industry classification
- `location`: Company location

## Usage Examples

### Python Implementation

```python
from app.actors.linkedin.company_actor import LinkedInCompanyActor

# Initialize the actor
company_actor = LinkedInCompanyActor()

# Scrape a single company
async def scrape_single_company():
    company_data = await company_actor.scrape_company(
        company_url="https://www.linkedin.com/company/apifytech",
        max_budget_usd=5.0
    )
    
    if company_data:
        print(f"Company: {company_data['company_name']}")
        print(f"Industry: {company_data['industry']}")
        print(f"Employees: {len(company_data['employees'])}")
        print(f"Updates: {len(company_data['updates'])}")
    
    return company_data

# Scrape multiple companies
async def scrape_multiple_companies():
    result = await company_actor.scrape_companies(
        company_urls=[
            "https://www.linkedin.com/company/apifytech",
            "https://www.linkedin.com/company/openai",
            "https://www.linkedin.com/company/microsoft"
        ],
        max_budget_usd=15.0,
        timeout_secs=900  # 15 minutes
    )
    
    # Access raw data from metadata
    metadata = result["metadata"]
    companies = metadata.items if metadata.items else []
    
    print(f"Successfully scraped {len(companies)} companies")
    print(f"Duration: {metadata.duration_secs}s")
    print(f"Cost: ${metadata.cost}")
    
    # Process each company
    for company in companies:
        print(f"- {company['company_name']}: {company['follower_count']} followers")
    
    return result
```

### API Endpoint Usage

```bash
# Multiple companies
curl -X POST "http://localhost:8000/api/v1/linkedin/companies" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "company_urls": [
      "https://www.linkedin.com/company/apifytech",
      "https://www.linkedin.com/company/openai"
    ],
    "max_budget_usd": 10.0,
    "timeout_secs": 600
  }'

# Test endpoint with sample data
curl -X GET "http://localhost:8000/api/v1/linkedin/test?actor_type=companies&sample_size=2" \
  -H "X-API-Key: your-api-key"
```

### Response Format

The API returns data in the following format:

```json
{
  "success": true,
  "data": [
    // Raw company objects from metadata.items
  ],
  "metadata": {
    "run_id": "fCyy4GvcGp62zQW1Y",
    "actor_id": "sanjeta/linkedin-company-profile-scraper",
    "status": "SUCCEEDED",
    "items_count": 2,
    "duration_secs": 6.687,
    "cost": "0.000",
    "execution_time": 8.234
  },
  "request_id": "12345678-1234-1234-1234-123456789012",
  "timestamp": "2025-05-24T12:39:42.408000Z"
}
```

## Error Handling

The actor includes comprehensive error handling for:

- **Invalid URLs**: Non-LinkedIn URLs or ID-based URLs will be rejected
- **Private/Restricted Companies**: Some companies may have restricted access
- **Rate Limiting**: LinkedIn may rate limit requests
- **Network Issues**: Timeout and connection errors are handled gracefully

## Cost Considerations

- **Typical Cost**: ~$0.01-0.05 per company profile
- **Factors Affecting Cost**:
  - Number of employees to extract
  - Number of company updates/posts
  - Network latency and retries
  - Proxy usage

## Rate Limiting & Best Practices

1. **Batch Processing**: Process companies in batches of 10-20 for better efficiency
2. **Timeout Settings**: Use appropriate timeouts (600-900 seconds for large companies)
3. **Budget Limits**: Set reasonable budget limits to prevent overruns
4. **Error Monitoring**: Monitor for rate limiting and access restrictions
5. **Data Validation**: Always validate URLs before processing

## Data Quality Notes

- **Employee Data**: Limited to publicly visible employees (typically 4-50 per company)
- **Update Frequency**: Company updates are recent posts (typically last 10-20 posts)
- **Location Accuracy**: Office locations depend on company-provided information
- **Similar Companies**: Algorithm-suggested similar companies based on LinkedIn's recommendations
- **Raw Data**: All data is returned in original format from LinkedIn without transformation

## Related Actors

- **LinkedIn Company Profile Id To Slug Finder**: Convert ID-based URLs to slug format
- **LinkedIn Profile Scraper**: Extract individual employee profiles
- **LinkedIn Posts Scraper**: Get more detailed post/update information

## API Endpoints

### Available Endpoints

- `POST /api/v1/linkedin/companies` - Scrape multiple companies
- `GET /api/v1/linkedin/pricing` - Get pricing information
- `GET /api/v1/linkedin/test` - Test with sample data

### Authentication

All API endpoints require authentication via API key:

```bash
-H "X-API-Key: your-api-key"
```

### Rate Limits

- Maximum 50 companies per request
- Timeout range: 120-3600 seconds
- Budget limits can be set per request 