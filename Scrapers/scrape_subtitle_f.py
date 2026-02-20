#!/usr/bin/env python3
"""Scrape Subtitle F - Procedure and Administration"""
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
    
    subtitle_f_link = None
    for link in soup.find_all('a', href=True):
        if 'Subtitle F' in link.get_text() and 'subtitle-f' in link['href']:
            subtitle_f_link = f"https://irc.bloombergtax.com{link['href']}" if not link['href'].startswith('http') else link['href']
            break
    
    if not subtitle_f_link:
        logging.error("Could not find Subtitle F link")
        return
    
    scraper = IRCCodeScraper()
    subtitle_info = {
        'title': 'Subtitle F — PROCEDURE AND ADMINISTRATION (Sections 6001 to 7874)',
        'url': subtitle_f_link,
        'sections': {'start': '6001', 'end': '7874'}
    }
    
    try:
        scraper.scrape_subtitle(subtitle_f_link, subtitle_info)
        logging.info("\n" + "="*70 + "\n✅ Subtitle F completed!\n" + "="*70)
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
