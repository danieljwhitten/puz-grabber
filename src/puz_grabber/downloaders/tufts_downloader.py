import requests
from requests.exceptions import ConnectTimeout, ReadTimeout
from bs4 import BeautifulSoup 
from .crosshare_downloader import CrosshareBaseDownloader
import re

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
        except (ConnectTimeout, ReadTimeout) as e:
            print(f"Failed to get page {puzzle_page_url}: {e}")
            return None
        if match := re.search(r'https://crosshare\.org/embed/([A-Za-z0-9]+)', response.text):
            return match.group(1)
        print(f"No embed URL found in {puzzle_page_url}")
        return None
