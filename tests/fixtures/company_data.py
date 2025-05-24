"""
Mock data fixtures for company data actors testing.
"""

# Crunchbase Scraper Mock Data
CRUNCHBASE_INPUT = {
    "companyNames": ["TechCorp", "InnovaCorp", "StartupXYZ"],
    "includeFinancing": True,
    "includePeople": True,
    "includeNews": False
}

CRUNCHBASE_OUTPUT = [
    {
        "company": {
            "name": "TechCorp",
            "website": "https://techcorp.com",
            "description": "Leading provider of enterprise software solutions",
            "industry": "Software",
            "founded": "2010",
            "headquarters": "San Francisco, CA, USA",
            "employeeCount": "1001-5000",
            "revenue": "$100M - $500M",
            "status": "Operating"
        },
        "financing": {
            "totalFunding": 125000000,
            "lastFundingDate": "2023-03-15",
            "lastFundingAmount": 45000000,
            "lastFundingType": "Series C",
            "investors": [
                {
                    "name": "Venture Capital Partners",
                    "type": "Venture Capital",
                    "website": "https://vcpartners.com"
                },
                {
                    "name": "Tech Investors LLC",
                    "type": "Private Equity",
                    "website": "https://techinvestors.com"
                }
            ],
            "fundingRounds": [
                {
                    "date": "2023-03-15",
                    "amount": 45000000,
                    "type": "Series C",
                    "investors": ["Venture Capital Partners"]
                },
                {
                    "date": "2021-08-10",
                    "amount": 25000000,
                    "type": "Series B",
                    "investors": ["Tech Investors LLC"]
                }
            ]
        },
        "people": [
            {
                "name": "Sarah Johnson",
                "title": "CEO & Co-Founder",
                "linkedinUrl": "https://linkedin.com/in/sarah-johnson"
            },
            {
                "name": "Mike Chen",
                "title": "CTO & Co-Founder",
                "linkedinUrl": "https://linkedin.com/in/mike-chen"
            }
        ]
    },
    {
        "company": {
            "name": "InnovaCorp",
            "website": "https://innovacorp.com",
            "description": "B2B SaaS platform for enterprise clients",
            "industry": "Information Technology",
            "founded": "2015",
            "headquarters": "New York, NY, USA",
            "employeeCount": "201-500",
            "revenue": "$10M - $50M",
            "status": "Operating"
        },
        "financing": {
            "totalFunding": 35000000,
            "lastFundingDate": "2022-11-20",
            "lastFundingAmount": 15000000,
            "lastFundingType": "Series A",
            "investors": [
                {
                    "name": "Growth Capital Fund",
                    "type": "Venture Capital"
                }
            ],
            "fundingRounds": [
                {
                    "date": "2022-11-20",
                    "amount": 15000000,
                    "type": "Series A"
                }
            ]
        },
        "people": [
            {
                "name": "Jane Smith",
                "title": "CEO",
                "linkedinUrl": "https://linkedin.com/in/jane-smith-456"
            }
        ]
    }
]

# Dun & Bradstreet Scraper Mock Data
DNB_INPUT = {
    "companyNames": ["TechCorp", "InnovaCorp"],
    "includeCreditRating": True,
    "includeFinancials": True,
    "includeRiskAssessment": True
}

DNB_OUTPUT = [
    {
        "company": {
            "name": "TechCorp",
            "dunsNumber": "123456789",
            "website": "https://techcorp.com",
            "address": {
                "street": "123 Tech Street",
                "city": "San Francisco",
                "state": "CA",
                "zipCode": "94105",
                "country": "United States"
            },
            "phone": "+1-555-123-4567",
            "industry": "Computer Software Development",
            "sicCode": "7372",
            "naicsCode": "541511",
            "founded": "2010",
            "employeeCount": 2500,
            "legalStructure": "Corporation"
        },
        "creditRating": {
            "score": 85,
            "grade": "A",
            "riskLevel": "Low",
            "paymentBehavior": "Prompt",
            "lastUpdated": "2024-01-15"
        },
        "financials": {
            "annualRevenue": 250000000,
            "netIncome": 35000000,
            "totalAssets": 180000000,
            "totalLiabilities": 85000000,
            "fiscalYearEnd": "2023-12-31"
        },
        "riskAssessment": {
            "overallRisk": "Low",
            "financialRisk": "Low",
            "operationalRisk": "Medium",
            "industryRisk": "Low"
        }
    },
    {
        "company": {
            "name": "InnovaCorp",
            "dunsNumber": "987654321",
            "website": "https://innovacorp.com",
            "address": {
                "street": "456 Innovation Ave",
                "city": "New York",
                "state": "NY",
                "zipCode": "10001",
                "country": "United States"
            },
            "industry": "Software Publishing",
            "employeeCount": 350,
            "founded": "2015"
        },
        "creditRating": {
            "score": 78,
            "grade": "B+",
            "riskLevel": "Medium",
            "paymentBehavior": "Satisfactory"
        },
        "financials": {
            "annualRevenue": 25000000,
            "fiscalYearEnd": "2023-12-31"
        }
    }
]

# ZoomInfo Scraper Mock Data
ZOOMINFO_INPUT = {
    "companyNames": ["TechCorp", "InnovaCorp"],
    "includeContacts": True,
    "includeTechnologies": True,
    "includeNews": False
}

ZOOMINFO_OUTPUT = [
    {
        "company": {
            "name": "TechCorp",
            "website": "https://techcorp.com",
            "industry": "Computer Software",
            "employees": "1001-5000",
            "revenue": "$100M-$500M",
            "headquarters": "San Francisco, CA",
            "founded": "2010",
            "phone": "+1-555-123-4567"
        },
        "contacts": [
            {
                "name": "Sarah Johnson",
                "title": "Chief Executive Officer",
                "email": "sarah.johnson@techcorp.com",
                "phone": "+1-555-123-4568",
                "linkedinUrl": "https://linkedin.com/in/sarah-johnson",
                "department": "Executive"
            },
            {
                "name": "Mike Chen",
                "title": "Chief Technology Officer",
                "email": "mike.chen@techcorp.com",
                "linkedinUrl": "https://linkedin.com/in/mike-chen",
                "department": "Engineering"
            },
            {
                "name": "Jennifer Davis",
                "title": "VP of Sales",
                "email": "jennifer.davis@techcorp.com",
                "phone": "+1-555-123-4569",
                "department": "Sales"
            }
        ],
        "technologies": [
            {
                "name": "Amazon Web Services",
                "category": "Cloud Computing",
                "usage": "Infrastructure"
            },
            {
                "name": "React",
                "category": "JavaScript Framework",
                "usage": "Frontend Development"
            },
            {
                "name": "PostgreSQL",
                "category": "Database",
                "usage": "Data Storage"
            }
        ]
    },
    {
        "company": {
            "name": "InnovaCorp",
            "website": "https://innovacorp.com",
            "industry": "Information Technology",
            "employees": "201-500",
            "revenue": "$10M-$50M",
            "headquarters": "New York, NY"
        },
        "contacts": [
            {
                "name": "Jane Smith",
                "title": "CEO",
                "email": "jane.smith@innovacorp.com",
                "linkedinUrl": "https://linkedin.com/in/jane-smith-456"
            }
        ],
        "technologies": [
            {
                "name": "Microsoft Azure",
                "category": "Cloud Computing"
            },
            {
                "name": "Node.js",
                "category": "Runtime Environment"
            }
        ]
    }
]

# Erasmus+ Organisation Scraper Mock Data
ERASMUS_INPUT = {
    "organisationNames": ["University of Technology", "European Research Institute"],
    "includeProjects": True,
    "includePartners": True,
    "country": "Netherlands"
}

ERASMUS_OUTPUT = [
    {
        "organisation": {
            "name": "University of Technology",
            "type": "Higher Education Institution",
            "country": "Netherlands",
            "city": "Amsterdam",
            "website": "https://utech.nl",
            "erasmusCode": "NL AMSTERD01",
            "pic": "999123456789"
        },
        "projects": [
            {
                "title": "Digital Innovation in Education",
                "projectNumber": "2023-1-NL01-KA220-HED-000123456",
                "programme": "Erasmus+",
                "action": "Cooperation partnerships in higher education",
                "startDate": "2023-09-01",
                "endDate": "2026-08-31",
                "budget": 400000,
                "role": "Coordinator"
            },
            {
                "title": "Sustainable Technology Transfer",
                "projectNumber": "2022-1-DE02-KA220-HED-000654321",
                "programme": "Erasmus+",
                "action": "Cooperation partnerships in higher education",
                "startDate": "2022-09-01",
                "endDate": "2025-08-31",
                "budget": 350000,
                "role": "Partner"
            }
        ],
        "partners": [
            {
                "name": "Technical University Munich",
                "country": "Germany",
                "type": "Higher Education Institution"
            },
            {
                "name": "École Polytechnique",
                "country": "France",
                "type": "Higher Education Institution"
            }
        ]
    },
    {
        "organisation": {
            "name": "European Research Institute",
            "type": "Research Organisation",
            "country": "Netherlands",
            "city": "The Hague",
            "website": "https://eri.eu",
            "pic": "999987654321"
        },
        "projects": [
            {
                "title": "Climate Change Research Network",
                "projectNumber": "2023-1-NL01-KA220-ADU-000789012",
                "programme": "Erasmus+",
                "action": "Cooperation partnerships in adult education",
                "startDate": "2023-10-01",
                "endDate": "2026-09-30",
                "budget": 300000,
                "role": "Coordinator"
            }
        ],
        "partners": []
    }
]

# Company Data Error Scenarios
COMPANY_DATA_ERROR_SCENARIOS = {
    "company_not_found": {
        "input": {
            "companyNames": ["NonExistentCompany123"]
        },
        "expected_error": "Company not found"
    },
    "invalid_company_name": {
        "input": {
            "companyNames": [""]
        },
        "expected_error": "Invalid company name"
    },
    "access_denied": {
        "input": {
            "companyNames": ["PrivateCompany"]
        },
        "expected_error": "Access denied"
    },
    "rate_limited": {
        "input": {
            "companyNames": ["TestCompany"]
        },
        "expected_error": "Rate limit exceeded"
    }
} 