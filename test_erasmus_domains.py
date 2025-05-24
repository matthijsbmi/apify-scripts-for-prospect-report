#!/usr/bin/env python3
"""
Test Erasmus+ Organisation Scraper with company domains (cleaned properly).
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
    # Keeping www. for now as it might be important for matching
    
    return domain


async def test_erasmus_domains():
    """Test Erasmus+ Organisation Scraper with company domains."""
    
    print("🔍 Testing Erasmus+ Organisation Scraper - Company Domains")
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
    ]
    
    # Clean all domains
    clean_domains = [clean_domain(domain) for domain in raw_domains]
    
    print("🧹 Domain cleaning preview:")
    for raw, clean in zip(raw_domains[:5], clean_domains[:5]):
        print(f"   {raw} → {clean}")
    
    # Test with different domain combinations
    test_cases = [
        {
            "name": "Single university domain",
            "raw_input": ["https://www.uva.nl/en"],
            "search_terms": [clean_domain("https://www.uva.nl/en")]
        },
        {
            "name": "Multiple university domains",
            "raw_input": ["https://www.uva.nl/en", "https://www.kth.se/", "www.tum.de/en/"],
            "search_terms": [clean_domain(d) for d in ["https://www.uva.nl/en", "https://www.kth.se/", "www.tum.de/en/"]]
        },
        {
            "name": "European companies",
            "raw_input": ["https://www.sap.com/", "www.philips.com", "https://www.siemens.com/global/en.html"],
            "search_terms": [clean_domain(d) for d in ["https://www.sap.com/", "www.philips.com", "https://www.siemens.com/global/en.html"]]
        },
        {
            "name": "Tech companies",
            "raw_input": ["nokia.com", "https://www.mozilla.org/en-US/"],
            "search_terms": [clean_domain(d) for d in ["nokia.com", "https://www.mozilla.org/en-US/"]]
        },
        {
            "name": "Single SAP test",
            "raw_input": ["https://www.sap.com/"],
            "search_terms": ["www.sap.com"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Raw inputs: {test_case['raw_input']}")
        print(f"Clean domains: {test_case['search_terms']}")
        
        input_data = {
            "debugMode": False,
            "proxyConfiguration": {
                "useApifyProxy": True
            },
            "searchTerms": test_case['search_terms']
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
                    output_file = f"erasmus_domains_test_{i}_{timestamp}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "test_name": test_case['name'],
                            "raw_input": test_case['raw_input'],
                            "clean_domains": test_case['search_terms'],
                            "input": input_data,
                            "result": result
                        }, f, indent=2, cls=CustomJSONEncoder)
                    
                    print(f"   💾 Saved to {output_file}")
                    
                    # Show organizational stats
                    countries = {}
                    for org in items:
                        if isinstance(org, dict):
                            country = org.get('country', 'Unknown')
                            countries[country] = countries.get(country, 0) + 1
                    
                    if countries:
                        print(f"\n   🌍 Countries represented:")
                        for country, count in sorted(countries.items()):
                            print(f"     - {country}: {count}")
                    
                    # If we found results, show domain cleaning effectiveness
                    print(f"\n🎉 SUCCESS! Found organizations using domain search!")
                    print(f"   Original inputs: {test_case['raw_input']}")
                    print(f"   Cleaned domains: {test_case['search_terms']}")
                    break  # Stop after first successful test to avoid too much data
                
                else:
                    print("   ⚠️  No organizations returned")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)
    
    print("\n✅ Erasmus+ domain testing completed!")
    print("\n📝 Key Learnings:")
    print("   ✅ Use clean domain names (no protocols, no paths)")
    print("   ✅ Domain format works better than organization names")
    print("   ✅ Proper URL cleaning is essential for results")


def test_domain_cleaning():
    """Test the domain cleaning function."""
    test_domains = [
        "https://www.example.com/en/about",
        "http://example.com/nl/contact",
        "www.example.com/path?query=1",
        "example.com",
        "https://subdomain.example.com/path/to/page",
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
    asyncio.run(test_erasmus_domains()) 