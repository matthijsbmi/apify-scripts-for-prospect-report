#!/usr/bin/env python3
"""
Test Erasmus+ Organisation Scraper with the correct websiteName parameter.
"""

import asyncio
import json
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlparse

from app.core.apify_client import ApifyService


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime, Decimal, and other non-serializable objects."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            return list(obj)
        return super().default(obj)


def clean_domain(domain_input):
    """
    Clean domain input by removing protocols, paths, and query parameters.
    
    Args:
        domain_input: Raw domain input (may include http/https, paths, etc.)
        
    Returns:
        Clean domain name only
    """
    # If it doesn't start with http/https, add https for parsing
    if not domain_input.startswith(('http://', 'https://')):
        domain_input = f"https://{domain_input}"
    
    # Parse the URL
    parsed = urlparse(domain_input)
    
    # Extract just the domain (netloc)
    domain = parsed.netloc
    
    # Remove www. prefix if present (optional, depending on requirements)
    # if domain.startswith('www.'):
    #     domain = domain[4:]
    
    return domain


async def test_erasmus_website():
    """Test Erasmus+ Organisation Scraper with websiteName parameter."""
    
    print("🔍 Testing Erasmus+ Organisation Scraper - Website Domain")
    print("=" * 70)
    
    apify_service = ApifyService()
    actor_id = "5ms6D6gKCnJhZN61e"  # Erasmus+ Organisation Scraper
    
    if not apify_service.is_available():
        print("❌ Apify service not available")
        return
    
    # Test with real company domains (raw inputs that need cleaning)
    raw_domains = [
        # Universities (likely to be in Erasmus+ database)
        "https://www.uva.nl/en",  # University of Amsterdam
        "https://www.kth.se/",
        "www.tum.de/en/",  # Technical University of Munich
        "https://www.ub.edu/web/ub/ca/",  # University of Barcelona
        "sorbonne-universite.fr",
        
        # European companies that might participate
        "https://www.sap.com/",
        "www.philips.com",
        "https://www.siemens.com/global/en.html",
        "nokia.com",
        
        # Other organizations
        "https://www.mozilla.org/en-US/",
        "https://europa.eu/",
        
        # Business Models Inc (from user's original request)
        "https://www.businessmodelsinc.com/"
    ]
    
    # Clean all domains
    clean_domains = [clean_domain(domain) for domain in raw_domains]
    
    print("🧹 Domain cleaning preview:")
    for raw, clean in zip(raw_domains[:5], clean_domains[:5]):
        print(f"   {raw} → {clean}")
    
    # Test with different domains
    test_cases = [
        {
            "name": "University of Amsterdam",
            "raw_input": "https://www.uva.nl/en",
            "website_name": clean_domain("https://www.uva.nl/en")
        },
        {
            "name": "Technical University of Munich",
            "raw_input": "www.tum.de/en/",
            "website_name": clean_domain("www.tum.de/en/")
        },
        {
            "name": "SAP",
            "raw_input": "https://www.sap.com/",
            "website_name": clean_domain("https://www.sap.com/")
        },
        {
            "name": "Nokia",
            "raw_input": "nokia.com",
            "website_name": clean_domain("nokia.com")
        },
        {
            "name": "Business Models Inc",
            "raw_input": "https://www.businessmodelsinc.com/",
            "website_name": clean_domain("https://www.businessmodelsinc.com/")
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Raw input: {test_case['raw_input']}")
        print(f"Clean domain: {test_case['website_name']}")
        
        # Use the correct input format with websiteName parameter
        input_data = {
            "debugMode": False,
            "proxyConfiguration": {
                "useApifyProxy": True
            },
            "websiteName": test_case['website_name'],
            "searchTerms": []  # Empty array as per the example
        }
        
        try:
            result = await apify_service.run_actor_async(
                actor_id=actor_id,
                input_data=input_data,
                timeout_secs=300  # Longer timeout for domain searches
            )
            
            if result.get("success"):
                items = result.get("items", [])
                run_info = result.get("run", {})
                
                print(f"✅ Success! Retrieved {len(items)} organizations")
                print(f"   Run ID: {run_info.get('id', 'N/A')}")
                print(f"   Status: {run_info.get('status', 'N/A')}")
                print(f"   Compute units: {run_info.get('computeUnits', 'N/A')}")
                
                if items:
                    print(f"   Data structure keys: {list(items[0].keys()) if items[0] else 'None'}")
                    
                    # Show sample organization data
                    for j, org in enumerate(items[:3], 1):  # Show first 3 orgs
                        print(f"\n   📋 Organization {j}:")
                        if isinstance(org, dict):
                            # Extract key fields
                            name = org.get('name', org.get('legalName', 'N/A'))
                            legal_name = org.get('legalName', 'N/A')
                            business_name = org.get('businessName', 'N/A')
                            country = org.get('country', 'N/A')
                            city = org.get('city', 'N/A')
                            website = org.get('website', 'N/A')
                            org_id = org.get('organisationId', 'N/A')
                            pic = org.get('pic', 'N/A')
                            
                            print(f"     Name: {name}")
                            print(f"     Legal Name: {legal_name}")
                            print(f"     Business Name: {business_name}")
                            print(f"     Country: {country}")
                            print(f"     City: {city}")
                            print(f"     Website: {website}")
                            print(f"     Organization ID: {org_id}")
                            print(f"     PIC: {pic}")
                    
                    # Save successful result
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = f"erasmus_website_test_{i}_{timestamp}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "test_name": test_case['name'],
                            "raw_input": test_case['raw_input'],
                            "clean_domain": test_case['website_name'],
                            "input": input_data,
                            "result": result
                        }, f, indent=2, cls=CustomJSONEncoder)
                    
                    print(f"   💾 Saved to {output_file}")
                    
                    # Show organizational stats if available
                    if any('country' in org for org in items if isinstance(org, dict)):
                        countries = {}
                        for org in items:
                            if isinstance(org, dict) and 'country' in org:
                                country = org.get('country', 'Unknown')
                                countries[country] = countries.get(country, 0) + 1
                        
                        if countries:
                            print(f"\n   🌍 Countries represented:")
                            for country, count in sorted(countries.items()):
                                print(f"     - {country}: {count}")
                
                else:
                    print("   ⚠️  No organizations returned")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
    
    print("\n✅ Erasmus+ website testing completed!")
    print("\n📝 Key Learnings:")
    print("   ✅ Use websiteName parameter for domain searches")
    print("   ✅ Clean domains by removing protocols and paths")
    print("   ✅ Keep searchTerms as an empty array")


def test_domain_cleaning():
    """Test the domain cleaning function."""
    test_domains = [
        "https://www.example.com/en/about",
        "http://example.com/nl/contact",
        "www.example.com/path?query=1",
        "example.com",
        "https://subdomain.example.com/path/to/page",
        "https://www.businessmodelsinc.com/"
    ]
    
    print("🧪 Testing domain cleaning function:")
    for domain in test_domains:
        cleaned = clean_domain(domain)
        print(f"   {domain} → {cleaned}")


if __name__ == "__main__":
    # First test domain cleaning
    test_domain_cleaning()
    print("\n" + "="*50 + "\n")
    
    # Then test the actor
    asyncio.run(test_erasmus_website()) 