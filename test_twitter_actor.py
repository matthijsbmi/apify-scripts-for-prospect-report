#!/usr/bin/env python3
"""
Test script for Twitter Actor.

This script tests the Twitter Actor with real handles and search terms
and saves the output to JSON.
"""

import asyncio
import json
import os
from datetime import datetime
from decimal import Decimal

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.actors.social.twitter_actor import TwitterActor
from app.actors.base import ActorRunOptions


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
        elif hasattr(obj, '__str__'):  # Handle Pydantic Url objects and other string-like objects
            return str(obj)
        return super().default(obj)


async def test_twitter_actor():
    """Test the Twitter actor with various input formats."""
    
    # Check for environment variable
    if not os.getenv("APIFY_API_TOKEN"):
        print("❌ Error: APIFY_API_TOKEN environment variable not set")
        print("Please add your Apify API token to the .env file")
        return
    
    actor = TwitterActor()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("🐦 Testing Twitter Actor")
    print("=" * 50)
    
    # Test 1: Twitter handles only
    print("\n📍 Test 1: Twitter handles only")
    try:
        result1 = await actor.scrape_tweets(
            twitter_handles=["elonmusk", "apify"],
            max_items=5,
            sort="Latest"
        )
        
        print(f"✅ Actor run: {result1['metadata'].status}")
        print(f"📊 Items retrieved: {len(result1['data'])}")
        
        # Save results
        filename1 = f"twitter_actor_test_1_{timestamp}.json"
        with open(filename1, 'w', encoding='utf-8') as f:
            json.dump(result1, f, indent=2, cls=CustomJSONEncoder, ensure_ascii=False)
        print(f"💾 Results saved to: {filename1}")
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        # Save error
        error_data1 = {"error": str(e), "test": "twitter_handles_only"}
        filename1 = f"twitter_actor_error_1_{timestamp}.json"
        with open(filename1, 'w') as f:
            json.dump(error_data1, f, indent=2)
    
    # Test 2: Search terms only
    print("\n📍 Test 2: Search terms only")
    try:
        result2 = await actor.scrape_tweets(
            search_terms=["web scraping", "AI automation"],
            max_items=5,
            sort="Latest",
            tweet_language="en"
        )
        
        print(f"✅ Actor run: {result2['metadata'].status}")
        print(f"📊 Items retrieved: {len(result2['data'])}")
        
        # Save results
        filename2 = f"twitter_actor_test_2_{timestamp}.json"
        with open(filename2, 'w', encoding='utf-8') as f:
            json.dump(result2, f, indent=2, cls=CustomJSONEncoder, ensure_ascii=False)
        print(f"💾 Results saved to: {filename2}")
        
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        # Save error
        error_data2 = {"error": str(e), "test": "search_terms_only"}
        filename2 = f"twitter_actor_error_2_{timestamp}.json"
        with open(filename2, 'w') as f:
            json.dump(error_data2, f, indent=2)
    
    # Test 3: Both handles and search terms
    print("\n📍 Test 3: Both handles and search terms")
    try:
        result3 = await actor.scrape_tweets(
            twitter_handles=["apify"],
            search_terms=["web scraping"],
            max_items=3,
            sort="Latest",
            tweet_language="en",
            minimum_favorites=1
        )
        
        print(f"✅ Actor run: {result3['metadata'].status}")
        print(f"📊 Items retrieved: {len(result3['data'])}")
        
        # Save results
        filename3 = f"twitter_actor_test_3_{timestamp}.json"
        with open(filename3, 'w', encoding='utf-8') as f:
            json.dump(result3, f, indent=2, cls=CustomJSONEncoder, ensure_ascii=False)
        print(f"💾 Results saved to: {filename3}")
        
        # Display sample tweet data
        if result3['data']:
            sample_tweet = result3['data'][0]
            print(f"\n📝 Sample tweet:")
            print(f"   Author: @{sample_tweet.get('author', {}).get('username', 'Unknown')}")
            print(f"   Text: {sample_tweet.get('text', 'No text')[:100]}...")
            print(f"   Likes: {sample_tweet.get('likeCount', 0)}")
            print(f"   Retweets: {sample_tweet.get('retweetCount', 0)}")
        
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        # Save error
        error_data3 = {"error": str(e), "test": "both_handles_and_search"}
        filename3 = f"twitter_actor_error_3_{timestamp}.json"
        with open(filename3, 'w') as f:
            json.dump(error_data3, f, indent=2)
    
    # Create summary
    summary = {
        "timestamp": timestamp,
        "tests_conducted": [
            "twitter_handles_only",
            "search_terms_only", 
            "both_handles_and_search"
        ],
        "actor_id": "61RPP7dywgiy0JPD0",
        "input_format": {
            "twitterHandles": ["list of handles"],
            "searchTerms": ["list of search terms"],
            "maxItems": "number",
            "sort": "Latest|Popular",
            "tweetLanguage": "en|es|etc"
        }
    }
    
    summary_filename = f"twitter_actor_summary_{timestamp}.json"
    with open(summary_filename, 'w') as f:
        json.dump(summary, f, indent=2, cls=CustomJSONEncoder)
    
    print(f"\n📋 Test summary saved to: {summary_filename}")
    print("\n🎉 Twitter Actor testing completed!")


if __name__ == "__main__":
    asyncio.run(test_twitter_actor()) 