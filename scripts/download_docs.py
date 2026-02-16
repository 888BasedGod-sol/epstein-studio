#!/usr/bin/env python3
"""
Download court documents from Court Listener's RECAP archive.
Giuffre v. Maxwell (1:15-cv-07433) - Case: gov.uscourts.nysd.447706
Uses web scraping to find PDF links, then downloads from public storage.
"""

import os
import re
import time
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse

# Configuration
CASE_ID = "gov.uscourts.nysd.447706"
DOCKET_ID = 4355835
OUTPUT_DIR = Path(__file__).parent.parent / "data"
STORAGE_BASE = "https://storage.courtlistener.com"
BASE_DOCKET_URL = "https://www.courtlistener.com/docket/4355835/giuffre-v-maxwell/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def get_pdf_links_from_page(html: str) -> list:
    """Extract PDF download links from docket page HTML."""
    links = []
    
    # Look for recap storage links (absolute URLs)
    pattern = r'href="(https://storage\.courtlistener\.com/recap/[^"]+\.pdf)"'
    links.extend(re.findall(pattern, html))
    
    # Also look for relative download links
    pattern2 = r'href="(/recap/[^"]+\.pdf)"'
    relative_links = re.findall(pattern2, html)
    for link in relative_links:
        links.append(f"{STORAGE_BASE}{link}")
    
    return list(set(links))


def scrape_docket_pages() -> list:
    """Scrape all docket pages to find PDF links."""
    all_links = []
    page = 1
    max_pages = 20  # Safety limit
    
    while page <= max_pages:
        url = f"{BASE_DOCKET_URL}?page={page}"
        print(f"  Fetching page {page}...")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 404:
                break
            response.raise_for_status()
            
            links = get_pdf_links_from_page(response.text)
            if links:
                all_links.extend(links)
                print(f"    Found {len(links)} PDF links on page {page}")
            
            # Check for next page - look for page link
            next_page = f"page={page+1}"
            if next_page not in response.text:
                break
            
            page += 1
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"    Error on page {page}: {e}")
            break
    
    return list(set(all_links))


def download_pdf(pdf_url: str, output_dir: Path) -> tuple:
    """Download a single PDF document."""
    # Extract filename from URL
    parsed = urlparse(pdf_url)
    path_parts = parsed.path.split('/')
    filename = path_parts[-1] if path_parts else "unknown.pdf"
    
    # Clean up filename
    filename = filename.replace('%20', '_')
    
    output_path = output_dir / filename
    
    # Skip if already downloaded
    if output_path.exists():
        return True, f"Already exists: {filename}"
    
    try:
        response = requests.get(pdf_url, headers=HEADERS, timeout=60, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        size_mb = output_path.stat().st_size / (1024 * 1024)
        return True, f"Downloaded: {filename} ({size_mb:.1f} MB)"
    except Exception as e:
        return False, f"Failed {filename}: {e}"


def main():
    """Main download function."""
    print(f"📂 Downloading Giuffre v. Maxwell documents")
    print(f"   Output: {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Scrape docket pages for PDF links
    print("\n📋 Scraping docket pages for PDF links...")
    pdf_links = scrape_docket_pages()
    print(f"\n✅ Found {len(pdf_links)} unique PDF links")
    
    if not pdf_links:
        print("\n⚠️  No PDF links found. The documents may require PACER access.")
        print("    Try archiving pages first via free.law/RECAP extension.")
        return
    
    # Download all PDFs
    print("\n📥 Downloading PDFs...")
    success_count = 0
    fail_count = 0
    
    for i, pdf_url in enumerate(sorted(pdf_links)):
        success, msg = download_pdf(pdf_url, OUTPUT_DIR)
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        print(f"  [{i+1}/{len(pdf_links)}] {msg}")
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n🎉 Download complete!")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {fail_count}")
    print(f"   📁 Location: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
