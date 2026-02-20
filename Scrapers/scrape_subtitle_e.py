#!/usr/bin/env python3
"""Scrape Subtitle E - Alcohol, Tobacco, and Certain Other Excise Taxes"""
import requests
from bs4 import BeautifulSoup
from Scrapers.irc_scraper import IRCCodeScraper
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('irc_scraper.log'), logging.StreamHandler()])

def main():
    toc_url = "https://irc.bloombergtax.com/public/uscode/toc/irc"
    response = requests.get(toc_url)
    soup = BeautifulSoup(response.content, 'lxml')
    
    subtitle_e_link = None
    for link in soup.find_all('a', href=True):
        if 'Subtitle E' in link.get_text() and 'subtitle-e' in link['href']:
            subtitle_e_link = f"https://irc.bloombergtax.com{link['href']}" if not link['href'].startswith('http') else link['href']
            break
    
    if not subtitle_e_link:
        logging.error("Could not find Subtitle E link")
        return
    
    scraper = IRCCodeScraper()
    subtitle_info = {
        'title': 'Subtitle E — ALCOHOL, TOBACCO, AND CERTAIN OTHER EXCISE TAXES (Sections 5001 to 5891)',
        'url': subtitle_e_link,
        'sections': {'start': '5001', 'end': '5891'}
    }
    
    try:
        scraper.scrape_subtitle(subtitle_e_link, subtitle_info)
        logging.info("\n" + "="*70 + "\n✅ Subtitle E completed!\n" + "="*70)
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
