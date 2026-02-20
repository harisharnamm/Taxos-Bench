#!/usr/bin/env python3
"""Scrape remaining subtitles G-K (smaller subtitles in one script)"""
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
    
    subtitles = [
        ('G', 'THE JOINT COMMITTEE ON TAXATION', '8001', '8023'),
        ('H', 'FINANCING OF PRESIDENTIAL ELECTION CAMPAIGNS', '9001', '9042'),
        ('I', 'TRUST FUND CODE', '9500', '9602'),
        ('J', 'COAL INDUSTRY HEALTH BENEFITS', '9701', '9722'),
        ('K', 'GROUP HEALTH PLAN REQUIREMENTS', '9801', '9834'),
    ]
    
    scraper = IRCCodeScraper()
    
    for letter, title, start, end in subtitles:
        subtitle_link = None
        for link in soup.find_all('a', href=True):
            if f'Subtitle {letter}' in link.get_text() and f'subtitle-{letter.lower()}' in link['href']:
                subtitle_link = f"https://irc.bloombergtax.com{link['href']}" if not link['href'].startswith('http') else link['href']
                break
        
        if not subtitle_link:
            logging.error(f"Could not find Subtitle {letter} link")
            continue
        
        subtitle_info = {
            'title': f'Subtitle {letter} — {title} (Sections {start} to {end})',
            'url': subtitle_link,
            'sections': {'start': start, 'end': end}
        }
        
        try:
            scraper.scrape_subtitle(subtitle_link, subtitle_info)
            logging.info(f"\n{'='*70}\n✅ Subtitle {letter} completed!\n{'='*70}")
        except Exception as e:
            logging.error(f"Error scraping Subtitle {letter}: {e}", exc_info=True)
    
    logging.info("\n" + "="*70 + "\n✅ All subtitles G-K completed!\n" + "="*70)

if __name__ == "__main__":
    main()
