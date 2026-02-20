#!/usr/bin/env python3
"""
Script to scrape complete Subtitle A - INCOME TAXES
Sections 1 to 1564
"""

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
    """Scrape complete Subtitle A"""
    scraper = IRCCodeScraper(output_dir='irc_data')
    
    logging.info("=" * 80)
    logging.info("Starting scrape of Subtitle A - INCOME TAXES (Sections 1 to 1564)")
    logging.info("=" * 80)
    
    try:
        # Get the main TOC to find Subtitle A
        soup = scraper._make_request(scraper.TOC_URL)
        if not soup:
            logging.error("Failed to fetch main TOC page")
            return
        
        # Extract all links and find Subtitle A
        links = scraper._extract_links_and_info(soup)
        subtitle_a_info = None
        
        for link in links:
            if 'Subtitle A' in link['title'] and 'INCOME TAXES' in link['title']:
                subtitle_a_info = link
                break
        
        if not subtitle_a_info:
            logging.error("Could not find Subtitle A in TOC")
            return
        
        logging.info(f"Found: {subtitle_a_info['title']}")
        logging.info(f"URL: {subtitle_a_info['url']}")
        
        # Scrape Subtitle A completely
        scraper.scrape_subtitle(subtitle_a_info['url'], subtitle_a_info)
        
        logging.info("=" * 80)
        logging.info("✅ Subtitle A scraping completed successfully!")
        logging.info("=" * 80)
        
    except KeyboardInterrupt:
        logging.info("\n⏸️  Scraping paused by user (Ctrl+C)")
        logging.info("Progress saved. Run this script again to resume from where you left off.")
    except Exception as e:
        logging.error(f"❌ Error during scraping: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
