"""
Mock data fixtures for social media actors testing.
"""

# Facebook Posts Scraper Mock Data
FACEBOOK_POSTS_INPUT = {
    "usernames": ["techcorp", "johndoe.dev"],
    "numberOfPosts": 20,
    "includeComments": True,
    "includeReactions": True,
    "dateFrom": "2024-01-01",
    "dateTo": "2024-01-31"
}

FACEBOOK_POSTS_OUTPUT = [
    {
        "id": "fb_post_123",
        "url": "https://www.facebook.com/techcorp/posts/123456",
        "text": "We're excited to announce our latest product update! New features include...",
        "timestamp": "2024-01-20T15:30:00Z",
        "author": {
            "name": "TechCorp",
            "username": "techcorp",
            "verified": True,
            "profileUrl": "https://www.facebook.com/techcorp"
        },
        "media": [
            {
                "type": "image",
                "url": "https://facebook.com/image123.jpg",
                "description": "Product screenshot"
            }
        ],
        "reactions": {
            "like": 234,
            "love": 45,
            "wow": 12,
            "haha": 5,
            "sad": 0,
            "angry": 2
        },
        "comments": [
            {
                "id": "comment_456",
                "author": "John Smith",
                "text": "Amazing update! Can't wait to try it.",
                "timestamp": "2024-01-20T16:00:00Z",
                "likes": 8
            }
        ],
        "shares": 23
    },
    {
        "id": "fb_post_124",
        "url": "https://www.facebook.com/johndoe.dev/posts/789012",
        "text": "Just finished building a new React component library. Open source and ready to use!",
        "timestamp": "2024-01-18T10:15:00Z",
        "author": {
            "name": "John Doe",
            "username": "johndoe.dev",
            "verified": False,
            "profileUrl": "https://www.facebook.com/johndoe.dev"
        },
        "media": [],
        "reactions": {
            "like": 67,
            "love": 15,
            "wow": 8
        },
        "comments": [],
        "shares": 12
    }
]

# Twitter/X Scraper Mock Data
TWITTER_POSTS_INPUT = {
    "usernames": ["@techcorp", "@johndoedev"],
    "numberOfTweets": 50,
    "includeReplies": True,
    "includeRetweets": True,
    "dateFrom": "2024-01-01",
    "dateTo": "2024-01-31"
}

TWITTER_POSTS_OUTPUT = [
    {
        "id": "tweet_123456789",
        "url": "https://twitter.com/techcorp/status/123456789",
        "text": "🚀 Exciting news! Our AI-powered analytics platform is now live. Check it out: https://techcorp.com/analytics #AI #Analytics #TechNews",
        "timestamp": "2024-01-22T14:45:00Z",
        "author": {
            "name": "TechCorp",
            "username": "techcorp",
            "verified": True,
            "profileUrl": "https://twitter.com/techcorp",
            "followers": 125000,
            "following": 2500
        },
        "metrics": {
            "views": 45000,
            "likes": 892,
            "retweets": 234,
            "replies": 67,
            "bookmarks": 156
        },
        "media": [
            {
                "type": "image",
                "url": "https://pbs.twimg.com/media/image123.jpg",
                "alt": "Analytics dashboard screenshot"
            }
        ],
        "hashtags": ["AI", "Analytics", "TechNews"],
        "mentions": [],
        "urls": ["https://techcorp.com/analytics"],
        "isRetweet": False,
        "isReply": False
    },
    {
        "id": "tweet_987654321",
        "url": "https://twitter.com/johndoedev/status/987654321",
        "text": "Building in public: Day 30 of my #100DaysOfCode challenge. Today I learned about WebAssembly performance optimizations 🔧",
        "timestamp": "2024-01-19T09:30:00Z",
        "author": {
            "name": "John Doe 🚀",
            "username": "johndoedev",
            "verified": False,
            "profileUrl": "https://twitter.com/johndoedev",
            "followers": 8500,
            "following": 1200
        },
        "metrics": {
            "views": 12000,
            "likes": 156,
            "retweets": 23,
            "replies": 12,
            "bookmarks": 45
        },
        "media": [],
        "hashtags": ["100DaysOfCode"],
        "mentions": [],
        "urls": [],
        "isRetweet": False,
        "isReply": False
    },
    {
        "id": "tweet_456789123",
        "url": "https://twitter.com/johndoedev/status/456789123",
        "text": "RT @techcorp: 🚀 Exciting news! Our AI-powered analytics platform is now live...",
        "timestamp": "2024-01-22T15:00:00Z",
        "author": {
            "name": "John Doe 🚀",
            "username": "johndoedev",
            "verified": False,
            "profileUrl": "https://twitter.com/johndoedev"
        },
        "originalTweet": {
            "id": "tweet_123456789",
            "author": "@techcorp"
        },
        "metrics": {
            "views": 3000,
            "likes": 12,
            "retweets": 2,
            "replies": 0
        },
        "isRetweet": True,
        "isReply": False
    }
]

# Social Media Error Scenarios
SOCIAL_MEDIA_ERROR_SCENARIOS = {
    "invalid_username": {
        "input": {
            "usernames": ["@invalid_user_12345"]
        },
        "expected_error": "User not found"
    },
    "private_account": {
        "input": {
            "usernames": ["@private_user"]
        },
        "expected_result": []  # Empty result for private accounts
    },
    "suspended_account": {
        "input": {
            "usernames": ["@suspended_user"]
        },
        "expected_error": "Account suspended"
    },
    "rate_limited": {
        "input": {
            "usernames": ["@test_user"]
        },
        "expected_error": "Rate limit exceeded"
    }
}

# Platform-specific configurations
PLATFORM_CONFIGS = {
    "facebook": {
        "max_posts_per_request": 100,
        "required_fields": ["id", "text", "timestamp", "author"],
        "optional_fields": ["media", "reactions", "comments", "shares"]
    },
    "twitter": {
        "max_tweets_per_request": 100,
        "required_fields": ["id", "text", "timestamp", "author", "metrics"],
        "optional_fields": ["media", "hashtags", "mentions", "urls", "isRetweet", "isReply"]
    }
} 