#!/usr/bin/env python3
"""
Script to scrape Subtitle D - Miscellaneous Excise Taxes (Sections 4001 to 5000D)
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
    """Scrape Subtitle D from the IRC Code"""
    
    # Get the main TOC page
    toc_url = "https://irc.bloombergtax.com/public/uscode/toc/irc"
    
    logging.info("Fetching IRC Table of Contents...")
    response = requests.get(toc_url)
    soup = BeautifulSoup(response.content, 'lxml')
    
    # Find Subtitle D link
    subtitle_d_link = None
    for link in soup.find_all('a', href=True):
        if 'Subtitle D' in link.get_text() and 'subtitle-d' in link['href']:
            subtitle_d_link = link['href']
            break
    
    if not subtitle_d_link:
        logging.error("Could not find Subtitle D link")
        return
    
    # Make it a full URL
    if not subtitle_d_link.startswith('http'):
        subtitle_d_link = f"https://irc.bloombergtax.com{subtitle_d_link}"
    
    logging.info(f"Found Subtitle D: {subtitle_d_link}")
    
    # Create scraper and scrape the subtitle
    scraper = IRCCodeScraper()
    
    subtitle_info = {
        'title': 'Subtitle D — MISCELLANEOUS EXCISE TAXES (Sections 4001 to 5000D)',
        'url': subtitle_d_link,
        'sections': {'start': '4001', 'end': '5000D'}
    }
    
    try:
        scraper.scrape_subtitle(subtitle_d_link, subtitle_info)
        logging.info("\n" + "="*70)
        logging.info("✅ Subtitle D scraping completed successfully!")
        logging.info("="*70)
    except Exception as e:
        logging.error(f"Error during scraping: {e}", exc_info=True)

if __name__ == "__main__":
    main()
