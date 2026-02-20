#!/usr/bin/env python3
"""
Script to scrape Subtitle C - Employment Taxes (Sections 3101 to 3512)
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
    """Scrape Subtitle C from the IRC Code"""
    
    # Get the main TOC page
    toc_url = "https://irc.bloombergtax.com/public/uscode/toc/irc"
    
    logging.info("Fetching IRC Table of Contents...")
    response = requests.get(toc_url)
    soup = BeautifulSoup(response.content, 'lxml')
    
    # Find Subtitle C link
    subtitle_c_link = None
    for link in soup.find_all('a', href=True):
        if 'Subtitle C' in link.get_text() and 'subtitle-c' in link['href']:
            subtitle_c_link = link['href']
            break
    
    if not subtitle_c_link:
        logging.error("Could not find Subtitle C link")
        return
    
    # Make it a full URL
    if not subtitle_c_link.startswith('http'):
        subtitle_c_link = f"https://irc.bloombergtax.com{subtitle_c_link}"
    
    logging.info(f"Found Subtitle C: {subtitle_c_link}")
    
    # Create scraper and scrape the subtitle
    scraper = IRCCodeScraper()
    
    subtitle_info = {
        'title': 'Subtitle C — EMPLOYMENT TAXES (Sections 3101 to 3512)',
        'url': subtitle_c_link,
        'sections': {'start': '3101', 'end': '3512'}
    }
    
    try:
        scraper.scrape_subtitle(subtitle_c_link, subtitle_info)
        logging.info("\n" + "="*70)
        logging.info("✅ Subtitle C scraping completed successfully!")
        logging.info("="*70)
    except Exception as e:
        logging.error(f"Error during scraping: {e}", exc_info=True)

if __name__ == "__main__":
    main()
