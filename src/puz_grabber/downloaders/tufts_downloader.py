import requests
from requests.exceptions import ConnectTimeout, ReadTimeout
from bs4 import BeautifulSoup 
from datetime import datetime
from .crosshare_downloader import CrosshareBaseDownloader
import re
import json

class TuftsDownloader(CrosshareBaseDownloader):

    def get_latest_id(self):
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(self.base_url, headers=headers, timeout=(5.05, 15))
        except (ConnectTimeout, ReadTimeout) as e:
            print(f"Failed to get page {self.base_url}: {e}")
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        link = soup.select_one('a[href*="/article/"][href*="mini-crossword-"]')
        puzzle_page_url = link["href"] if link else None
        if puzzle_page_url is None:
            print(f"No mini crossword link found at {self.base_url}")
            return None
        try:
            response = requests.get(puzzle_page_url, headers=headers, timeout=(5.05, 15))
            self.puzzle_page_html = response.text
        except (ConnectTimeout, ReadTimeout) as e:
            print(f"Failed to get page {puzzle_page_url}: {e}")
            return None
        if match := re.search(r'https://crosshare\.org/embed/([A-Za-z0-9]+)', self.puzzle_page_html):
            return match.group(1)
        print(f"No embed URL found in {puzzle_page_url}")
        return None

    def get_date(self): 
        script_block = BeautifulSoup(self.puzzle_page_html, "html.parser").find("script", type="application/ld+json")
        content_data = json.loads(script_block.string)
        date_section = content_data["dateCreated"]
        if date_section and (match := re.search(r'\d{4}-\d{2}-\d{2}', date_section)):
            try:
                return datetime.strptime(re.sub(r'[^\d-]', '', match.group(0)), '%Y-%m-%d').date()
            except ValueError as e:
                print(f"Could not determine date from {self.url}: {e}")
        else:
            print(f"No date found in {self.url}")
            return None
