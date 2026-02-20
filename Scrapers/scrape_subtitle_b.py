#!/usr/bin/env python3
"""
Script to scrape Subtitle B - Estate and Gift Taxes (Sections 2001 to 2801)
"""

import requests
from bs4 import BeautifulSoup
from Scrapers.irc_scraper import IRCCodeScraper
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('irc_scraper.log'),
        logging.StreamHandler()
    ]
)

def main():
    """Scrape Subtitle B from the IRC Code"""
    
    # Get the main TOC page
    toc_url = "https://irc.bloombergtax.com/public/uscode/toc/irc"
    
    logging.info("Fetching IRC Table of Contents...")
    response = requests.get(toc_url)
    soup = BeautifulSoup(response.content, 'lxml')
    
    # Find Subtitle B link
    subtitle_b_link = None
    for link in soup.find_all('a', href=True):
        if 'Subtitle B' in link.get_text() and 'subtitle-b' in link['href']:
            subtitle_b_link = link['href']
            break
    
    if not subtitle_b_link:
        logging.error("Could not find Subtitle B link")
        return
    
    # Make it a full URL
    if not subtitle_b_link.startswith('http'):
        subtitle_b_link = f"https://irc.bloombergtax.com{subtitle_b_link}"
    
    logging.info(f"Found Subtitle B: {subtitle_b_link}")
    
    # Create scraper and scrape the subtitle
    scraper = IRCCodeScraper()
    
    subtitle_info = {
        'title': 'Subtitle B — ESTATE AND GIFT TAXES (Sections 2001 to 2801)',
        'url': subtitle_b_link,
        'sections': {'start': '2001', 'end': '2801'}
    }
    
    try:
        scraper.scrape_subtitle(subtitle_b_link, subtitle_info)
        logging.info("\n" + "="*70)
        logging.info("✅ Subtitle B scraping completed successfully!")
        logging.info("="*70)
    except Exception as e:
        logging.error(f"Error during scraping: {e}", exc_info=True)

if __name__ == "__main__":
    main()
