"""
Mock data fixtures for LinkedIn actors testing.
"""

# LinkedIn Profile Bulk Scraper Mock Data
LINKEDIN_PROFILE_INPUT = {
    "profileUrls": [
        "https://www.linkedin.com/in/john-doe-123/",
        "https://www.linkedin.com/in/jane-smith-456/"
    ],
    "includeSkills": True,
    "includeEducation": True,
    "includeExperience": True,
    "includeRecommendations": False,
    "includeCourses": False
}

LINKEDIN_PROFILE_OUTPUT = [
    {
        "profile": {
            "fullName": "John Doe",
            "headline": "Senior Software Engineer at TechCorp",
            "location": "San Francisco, CA",
            "profileUrl": "https://www.linkedin.com/in/john-doe-123/",
            "connectionsCount": 500,
            "followersCount": 1200,
            "summary": "Experienced software engineer with 8+ years in full-stack development...",
            "industry": "Computer Software"
        },
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "TechCorp",
                "startDate": "2022-01",
                "endDate": None,
                "location": "San Francisco, CA",
                "description": "Leading development of microservices architecture using Python and React",
                "duration": "2 years"
            },
            {
                "title": "Software Engineer",
                "company": "StartupXYZ",
                "startDate": "2019-06",
                "endDate": "2021-12",
                "location": "Palo Alto, CA",
                "description": "Full-stack development using Django and JavaScript",
                "duration": "2 years 7 months"
            }
        ],
        "education": [
            {
                "school": "Stanford University",
                "degree": "Master of Science",
                "field": "Computer Science",
                "startDate": "2017",
                "endDate": "2019",
                "description": "Focus on Machine Learning and AI"
            },
            {
                "school": "UC Berkeley",
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "startDate": "2013",
                "endDate": "2017",
                "description": "Summa Cum Laude"
            }
        ],
        "skills": [
            {"name": "Python", "endorsements": 25},
            {"name": "JavaScript", "endorsements": 18},
            {"name": "React", "endorsements": 12},
            {"name": "Node.js", "endorsements": 15},
            {"name": "AWS", "endorsements": 20}
        ]
    },
    {
        "profile": {
            "fullName": "Jane Smith",
            "headline": "Product Manager at InnovaCorp",
            "location": "New York, NY",
            "profileUrl": "https://www.linkedin.com/in/jane-smith-456/",
            "connectionsCount": 800,
            "followersCount": 2500,
            "summary": "Product leader with 6+ years experience in B2B SaaS...",
            "industry": "Software"
        },
        "experience": [
            {
                "title": "Senior Product Manager",
                "company": "InnovaCorp",
                "startDate": "2021-03",
                "endDate": None,
                "location": "New York, NY",
                "description": "Leading product strategy for enterprise platform",
                "duration": "3 years"
            }
        ],
        "education": [
            {
                "school": "Harvard Business School",
                "degree": "Master of Business Administration",
                "field": "Technology & Operations",
                "startDate": "2018",
                "endDate": "2020"
            }
        ],
        "skills": [
            {"name": "Product Management", "endorsements": 35},
            {"name": "Strategy", "endorsements": 28},
            {"name": "Analytics", "endorsements": 22}
        ]
    }
]

# LinkedIn Posts Bulk Scraper Mock Data
LINKEDIN_POSTS_INPUT = {
    "profileUrls": [
        "https://www.linkedin.com/in/john-doe-123/"
    ],
    "numberOfPosts": 10,
    "includeComments": True,
    "includeReactions": True
}

LINKEDIN_POSTS_OUTPUT = [
    {
        "id": "post123",
        "url": "https://www.linkedin.com/posts/john-doe-123_activity-123456",
        "text": "Excited to share our latest product launch! After months of hard work...",
        "timestamp": "2024-01-15T10:30:00Z",
        "author": {
            "name": "John Doe",
            "username": "john-doe-123",
            "profileUrl": "https://www.linkedin.com/in/john-doe-123/"
        },
        "reactions": {
            "like": 45,
            "love": 12,
            "insightful": 8,
            "celebrate": 15
        },
        "comments": [
            {
                "author": "Jane Smith",
                "text": "Congratulations! This looks amazing.",
                "timestamp": "2024-01-15T11:00:00Z"
            }
        ],
        "reshares": 5
    },
    {
        "id": "post124",
        "url": "https://www.linkedin.com/posts/john-doe-123_activity-123457",
        "text": "Thoughts on the future of AI in software development...",
        "timestamp": "2024-01-10T14:20:00Z",
        "author": {
            "name": "John Doe",
            "username": "john-doe-123",
            "profileUrl": "https://www.linkedin.com/in/john-doe-123/"
        },
        "reactions": {
            "like": 32,
            "insightful": 18,
            "love": 5
        },
        "comments": [],
        "reshares": 3
    }
]

# LinkedIn Company Profile Scraper Mock Data
LINKEDIN_COMPANY_INPUT = [
    "https://www.linkedin.com/company/apifytech",
    "https://www.linkedin.com/company/google"
]

LINKEDIN_COMPANY_OUTPUT = [
    {
        "company_name": "Apify",
        "universal_name_id": "apifytech",
        "background_cover_image_url": "https://media.licdn.com/dms/image/D4E3DAQEmIocms5XB-A/image-scale_191_1128/0/1693828072729?e=1695034800&v=beta&t=IXE1hYgnwxtuP7P-EW4Xc4q5iAXLWN9lgKpUgIVQ0sI",
        "linkedin_internal_id": "",
        "industry": "IT Services and IT Consulting",
        "location": "Praha, Hlavní město Praha",
        "follower_count": "4,289",
        "tagline": "On a mission to make the web more open and programmable.",
        "company_size_on_linkedin": 83,
        "about": "Apify is a web scraping and automation platform that lets you extract data from websites, process data and automate workflows on the web. \n\nTurn any website into an API!",
        "website": "https://www.linkedin.com/redir/redirect?url=https%3A%2F%2Fapify%2Ecom%2F&urlhash=kGKH&trk=about_website",
        "industries": "IT Services and IT Consulting",
        "company_size": "51-200 employees",
        "headquarters": "Praha, Hlavní město Praha",
        "type": "Privately Held",
        "founded": "2015",
        "specialties": "",
        "locations": [
            {
                "is_hq": True,
                "office_address_line_1": "Stepanska 704/61",
                "office_address_line_2": "Praha, Hlavní město Praha 11100, CZ",
                "office_location_link": "https://www.bing.com/maps?where=Stepanska+704%2F61+Praha+11100+Hlavn%C3%AD+m%C4%9Bsto+Praha+CZ&trk=org-locations_url"
            }
        ],
        "employees": [
            {
                "employee_photo": "https://media.licdn.com/dms/image/D4E03AQGVYzvGHp9zhw/profile-displayphoto-shrink_100_100/0/1688982176820?e=1700092800&v=beta&t=2jH_X4VPFBLp3r2xIZmUlp12iE32JMktOhO96_DZta8",
                "employee_name": "Jan Čurn",
                "employee_position": "CEO of Apify, a leading platform for web scraping and data for AI.",
                "employee_profile_url": "https://cz.linkedin.com/in/jancurn?trk=org-employees"
            },
            {
                "employee_photo": "https://media.licdn.com/dms/image/C4E03AQFbR0qzQd-6eA/profile-displayphoto-shrink_100_100/0/1516309144105?e=1700092800&v=beta&t=1aC4nuK7Cp910_u56-PpG2TUH0a5eu0w5WLURFL6ouQ",
                "employee_name": "Jakub Balada",
                "employee_position": "Co-founder at Apify",
                "employee_profile_url": "https://cz.linkedin.com/in/jbalada?trk=org-employees"
            }
        ],
        "updates": [
            {
                "text": "Data is the fuel for AI 🔥 And what is the largest open source of data ever created?\n\nThe web! 🌐\n\nApify gives you access to an endless pool of data from the web to power your #AI and large language models (#LLMs) such as #ChatGPT 🤖",
                "article_posted_date": "4mo",
                "total_likes": "14"
            }
        ],
        "similar_companies": [
            {
                "link": "https://ca.linkedin.com/company/apify?trk=similar-pages",
                "name": "APIfy",
                "summary": "IT Services and IT Consulting",
                "location": "Vancouver, BC"
            }
        ],
        "affiliated_companies": []
    },
    {
        "company_name": "Google",
        "universal_name_id": "google",
        "background_cover_image_url": "https://media.licdn.com/dms/image/C4D3DAQG-8Q8mIYnVQA/image-scale_191_1128/0/1519856215226?e=1695034800&v=beta&t=abc123",
        "linkedin_internal_id": "1441",
        "industry": "Computer Software",
        "location": "Mountain View, CA",
        "follower_count": "25,000,000",
        "tagline": "Our mission is to organize the world's information and make it universally accessible and useful.",
        "company_size_on_linkedin": 139995,
        "about": "Google's mission is to organize the world's information and make it universally accessible and useful.",
        "website": "https://www.google.com",
        "industries": "Computer Software",
        "company_size": "10,001+ employees",
        "headquarters": "Mountain View, CA",
        "type": "Public Company",
        "founded": "1998",
        "specialties": "search, ads, mobile, android, online video, apps, machine learning, virtual reality, cloud, hardware, artificial intelligence, youtube, and software",
        "locations": [
            {
                "is_hq": True,
                "office_address_line_1": "1600 Amphitheatre Parkway",
                "office_address_line_2": "Mountain View, CA 94043, US",
                "office_location_link": "https://www.bing.com/maps?where=1600+Amphitheatre+Parkway+Mountain+View+CA+94043+US&trk=org-locations_url"
            }
        ],
        "employees": [
            {
                "employee_photo": "https://media.licdn.com/dms/image/example1.jpg",
                "employee_name": "Sundar Pichai",
                "employee_position": "CEO of Google and Alphabet",
                "employee_profile_url": "https://www.linkedin.com/in/sundarpichai"
            }
        ],
        "updates": [
            {
                "text": "Excited to announce our latest AI breakthrough! 🤖 Our new language model is pushing the boundaries of what's possible.",
                "article_posted_date": "1w",
                "total_likes": "1,250"
            }
        ],
        "similar_companies": [
            {
                "link": "https://www.linkedin.com/company/microsoft",
                "name": "Microsoft",
                "summary": "Computer Software",
                "location": "Redmond, WA"
            }
        ],
        "affiliated_companies": [
            {
                "name": "YouTube",
                "url": "https://www.linkedin.com/company/youtube"
            }
        ]
    }
]

# Error scenarios for testing
LINKEDIN_ERROR_SCENARIOS = {
    "invalid_profile_url": {
        "input": {
            "profileUrls": ["https://invalid-url.com/profile"]
        },
        "expected_error": "Invalid LinkedIn profile URL"
    },
    "private_profile": {
        "input": {
            "profileUrls": ["https://www.linkedin.com/in/private-profile/"]
        },
        "expected_result": []  # Empty result for private profiles
    },
    "rate_limited": {
        "input": {
            "profileUrls": ["https://www.linkedin.com/in/test-profile/"]
        },
        "expected_error": "Rate limit exceeded"
    }
} 