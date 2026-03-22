"""
Exit Load Scraper Service

Scrapes exit load data from Groww mutual fund pages.
"""

import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone, timedelta


def get_ist_timestamp() -> str:
    """Get current timestamp in IST (Indian Standard Time, UTC+5:30)"""
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_timezone).replace(tzinfo=None).isoformat()


class ExitLoadScraper:
    """Scrapes exit load information from mutual fund scheme pages"""
    
    # URLs for mutual fund schemes
    FUND_URLS = {
        "Axis Flexi Cap Fund": "https://groww.in/mutual-funds/axis-flexi-cap-fund-direct-growth",
        "Nippon India Large Cap Fund": "https://groww.in/mutual-funds/nippon-india-large-cap-fund-direct-growth",
        "ICICI Prudential Indo Asia Equity Fund": "https://groww.in/mutual-funds/icici-prudential-indo-asia-equity-fund-direct-growth"
    }
    
    # Static source for exit load definition
    DEFINITION_SOURCE = {
        "name": "Mirae Asset - Exit Load Guide",
        "url": "https://www.miraeassetmf.co.in/knowledge-center/exit-load-in-mutual-funds",
        "description": "Exit load is a fee charged when units are redeemed before a specified holding period"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def scrape_all_funds(self) -> Dict:
        """
        Scrape exit load data from all configured mutual fund pages
        
        Returns:
            Dictionary containing scraped data from all funds
        """
        results = {
            "funds": [],
            "sources": [],
            "scraped_at": get_ist_timestamp()
        }
        
        # Add definition source (static, not scraped)
        results["sources"].append(self.DEFINITION_SOURCE)
        
        for fund_name, url in self.FUND_URLS.items():
            try:
                fund_data = self._scrape_fund_page(fund_name, url)
                if fund_data:
                    results["funds"].append(fund_data)
                    results["sources"].append({
                        "name": fund_name,
                        "url": url
                    })
            except Exception as e:
                print(f"Error scraping {fund_name}: {e}")
                # Continue with other funds even if one fails
                continue
        
        return results
    
    def _scrape_fund_page(self, fund_name: str, url: str) -> Optional[Dict]:
        """
        Scrape exit load data from a single fund page
        
        Args:
            fund_name: Name of the mutual fund
            url: URL of the fund page
            
        Returns:
            Dictionary containing fund data or None if scraping fails
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract exit load information
            exit_load_content = self._extract_exit_load(soup)
            
            # Extract fund basic info
            fund_info = self._extract_fund_info(soup, fund_name)
            
            return {
                "fund_name": fund_name,
                "url": url,
                "exit_load": exit_load_content,
                "fund_info": fund_info
            }
            
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def _extract_exit_load(self, soup: BeautifulSoup) -> str:
        """
        Extract exit load content from the page
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            String containing exit load content
        """
        exit_load_content = ""
        
        try:
            # Pattern 1: Look for the specific exit load section heading "### Exit Load"
            exit_load_section = soup.find('h3', string=re.compile(r'exit\s*load', re.IGNORECASE))
            
            if exit_load_section:
                # Get the next sibling elements which contain the actual exit load details
                next_elem = exit_load_section.find_next_sibling()
                if next_elem:
                    # Look for divs or paragraphs containing exit load details
                    exit_load_details = []
                    current = next_elem
                    
                    # Collect up to 3 elements or until we hit another heading
                    for _ in range(5):
                        if not current:
                            break
                        text = current.get_text(strip=True)
                        if text and len(text) > 20:  # Filter out short/empty texts
                            exit_load_details.append(text)
                        current = current.find_next_sibling()
                    
                    if exit_load_details:
                        exit_load_content = " ".join(exit_load_details)
            
            # Pattern 2: Look for specific exit load patterns in the page
            if not exit_load_content:
                page_text = soup.get_text()
                
                # Look for specific exit load patterns
                patterns = [
                    # Pattern: "Exit Load for units in excess of X%, Y% will be charged for redemption within Z months"
                    r'Exit\s*Load\s*for\s*units[^.]*\d+%[^.]*\d+%[^.]*(?:months?|years?)[^.]*\.',
                    # Pattern: "Exit load of X% if redeemed within Y months"
                    r'Exit\s*load\s*of\s*\d+%[^.]*if\s*redeemed[^.]*(?:months?|years?)[^.]*\.',
                    # Pattern: General exit load with percentage and period
                    r'Exit\s*[Ll]oad[^.]*\d+%[^.]*(?:months?|years?)[^.]{0,100}\.',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        exit_load_content = match.group(0).strip()
                        break
            
            # Pattern 3: Look for exit load in specific divs/sections
            if not exit_load_content:
                # Look for elements containing "Exit Load" and percentage
                exit_load_elems = soup.find_all(string=re.compile(r'Exit\s*[Ll]oad.*\d+%', re.IGNORECASE))
                for elem in exit_load_elems:
                    text = elem.strip()
                    if len(text) > 30 and len(text) < 300:  # Reasonable length for exit load description
                        exit_load_content = text
                        break
            
        except Exception as e:
            print(f"Error extracting exit load: {e}")
        
        return exit_load_content
    
    def _extract_fund_info(self, soup: BeautifulSoup, fund_name: str) -> Dict:
        """
        Extract basic fund information
        
        Args:
            soup: BeautifulSoup object of the page
            fund_name: Name of the fund
            
        Returns:
            Dictionary containing fund information
        """
        fund_info = {
            "name": fund_name,
            "category": None,
            "amc": None
        }
        
        try:
            # Try to extract AMC name from fund name
            amc_patterns = [
                r'^([A-Za-z\s]+)\s+(Flexi|Large|Mid|Small|Multi|Balanced|Debt|Equity)',
                r'^([A-Za-z\s]+)\s+India',
                r'^([A-Za-z\s]+)\s+Prudential'
            ]
            
            for pattern in amc_patterns:
                match = re.match(pattern, fund_name)
                if match:
                    fund_info["amc"] = match.group(1).strip()
                    break
            
            # Try to find category from page
            category_elem = soup.find(string=re.compile(r'fund\s*category', re.IGNORECASE))
            if category_elem:
                parent = category_elem.find_parent(['div', 'span', 'td'])
                if parent:
                    # Get next sibling or parent's text
                    category_text = parent.get_text(strip=True)
                    fund_info["category"] = category_text.replace('Fund Category', '').strip()
            
        except Exception as e:
            print(f"Error extracting fund info: {e}")
        
        return fund_info
    
    def get_static_exit_load_definition(self) -> Dict:
        """
        Get static exit load definition (not scraped)
        
        Returns:
            Dictionary with exit load definition
        """
        return {
            "definition": "Exit load is a fee charged when units are redeemed before a specified holding period — typically 1% if redeemed within 1 year.",
            "source": self.DEFINITION_SOURCE
        }
