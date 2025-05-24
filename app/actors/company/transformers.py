"""
Data transformers for company data actors.

Contains functions for transforming raw actor responses into standardized CompanyData formats.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.data import CompanyData, CompanyFinancialData, CompanyEmployeeData


def transform_crunchbase_data(raw_data: Dict[str, Any]) -> CompanyData:
    """
    Transform raw Crunchbase data to standardized format.
    
    Args:
        raw_data: Raw data from Crunchbase Scraper actor.
        
    Returns:
        Standardized company data.
    """
    # Extract basic company information
    company_name = raw_data.get("name", "Unknown Company")
    website = raw_data.get("website")
    
    # Extract industry information
    industry_info = {}
    if raw_data.get("industry"):
        industry_info["primary"] = raw_data["industry"]
    if raw_data.get("categories"):
        industry_info["categories"] = raw_data["categories"]
    if raw_data.get("industries"):
        industry_info["industries"] = raw_data["industries"]
    
    # Extract funding information
    funding_info = {}
    if raw_data.get("totalFunding"):
        funding_info["total_funding"] = raw_data["totalFunding"]
    if raw_data.get("lastFundingAmount"):
        funding_info["last_funding_amount"] = raw_data["lastFundingAmount"]
    if raw_data.get("lastFundingDate"):
        funding_info["last_funding_date"] = raw_data["lastFundingDate"]
    if raw_data.get("fundingRounds"):
        funding_info["funding_rounds"] = raw_data["fundingRounds"]
    if raw_data.get("valuation"):
        funding_info["valuation"] = raw_data["valuation"]
    
    # Extract investor information
    if raw_data.get("investors"):
        funding_info["investors"] = raw_data["investors"]
    
    # Extract financial data
    financial_data = None
    if raw_data.get("revenue") or raw_data.get("valuation") or funding_info:
        financial_data = CompanyFinancialData(
            revenue=raw_data.get("revenue"),
            valuation=str(raw_data.get("valuation", "")) if raw_data.get("valuation") else None,
            funding=str(funding_info.get("total_funding", "")) if funding_info.get("total_funding") else None,
            funding_rounds=funding_info.get("funding_rounds", []),
            key_investors=funding_info.get("investors", []),
        )
    
    # Extract employee data
    employee_data = None
    if raw_data.get("employeeCount") or raw_data.get("employeeRange"):
        employee_count = None
        if raw_data.get("employeeCount"):
            try:
                employee_count = int(raw_data["employeeCount"])
            except (ValueError, TypeError):
                pass
        
        employee_data = CompanyEmployeeData(
            employee_count=employee_count,
            locations=raw_data.get("locations", []),
            executives=raw_data.get("executives", []),
        )
    
    # Extract news and other information
    news = raw_data.get("news", [])
    competitors = raw_data.get("competitors", [])
    
    return CompanyData(
        name=company_name,
        website=website,
        financial=financial_data,
        funding=funding_info,
        industry=industry_info,
        employees=employee_data,
        competitors=competitors,
        news=news,
        sources=["crunchbase"],
    )


def transform_duns_data(raw_data: Dict[str, Any]) -> CompanyData:
    """
    Transform raw Dun & Bradstreet data to standardized format.
    
    Args:
        raw_data: Raw data from Dun & Bradstreet Scraper actor.
        
    Returns:
        Standardized company data.
    """
    # Extract basic company information
    company_name = raw_data.get("name", "Unknown Company")
    website = raw_data.get("website")
    
    # Extract industry information
    industry_info = {}
    if raw_data.get("primaryIndustry"):
        industry_info["primary"] = raw_data["primaryIndustry"]
    if raw_data.get("sicCode"):
        industry_info["sic_code"] = raw_data["sicCode"]
    if raw_data.get("naicsCode"):
        industry_info["naics_code"] = raw_data["naicsCode"]
    if raw_data.get("industryDescription"):
        industry_info["description"] = raw_data["industryDescription"]
    
    # Extract financial data
    financial_data = None
    financial_info = raw_data.get("financials", {})
    if financial_info or raw_data.get("annualRevenue"):
        financial_data = CompanyFinancialData(
            revenue=raw_data.get("annualRevenue") or financial_info.get("revenue"),
            funding=financial_info.get("totalDebt"),
        )
    
    # Extract employee data
    employee_data = None
    if raw_data.get("employeeCount") or raw_data.get("employeeRange"):
        employee_count = None
        if raw_data.get("employeeCount"):
            try:
                employee_count = int(raw_data["employeeCount"])
            except (ValueError, TypeError):
                pass
        
        employee_data = CompanyEmployeeData(
            employee_count=employee_count,
            locations=raw_data.get("locations", []),
            executives=raw_data.get("keyPersonnel", []),
        )
    
    # Extract risk and credit information
    funding_info = {}
    if raw_data.get("creditRating"):
        funding_info["credit_rating"] = raw_data["creditRating"]
    if raw_data.get("riskScore"):
        funding_info["risk_score"] = raw_data["riskScore"]
    if raw_data.get("paymentBehavior"):
        funding_info["payment_behavior"] = raw_data["paymentBehavior"]
    
    return CompanyData(
        name=company_name,
        website=website,
        financial=financial_data,
        funding=funding_info,
        industry=industry_info,
        employees=employee_data,
        sources=["duns"],
    )


def transform_zoominfo_data(raw_data: Dict[str, Any]) -> CompanyData:
    """
    Transform raw ZoomInfo data to standardized format.
    
    Args:
        raw_data: Raw data from ZoomInfo Scraper actor.
        
    Returns:
        Standardized company data.
    """
    # Extract basic company information - ZoomInfo returns flat structure
    company_name = raw_data.get("name") or raw_data.get("full_name", "Unknown Company")
    website = raw_data.get("website")
    if website and website.startswith("//"):
        website = "https:" + website
    
    # Extract industry information
    industry_info = {}
    if raw_data.get("industries"):
        industry_info["industries"] = raw_data["industries"]
        if isinstance(raw_data["industries"], list) and raw_data["industries"]:
            industry_info["primary"] = raw_data["industries"][0]
    
    # Extract financial data
    financial_data = None
    revenue = raw_data.get("revenue")
    revenue_text = raw_data.get("revenue_text")
    if revenue or revenue_text:
        financial_data = CompanyFinancialData(
            revenue=revenue_text or revenue,
        )
    
    # Extract funding information
    funding_info = {}
    fundings = raw_data.get("fundings", {})
    if fundings:
        funding_data = fundings.get("data", [])
        funding_totals = fundings.get("totals", {})
        
        if funding_totals:
            funding_info["total_funding"] = funding_totals.get("total_amount")
            funding_info["last_funding_amount"] = funding_totals.get("last_funding_amount")
            funding_info["funding_rounds_count"] = funding_totals.get("num_of_rounds")
        
        if funding_data:
            funding_info["funding_rounds"] = funding_data
    
    # Extract employee data
    employee_data = None
    employee_count = raw_data.get("number_of_employees")
    address = raw_data.get("address")
    
    if employee_count or address:
        try:
            emp_count = int(employee_count) if employee_count else None
        except (ValueError, TypeError):
            emp_count = None
            
        locations = []
        if address:
            locations.append(address)
        
        employee_data = CompanyEmployeeData(
            employee_count=emp_count,
            locations=locations,
        )
    
    # Extract similar companies
    competitors = []
    similar_companies = raw_data.get("similar_company_urls", [])
    if similar_companies:
        for similar in similar_companies:
            if isinstance(similar, dict):
                competitors.append({
                    "name": similar.get("name"),
                    "employees": similar.get("employees"),
                    "revenue": similar.get("revenue"),
                    "logo": similar.get("logo"),
                    "zoominfo_url": f"https://www.zoominfo.com{similar.get('company_page_link', '')}"
                })
    
    # Extract additional data for CompanyData
    additional_data = {
        "zoominfo_id": raw_data.get("id"),
        "description": raw_data.get("description"),
        "founding_year": raw_data.get("founding_year"),
        "stock_symbol": raw_data.get("stock_symbol"),
        "phone_number": raw_data.get("phone_number"),
        "fax": raw_data.get("fax"),
        "social_networks": raw_data.get("social_network_urls", []),
        "source_url": raw_data.get("url"),
        "from_input": raw_data.get("from_url_or_company_name")
    }
    
    return CompanyData(
        name=company_name,
        website=website,
        financial=financial_data,
        funding=funding_info,
        industry=industry_info,
        employees=employee_data,
        competitors=competitors,
        sources=["zoominfo"],
        additional_data=additional_data,
    )


def transform_erasmus_data(raw_data: Dict[str, Any]) -> CompanyData:
    """
    Transform raw Erasmus+ data to standardized format.
    
    Args:
        raw_data: Raw data from Erasmus+ Organisation Scraper actor.
        
    Returns:
        Standardized company data.
    """
    # Extract basic organization information
    organization_name = raw_data.get("name", "Unknown Organization")
    website = raw_data.get("website")
    
    # Extract industry/sector information
    industry_info = {}
    if raw_data.get("sector"):
        industry_info["sector"] = raw_data["sector"]
    if raw_data.get("type"):
        industry_info["organization_type"] = raw_data["type"]
    if raw_data.get("legalStatus"):
        industry_info["legal_status"] = raw_data["legalStatus"]
    
    # Extract location information
    locations = []
    if raw_data.get("address"):
        locations.append(str(raw_data["address"]))
    if raw_data.get("country"):
        country_str = str(raw_data["country"])
        # Check if country is not already in locations
        if country_str not in locations:
            locations.append(country_str)
    
    # Extract employee/organization data
    employee_data = None
    if raw_data.get("size") or locations:
        employee_data = CompanyEmployeeData(
            locations=locations,
        )
    
    # Extract funding/project information
    funding_info = {}
    if raw_data.get("projects"):
        funding_info["erasmus_projects"] = raw_data["projects"]
    if raw_data.get("grants"):
        funding_info["grants"] = raw_data["grants"]
    if raw_data.get("partnerships"):
        funding_info["partnerships"] = raw_data["partnerships"]
    
    # Extract contact information
    contacts = []
    if raw_data.get("contactPerson"):
        contacts.append(raw_data["contactPerson"])
    if raw_data.get("email"):
        contacts.append({"email": raw_data["email"]})
    if raw_data.get("phone"):
        contacts.append({"phone": raw_data["phone"]})
    
    return CompanyData(
        name=organization_name,
        website=website,
        funding=funding_info,
        industry=industry_info,
        employees=employee_data,
        sources=["erasmus"],
    ) 