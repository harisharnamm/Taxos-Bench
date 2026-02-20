"""
IRC Code Scraper for Bloomberg Tax
Scrapes the complete Internal Revenue Code from Bloomberg Tax public website
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin
import logging
from typing import Dict, List, Optional
import os
from datetime import datetime
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('irc_scraper.log'),
        logging.StreamHandler()
    ]
)

class IRCCodeScraper:
    """Scraper for the Internal Revenue Code from Bloomberg Tax"""
    
    BASE_URL = "https://irc.bloombergtax.com"
    TOC_URL = "https://irc.bloombergtax.com/public/uscode/toc/irc"
    
    def __init__(self, output_dir: str = "irc_data"):
        """
        Initialize the IRC Code Scraper
        
        Args:
            output_dir: Directory to save scraped data
        """
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.data = {
            'metadata': {
                'scrape_date': datetime.now().isoformat(),
                'source_url': self.TOC_URL
            },
            'subtitles': []
        }
        
        # Create output directory structure
        os.makedirs(output_dir, exist_ok=True)
        
        # Progress tracking for resume functionality
        self.progress_file = os.path.join(output_dir, 'scraper_progress.json')
        self.completed_sections = set()
        self.should_pause = False
        
        # Load existing progress if resuming
        self._load_progress()
        
        # Rate limiting
        self.delay = 1  # seconds between requests
    
    def _load_progress(self):
        """Load progress from previous scraping session"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    self.completed_sections = set(progress.get('completed_sections', []))
                    logging.info(f"Resumed: {len(self.completed_sections)} sections already completed")
            except Exception as e:
                logging.warning(f"Could not load progress file: {e}")
    
    def _save_progress_state(self):
        """Save current progress state"""
        progress = {
            'last_updated': datetime.now().isoformat(),
            'completed_sections': list(self.completed_sections),
            'total_completed': len(self.completed_sections)
        }
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2)
    
    def _check_if_completed(self, section_url: str) -> bool:
        """Check if a section has already been scraped"""
        return section_url in self.completed_sections
    
    def _mark_completed(self, section_url: str):
        """Mark a section as completed"""
        self.completed_sections.add(section_url)
        self._save_progress_state()
    
    def request_pause(self):
        """Request graceful pause of scraping"""
        self.should_pause = True
        logging.info("Pause requested - will stop after current section completes")
    
    def _make_request(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Make HTTP request with retry logic
        
        Args:
            url: URL to fetch
            retries: Number of retry attempts
            
        Returns:
            BeautifulSoup object or None if failed
        """
        for attempt in range(retries):
            try:
                time.sleep(self.delay)  # Rate limiting
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    logging.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        return None
    
    def _extract_sections_range(self, text: str) -> Optional[Dict[str, int]]:
        """
        Extract section range from text like '(Sections 1 to 1564)'
        
        Args:
            text: Text containing section range
            
        Returns:
            Dictionary with start and end sections
        """
        match = re.search(r'\(Sections?\s+(\d+[A-Z]?)\s+to\s+(\d+[A-Z]?)\)', text)
        if match:
            return {'start': match.group(1), 'end': match.group(2)}
        
        # Single section
        match = re.search(r'\(Section\s+(\d+[A-Z]?)\)', text)
        if match:
            return {'start': match.group(1), 'end': match.group(1)}
        
        return None
    
    def _extract_links_and_info(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract links and information from a TOC page
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of dictionaries containing link info
        """
        items = []
        
        # Find all links that are likely hierarchical elements
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Skip empty, very short, or irrelevant links
            if not text or len(text) < 5:
                continue
            
            # Skip navigation/footer links
            if any(skip in text for skip in ['Bloomberg', 'Log In', 'About Us', 'Contact', 
                                               'Copyright', 'Terms', 'Privacy', 'Request']):
                continue
            
            # Skip external links and non-IRC links
            if href.startswith('http') and 'bloombergtax.com' not in href:
                continue
            
            # Only include IRC hierarchy links (subtitle, chapter, subchapter, part, section)
            is_irc_link = (
                '/public/uscode/' in href and (
                    'subtitle-' in href or 
                    'chapter-' in href or 
                    'subchapter-' in href or 
                    'part-' in href or 
                    'section_' in href
                )
            )
            
            if not is_irc_link:
                continue
            
            # Build full URL
            full_url = urljoin(self.BASE_URL, href) if not href.startswith('http') else href
            
            # Extract section range if present
            sections = self._extract_sections_range(text)
            
            items.append({
                'title': text,
                'url': full_url,
                'sections': sections
            })
        
        return items
    
    def _parse_section_content(self, soup: BeautifulSoup, section_number: str) -> Dict:
        """
        Parse the actual content of an IRC section
        
        Args:
            soup: BeautifulSoup object of the section page
            section_number: Section number (e.g., '1', '401')
            
        Returns:
            Dictionary containing section content
        """
        from irc_parser import IRCSectionParser
        
        # Use the enhanced parser
        parser = IRCSectionParser()
        content = parser.parse_section_detailed(soup, section_number)
        
        return content
    
    def _save_section_file(self, content: Dict, subtitle_name: str, chapter_name: str, section_number: str):
        """
        Save individual section to organized folder structure
        
        Args:
            content: Section content dictionary
            subtitle_name: Name of subtitle (e.g., 'Subtitle_A')
            chapter_name: Name of chapter (e.g., 'Chapter_1')
            section_number: Section number (e.g., '1', '401')
        """
        # Clean names for folder/file naming
        subtitle_clean = re.sub(r'[^\w\s-]', '', subtitle_name).strip().replace(' ', '_')[:50]
        chapter_clean = re.sub(r'[^\w\s-]', '', chapter_name).strip().replace(' ', '_')[:50]
        
        # Create folder structure: irc_data/Subtitle_A/Chapter_1/
        chapter_dir = os.path.join(self.output_dir, subtitle_clean, chapter_clean)
        os.makedirs(chapter_dir, exist_ok=True)
        
        # Save section file
        filename = f"section_{section_number}.json"
        filepath = os.path.join(chapter_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Saved: {filepath}")
    
    def _save_chapter_summary(self, chapter_data: Dict, subtitle_name: str, chapter_name: str):
        """
        Save chapter summary after completing all subchapters
        
        Args:
            chapter_data: Complete chapter data
            subtitle_name: Name of subtitle
            chapter_name: Name of chapter
        """
        subtitle_clean = re.sub(r'[^\w\s-]', '', subtitle_name).strip().replace(' ', '_')[:50]
        chapter_clean = re.sub(r'[^\w\s-]', '', chapter_name).strip().replace(' ', '_')[:50]
        
        chapter_dir = os.path.join(self.output_dir, subtitle_clean, chapter_clean)
        os.makedirs(chapter_dir, exist_ok=True)
        
        summary_file = os.path.join(chapter_dir, '_chapter_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(chapter_data, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Chapter summary saved: {summary_file}")
    
    def scrape_section(self, section_url: str, section_info: Dict, subtitle_name: str = '', chapter_name: str = '') -> Optional[Dict]:
        """
        Scrape an individual IRC section
        
        Args:
            section_url: URL of the section
            section_info: Basic info about the section
            subtitle_name: Name of subtitle for folder organization
            chapter_name: Name of chapter for folder organization
            
        Returns:
            Dictionary containing section data
        """
        # Check if already completed
        if self._check_if_completed(section_url):
            logging.info(f"Skipping already completed section: {section_info.get('title', section_url)}")
            return {'skipped': True, 'url': section_url}
        
        logging.info(f"Scraping section: {section_info.get('title', section_url)}")
        
        soup = self._make_request(section_url)
        if not soup:
            return None
        
        # Extract section number from URL or title (handle multi-letter suffixes like 45AA, 1400Z-2)
        # URLs use lowercase (section_30a) so match case-insensitively, then uppercase it
        section_match = re.search(r'section_(\d+[a-zA-Z]*(?:-\d+)?)', section_url, re.IGNORECASE)
        if not section_match:
            # Try extracting from title as fallback
            title_match = re.search(r'Sec\.\s+(\d+[A-Z]*(?:-\d+)?)', section_info.get('title', ''))
            section_number = title_match.group(1) if title_match else 'unknown'
        else:
            # Uppercase the letters for consistency (30a -> 30A, 45aa -> 45AA)
            section_number = section_match.group(1).upper()
        
        content = self._parse_section_content(soup, section_number)
        content.update(section_info)
        
        # Save individual section file
        if subtitle_name and chapter_name:
            self._save_section_file(content, subtitle_name, chapter_name, section_number)
        
        # Mark as completed
        self._mark_completed(section_url)
        
        return content
    
    def scrape_part(self, part_url: str, part_info: Dict, subtitle_name: str = '', chapter_name: str = '') -> Dict:
        """
        Scrape a part and its sections (or subparts if they exist)
        
        Args:
            part_url: URL of the part
            part_info: Basic info about the part
            subtitle_name: Name of subtitle for folder organization
            chapter_name: Name of chapter for folder organization
            
        Returns:
            Dictionary containing part data with sections
        """
        if self.should_pause:
            logging.info("Pause requested, stopping...")
            return part_info
        
        logging.info(f"Scraping part: {part_info.get('title', part_url)}")
        
        soup = self._make_request(part_url)
        if not soup:
            return part_info
        
        part_data = part_info.copy()
        part_data['sections'] = []
        part_data['subparts'] = []
        
        # Find all links (could be sections or subparts)
        links = self._extract_links_and_info(soup)
        
        for link_info in links:
            if self.should_pause:
                logging.info("Pause requested, stopping at current part...")
                break
            
            # Check if this is a subpart (some parts have subparts instead of direct sections)
            if 'Subpart' in link_info['title']:
                logging.info(f"Scraping subpart: {link_info.get('title', link_info['url'])}")
                subpart_soup = self._make_request(link_info['url'])
                if subpart_soup:
                    # Get sections from subpart
                    subpart_sections = self._extract_links_and_info(subpart_soup)
                    for section_info in subpart_sections:
                        if 'Sec.' in section_info['title'] or 'section' in section_info['url'].lower():
                            section_data = self.scrape_section(section_info['url'], section_info, subtitle_name, chapter_name)
                            if section_data and not section_data.get('skipped'):
                                part_data['sections'].append(section_data)
                    part_data['subparts'].append(link_info)
            # Direct section (no subparts)
            elif 'Sec.' in link_info['title'] or 'section' in link_info['url'].lower():
                section_data = self.scrape_section(link_info['url'], link_info, subtitle_name, chapter_name)
                if section_data and not section_data.get('skipped'):
                    part_data['sections'].append(section_data)
        
        return part_data
    
    def scrape_subchapter(self, subchapter_url: str, subchapter_info: Dict, subtitle_name: str = '', chapter_name: str = '') -> Dict:
        """
        Scrape a subchapter and its parts
        
        Args:
            subchapter_url: URL of the subchapter
            subchapter_info: Basic info about the subchapter
            subtitle_name: Name of subtitle for folder organization
            chapter_name: Name of chapter for folder organization
            
        Returns:
            Dictionary containing subchapter data with parts
        """
        if self.should_pause:
            logging.info("Pause requested, stopping...")
            return subchapter_info
        
        logging.info(f"Scraping subchapter: {subchapter_info.get('title', subchapter_url)}")
        
        soup = self._make_request(subchapter_url)
        if not soup:
            return subchapter_info
        
        subchapter_data = subchapter_info.copy()
        subchapter_data['parts'] = []
        # Ensure sections is a list, not the dict from _extract_sections_range
        if 'sections' in subchapter_data and isinstance(subchapter_data['sections'], dict):
            subchapter_data['sections'] = []
        
        # Find all part links
        part_links = self._extract_links_and_info(soup)
        
        for part_info in part_links:
            if self.should_pause:
                logging.info("Pause requested, stopping at current subchapter...")
                break
            
            # Check if this is a part
            if 'Part' in part_info['title']:
                part_data = self.scrape_part(part_info['url'], part_info, subtitle_name, chapter_name)
                subchapter_data['parts'].append(part_data)
            # Some subchapters might have sections directly
            elif 'Sec.' in part_info['title']:
                section_data = self.scrape_section(part_info['url'], part_info, subtitle_name, chapter_name)
                if section_data and not section_data.get('skipped'):
                    if 'sections' not in subchapter_data or not isinstance(subchapter_data.get('sections'), list):
                        subchapter_data['sections'] = []
                    subchapter_data['sections'].append(section_data)
        
        return subchapter_data
    
    def scrape_chapter(self, chapter_url: str, chapter_info: Dict, subtitle_name: str = '') -> Dict:
        """
        Scrape a chapter and its subchapters
        
        Args:
            chapter_url: URL of the chapter
            chapter_info: Basic info about the chapter
            subtitle_name: Name of subtitle for folder organization
            
        Returns:
            Dictionary containing chapter data with subchapters
        """
        if self.should_pause:
            logging.info("Pause requested, stopping...")
            return chapter_info
        
        logging.info(f"Scraping chapter: {chapter_info.get('title', chapter_url)}")
        
        soup = self._make_request(chapter_url)
        if not soup:
            return chapter_info
        
        chapter_data = chapter_info.copy()
        chapter_data['subchapters'] = []
        
        chapter_name = chapter_info.get('title', 'Unknown_Chapter')
        
        # Find all subchapter links
        subchapter_links = self._extract_links_and_info(soup)
        
        for subchapter_info in subchapter_links:
            if self.should_pause:
                logging.info("Pause requested, stopping at current chapter...")
                break
            
            # Check if this is a subchapter
            if 'Subchapter' in subchapter_info['title']:
                subchapter_data = self.scrape_subchapter(subchapter_info['url'], subchapter_info, subtitle_name, chapter_name)
                chapter_data['subchapters'].append(subchapter_data)
            # Some chapters might have parts directly
            elif 'Part' in subchapter_info['title']:
                part_data = self.scrape_part(subchapter_info['url'], subchapter_info, subtitle_name, chapter_name)
                if 'parts' not in chapter_data:
                    chapter_data['parts'] = []
                chapter_data['parts'].append(part_data)
            # Some chapters have sections directly (e.g., Chapter 2, 2A, 4)
            elif 'Sec.' in subchapter_info['title']:
                section_data = self.scrape_section(subchapter_info['url'], subchapter_info, subtitle_name, chapter_name)
                if section_data and not section_data.get('skipped'):
                    if 'sections' not in chapter_data or not isinstance(chapter_data.get('sections'), list):
                        chapter_data['sections'] = []
                    chapter_data['sections'].append(section_data)
        
        # Save chapter summary
        self._save_chapter_summary(chapter_data, subtitle_name, chapter_name)
        
        return chapter_data
    
    def scrape_subtitle(self, subtitle_url: str, subtitle_info: Dict) -> Dict:
        """
        Scrape a subtitle and its chapters
        
        Args:
            subtitle_url: URL of the subtitle
            subtitle_info: Basic info about the subtitle
            
        Returns:
            Dictionary containing subtitle data with chapters
        """
        if self.should_pause:
            logging.info("Pause requested, stopping...")
            return subtitle_info
        
        logging.info(f"Scraping subtitle: {subtitle_info.get('title', subtitle_url)}")
        
        soup = self._make_request(subtitle_url)
        if not soup:
            return subtitle_info
        
        subtitle_data = subtitle_info.copy()
        subtitle_data['chapters'] = []
        
        subtitle_name = subtitle_info.get('title', 'Unknown_Subtitle')
        
        # Find all chapter links
        chapter_links = self._extract_links_and_info(soup)
        
        for chapter_info in chapter_links:
            if self.should_pause:
                logging.info("Pause requested, stopping at current subtitle...")
                break
            
            if 'Chapter' in chapter_info['title']:
                chapter_data = self.scrape_chapter(chapter_info['url'], chapter_info, subtitle_name)
                subtitle_data['chapters'].append(chapter_data)
        
        return subtitle_data
    
    def scrape_all(self, resume: bool = False):
        """
        Scrape the entire IRC code starting from the main TOC
        
        Args:
            resume: If True, resume from last saved progress
        """
        logging.info("Starting IRC Code scrape...")
        
        # Check for existing progress if resume is requested
        completed_subtitles = set()
        if resume:
            progress_file = os.path.join(self.output_dir, 'irc_data_progress.json')
            if os.path.exists(progress_file):
                try:
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        progress_data = json.load(f)
                    self.data = progress_data
                    completed_subtitles = {sub['url'] for sub in self.data.get('subtitles', [])}
                    logging.info(f"Resuming from progress: {len(completed_subtitles)} subtitles already completed")
                except Exception as e:
                    logging.error(f"Failed to load progress file: {e}")
                    logging.info("Starting fresh scrape")
            else:
                logging.info("No progress file found, starting fresh scrape")
        
        logging.info(f"Fetching main TOC from {self.TOC_URL}")
        
        # Get main TOC page
        soup = self._make_request(self.TOC_URL)
        if not soup:
            logging.error("Failed to fetch main TOC page")
            return
        
        # Extract all subtitles
        subtitle_links = self._extract_links_and_info(soup)
        
        # Filter to only subtitles
        subtitles = [link for link in subtitle_links if 'Subtitle' in link['title']]
        
        logging.info(f"Found {len(subtitles)} subtitles to scrape")
        
        if resume and completed_subtitles:
            logging.info(f"Skipping {len(completed_subtitles)} already completed subtitles")
        
        for i, subtitle_info in enumerate(subtitles, 1):
            # Skip if already completed (when resuming)
            if resume and subtitle_info['url'] in completed_subtitles:
                logging.info(f"Skipping already completed: {subtitle_info['title']}")
                continue
            
            logging.info(f"\n{'='*80}")
            logging.info(f"Processing subtitle {i}/{len(subtitles)}")
            logging.info(f"{'='*80}\n")
            
            try:
                subtitle_data = self.scrape_subtitle(subtitle_info['url'], subtitle_info)
                self.data['subtitles'].append(subtitle_data)
                
                # Save progress after each subtitle
                self._save_progress()
                logging.info(f"✓ Progress saved. Safe to pause/resume at any time.")
            except KeyboardInterrupt:
                logging.info("\n\n" + "="*80)
                logging.info("⏸️  SCRAPING PAUSED BY USER")
                logging.info("="*80)
                logging.info(f"Progress saved: {len(self.data['subtitles'])} subtitles completed")
                logging.info(f"To resume, run: scraper.scrape_all(resume=True)")
                logging.info("="*80)
                self._save_progress()
                return
            except Exception as e:
                logging.error(f"Error processing subtitle {subtitle_info['title']}: {e}")
                logging.info("Saving progress before continuing...")
                self._save_progress()
                continue
        
        if self.should_pause:
            logging.info("\n" + "="*80)
            logging.info("Scraping PAUSED by user")
            logging.info(f"Progress saved: {len(self.completed_sections)} sections completed")
            logging.info("To resume: Run the script again, it will automatically continue")
            logging.info("="*80)
        else:
            logging.info("\n" + "="*80)
            logging.info("Scraping completed!")
            logging.info("="*80)
            
            # Final save
            self._save_final()
    
    def _save_progress(self):
        """Save progress to a JSON file"""
        progress_file = os.path.join(self.output_dir, 'irc_data_progress.json')
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        logging.info(f"Progress saved to {progress_file}")
    
    def _save_final(self):
        """Save final data in multiple formats"""
        # JSON format
        json_file = os.path.join(self.output_dir, 'irc_complete.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        logging.info(f"Complete data saved to {json_file}")
        
        # Create a summary file
        summary_file = os.path.join(self.output_dir, 'scrape_summary.txt')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"IRC Code Scrape Summary\n")
            f.write(f"{'='*50}\n")
            f.write(f"Scrape Date: {self.data['metadata']['scrape_date']}\n")
            f.write(f"Source: {self.data['metadata']['source_url']}\n\n")
            
            total_sections = 0
            for subtitle in self.data['subtitles']:
                f.write(f"\n{subtitle['title']}\n")
                chapter_count = len(subtitle.get('chapters', []))
                f.write(f"  Chapters: {chapter_count}\n")
                
                for chapter in subtitle.get('chapters', []):
                    subchapter_count = len(chapter.get('subchapters', []))
                    for subchapter in chapter.get('subchapters', []):
                        part_count = len(subchapter.get('parts', []))
                        for part in subchapter.get('parts', []):
                            section_count = len(part.get('sections', []))
                            total_sections += section_count
            
            f.write(f"\n\nTotal Sections Scraped: {total_sections}\n")
        
        logging.info(f"Summary saved to {summary_file}")


def main():
    """Main execution function"""
    import sys
    
    scraper = IRCCodeScraper(output_dir="irc_data")
    
    # Setup signal handler for graceful pause on Ctrl+C
    def signal_handler(sig, frame):
        logging.info("\n\n⏸️  Ctrl+C detected - requesting graceful pause...")
        scraper.request_pause()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check if there's existing progress
    progress_file = os.path.join("irc_data", 'irc_data_progress.json')
    has_progress = os.path.exists(progress_file)
    
    print("\n" + "="*80)
    print("IRC Code Scraper for Bloomberg Tax")
    print("="*80)
    print("\nThis scraper will download the complete Internal Revenue Code")
    print("from Bloomberg Tax's public website.")
    print("\nWarning: This will take considerable time (potentially hours)")
    print("depending on the size of the code and your internet connection.")
    print("\nData will be saved to the 'irc_data' directory.")
    print("Progress will be saved after each subtitle.")
    
    if has_progress:
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            completed = len(progress_data.get('subtitles', []))
            print("\n" + "⚠️  "*20)
            print(f"EXISTING PROGRESS DETECTED: {completed} subtitles already completed")
            print("⚠️  "*20)
        except:
            pass
    
    print("\n" + "="*80)
    print("Options:")
    print("  1. Start fresh scrape (overwrites existing progress)")
    print("  2. Resume from last saved progress")
    print("  3. Cancel")
    print("="*80 + "\n")
    
    if has_progress:
        response = input("Choose option (1/2/3): ").strip()
    else:
        response = input("Start scraping? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            response = '1'
        else:
            response = '3'
    
    if response == '1':
        print("\n🚀 Starting fresh scrape...")
        print("💡 TIP: You can press Ctrl+C at any time to pause.")
        print("   Progress is saved after each subtitle, so you can resume later.\n")
        try:
            scraper.scrape_all(resume=False)
            print("\n" + "="*80)
            print("✅ Scraping completed! Check the 'irc_data' directory for results.")
            print("="*80 + "\n")
        except KeyboardInterrupt:
            print("\n\n⏸️  Scraping paused. Run again and choose 'Resume' to continue.")
    elif response == '2':
        if not has_progress:
            print("❌ No progress file found. Please start fresh scrape.")
            return
        print("\n🔄 Resuming from last saved progress...")
        print("💡 TIP: You can press Ctrl+C at any time to pause again.\n")
        try:
            scraper.scrape_all(resume=True)
            print("\n" + "="*80)
            print("✅ Scraping completed! Check the 'irc_data' directory for results.")
            print("="*80 + "\n")
        except KeyboardInterrupt:
            print("\n\n⏸️  Scraping paused. Run again and choose 'Resume' to continue.")
    else:
        print("❌ Scraping cancelled.")


if __name__ == "__main__":
    main()
