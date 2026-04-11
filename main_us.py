#!/usr/bin/env python3
"""
MarketBeat Morgan Stanley Stock Recommendations Scraper
Extracts company data and exports to Excel
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re


def fetch_page(url):
    """Fetch the webpage content"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"✓ Successfully fetched page (Status: {response.status_code})")
        
        # Save HTML for debugging
        with open('marketbeat_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("✓ Saved HTML to marketbeat_page.html for inspection")
        
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching page: {e}")
        return None


def parse_marketbeat_table(html):
    """Parse the MarketBeat ratings table"""
    soup = BeautifulSoup(html, 'lxml')
    
    # Find the ratings table
    table = soup.find('table', {'class': 'scroll-table'}) or soup.find('table')
    
    if not table:
        print("✗ Could not find ratings table")
        return None
    
    print("✓ Found ratings table")
    
    # Extract headers
    headers = []
    header_row = table.find('thead') or table.find('tr')
    if header_row:
        for th in header_row.find_all(['th', 'td']):
            headers.append(th.get_text(strip=True))
    
    print(f"✓ Found headers: {headers}")
    
    # Map column names to indices (flexible matching)
    col_map = {}
    for i, header in enumerate(headers):
        header_lower = header.lower()
        if 'company' in header_lower or 'stock' in header_lower or 'ticker' in header_lower:
            col_map['company'] = i
        elif 'current' in header_lower and 'price' in header_lower:
            col_map['current_price'] = i
        elif 'date' in header_lower:
            col_map['date'] = i
        elif 'rating' in header_lower or 'action' in header_lower:
            col_map['rating'] = i
        elif 'price target' in header_lower or 'target' in header_lower:
            col_map['price_target'] = i
        elif 'analyst' in header_lower or 'firm' in header_lower:
            col_map['analyst'] = i
    
    print(f"✓ Mapped columns: {col_map}")
    
    # Extract data rows
    data = []
    tbody = table.find('tbody') or table
    rows = tbody.find_all('tr')
    
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) < 3:  # Skip header or empty rows
            continue
        
        row_data = {}
        
        # Extract company name
        if 'company' in col_map:
            company_cell = cells[col_map['company']]
            # Try to get the link text first, or cell text
            company_link = company_cell.find('a')
            row_data['Company Name'] = company_link.get_text(strip=True) if company_link else company_cell.get_text(strip=True)
        else:
            row_data['Company Name'] = cells[0].get_text(strip=True)
        
        # Extract current price
        if 'current_price' in col_map:
            price_text = cells[col_map['current_price']].get_text(strip=True)
            row_data['Current Price'] = price_text
        else:
            row_data['Current Price'] = ''
        
        # Extract report date
        if 'date' in col_map:
            date_text = cells[col_map['date']].get_text(strip=True)
            row_data['Report Date'] = date_text
        else:
            row_data['Report Date'] = ''
        
        # Extract rating
        if 'rating' in col_map:
            rating_text = cells[col_map['rating']].get_text(strip=True)
            row_data['Rating'] = rating_text
        else:
            row_data['Rating'] = ''
        
        # Extract price target
        if 'price_target' in col_map:
            target_text = cells[col_map['price_target']].get_text(strip=True)
            row_data['Price Target'] = target_text
        else:
            row_data['Price Target'] = ''
        
        # Extract analyst (should be Morgan Stanley for all)
        if 'analyst' in col_map:
            analyst_text = cells[col_map['analyst']].get_text(strip=True)
            row_data['Analyst Name'] = analyst_text
        else:
            row_data['Analyst Name'] = 'Morgan Stanley'
        
        # Only add row if it has a company name
        if row_data['Company Name']:
            data.append(row_data)
    
    print(f"✓ Extracted {len(data)} rows of data")
    return data


def save_to_excel(data, filename='morgan_stanley_ratings.xlsx'):
    """Save data to Excel file"""
    if not data:
        print("✗ No data to save")
        return None
    
    df = pd.DataFrame(data)
    
    # Ensure column order
    columns = ['Company Name', 'Current Price', 'Report Date', 'Rating', 'Price Target', 'Analyst Name']
    df = df.reindex(columns=columns, fill_value='')
    
    # Save to Excel
    df.to_excel(filename, index=False, engine='openpyxl')
    print(f"✓ Saved {len(df)} records to {filename}")
    
    # Print preview
    print("\nPreview of data:")
    print(df.head(10).to_string())
    
    return filename


def main():
    """Main execution function"""
    print("=" * 60)
    print("MarketBeat Morgan Stanley Stock Recommendations Scraper")
    print("=" * 60)
    
    url = "https://www.marketbeat.com/ratings/by-issuer/morgan-stanley-stock-recommendations/"
    
    # Step 1: Fetch the page
    print("\n[1/3] Fetching webpage...")
    html = fetch_page(url)
    
    if not html:
        print("\n✗ Failed to fetch page. Please check your internet connection.")
        return
    
    # Step 2: Parse the table
    print("\n[2/3] Parsing data...")
    data = parse_marketbeat_table(html)
    
    if not data:
        print("\n✗ No data extracted. The website structure may have changed.")
        print("   Check marketbeat_page.html to inspect the page structure.")
        return
    
    # Step 3: Save to Excel
    print("\n[3/3] Saving to Excel...")
    output_file = save_to_excel(data)
    
    if output_file:
        print("\n" + "=" * 60)
        print(f"✓ SUCCESS! Data exported to: {output_file}")
        print("=" * 60)
    else:
        print("\n✗ Failed to save Excel file.")


if __name__ == "__main__":
    main()
