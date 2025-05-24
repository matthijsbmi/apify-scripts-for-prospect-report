#!/usr/bin/env python3
"""
Test script for LinkedIn Posts Bulk Scraper.

This script tests the LinkedIn Posts Bulk Scraper with real profiles
and saves the output to JSON.
"""

import asyncio
import json
import os
from datetime import datetime
from decimal import Decimal

from app.actors.linkedin.posts_scraper import LinkedInPostsScraper
from app.core.apify_client import ApifyService
from app.cost.manager import CostManager


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime, Decimal, and other non-serializable objects."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            # For complex objects, convert to dict
            return obj.__dict__
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            # For iterables, convert to list
            return list(obj)
        
        # Let the base class default method raise the TypeError
        return super().default(obj)


async def test_linkedin_posts_scraper():
    """Test the LinkedIn Posts Scraper with real profiles."""
    
    print("🚀 Testing LinkedIn Posts Bulk Scraper")
    print("=" * 50)
    
    # Initialize services
    print("📊 Initializing services...")
    apify_service = ApifyService()
    cost_manager = CostManager()
    scraper = LinkedInPostsScraper(apify_service, cost_manager)
    
    # Check if Apify service is available
    if not apify_service.is_available():
        print("❌ Apify service not available. Please check your APIFY_API_TOKEN.")
        return
    
    print("✅ Apify service initialized successfully")
    
    # Test input - using public LinkedIn profiles
    test_input = {
        "profileUrls": [
            "https://www.linkedin.com/in/williamhgates/"  # Bill Gates' public profile
        ],
        "maxPostsPerProfile": 10,
        "includeComments": False  # Keep it simple for first test
    }
    
    print(f"📋 Testing with {len(test_input['profileUrls'])} profile(s)")
    for url in test_input['profileUrls']:
        print(f"   - {url}")
    print(f"   Max posts per profile: {test_input['maxPostsPerProfile']}")
    
    # Validate input
    print("\n🔍 Validating input...")
    try:
        scraper.validate_input(test_input)
        print("✅ Input validation passed")
    except ValueError as e:
        print(f"❌ Input validation failed: {e}")
        return
    
    # Estimate cost
    print("\n💰 Estimating cost...")
    cost_estimate = scraper.estimate_cost(test_input)
    print(f"   Estimated cost: ${cost_estimate['estimated_cost']:.4f}")
    print(f"   Compute units: {cost_estimate['compute_units']:.2f}")
    print(f"   Expected posts: {cost_estimate['cost_breakdown']['expected_posts']}")
    print(f"   Cost per post: ${cost_estimate['cost_breakdown']['base_cost_per_post']:.4f}")
    
    # Run the scraper
    print("\n🔄 Running LinkedIn Posts Scraper...")
    print("   This may take a few minutes...")
    
    try:
        result = await scraper.run_actor_async(test_input, timeout=600)
        
        if result.get("success"):
            print("✅ Scraping completed successfully!")
            
            # Display basic results info
            items = result.get("items", [])
            print(f"📊 Retrieved {len(items)} post(s)")
            
            if "run" in result:
                run_info = result["run"]
                print(f"   Run ID: {run_info.get('id', 'N/A')}")
                print(f"   Status: {run_info.get('status', 'N/A')}")
                print(f"   Compute units used: {run_info.get('computeUnits', 'N/A')}")
                
                if run_info.get('computeUnits'):
                    from app.core.config import settings
                    actual_cost = run_info['computeUnits'] * settings.default_compute_unit_cost
                    print(f"   Actual cost: ${actual_cost:.4f}")
            
            # Save to JSON file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"linkedin_posts_scraper_output_{timestamp}.json"
            
            print(f"\n💾 Saving output to {output_file}...")
            
            # Create output data with metadata
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "input": test_input,
                "cost_estimate": cost_estimate,
                "result": result,
                "summary": {
                    "posts_found": len(items),
                    "success": True,
                    "run_id": result.get("run", {}).get("id"),
                    "compute_units": result.get("run", {}).get("computeUnits"),
                    "status": result.get("run", {}).get("status")
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
            
            print(f"✅ Output saved to {output_file}")
            
            # Display sample post data (first few posts only, limited fields)
            if items:
                print(f"\n📋 Sample post data (showing first {min(3, len(items))} posts):")
                
                for i, post_item in enumerate(items[:3], 1):
                    print(f"\n   Post {i}:")
                    
                    if isinstance(post_item, dict):
                        # Show basic post info
                        if "post" in post_item:
                            post = post_item["post"]
                            print(f"     ID: {post.get('id', 'N/A')}")
                            print(f"     Type: {post.get('type', 'N/A')}")
                            
                            # Show content preview
                            content = post.get('content', '')
                            if content:
                                content_preview = content[:150] + "..." if len(content) > 150 else content
                                print(f"     Content: {content_preview}")
                            
                            # Show posted date
                            posted_at = post.get('postedAt', {})
                            if isinstance(posted_at, dict) and 'date' in posted_at:
                                print(f"     Posted: {posted_at.get('date', 'N/A')}")
                        
                        # Show author info
                        if "author" in post_item:
                            author = post_item["author"]
                            print(f"     Author: {author.get('name', 'N/A')}")
                        
                        # Show engagement
                        if "engagement" in post_item:
                            engagement = post_item["engagement"]
                            likes = engagement.get('likes', 0)
                            comments = engagement.get('comments', 0)
                            shares = engagement.get('shares', 0)
                            print(f"     Engagement: {likes} likes, {comments} comments, {shares} shares")
                        
                        # Show if it has media
                        if "media" in post_item and post_item["media"].get("images"):
                            image_count = len(post_item["media"]["images"])
                            print(f"     Media: {image_count} image(s)")
                
                # Show post types distribution
                post_types = {}
                for item in items:
                    if isinstance(item, dict) and "post" in item:
                        post_type = item["post"].get("type", "unknown")
                        post_types[post_type] = post_types.get(post_type, 0) + 1
                
                if post_types:
                    print(f"\n   📊 Post types distribution:")
                    for post_type, count in post_types.items():
                        print(f"     - {post_type}: {count}")
                
            else:
                print("\n⚠️  No post data found. This could be because:")
                print("   - The profile has no recent posts")
                print("   - The profile URL is not accessible")
                print("   - The LinkedIn profile is private or restricted")
                print("   - Rate limiting or anti-bot measures are in place")
            
        else:
            print("❌ Scraping failed!")
            error = result.get("error", "Unknown error")
            print(f"   Error: {error}")
            
            # Still save the error result
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"linkedin_posts_scraper_error_{timestamp}.json"
            
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "input": test_input,
                "cost_estimate": cost_estimate,
                "result": result,
                "summary": {
                    "success": False,
                    "error": error
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
            
            print(f"📄 Error details saved to {output_file}")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    # Display cost summary
    print(f"\n💰 Cost Summary:")
    print(f"   Total cost tracked: ${float(cost_manager.total_cost):.4f}")
    print(f"   Execution history: {len(cost_manager.execution_history)} records")
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_linkedin_posts_scraper()) 