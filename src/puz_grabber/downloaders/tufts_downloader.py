import requests
from datetime import datetime
from bs4 import BeautifulSoup 
from .crosshare_downloader import CrosshareDownloader
import re

class TuftsDownloader(CrosshareDownloader):

    def __init__(self, puzzle_code = "td"):
        super().__init__(puzzle_code)

    def get_latest_id(self):
        headers = {'User-Agent': 'Googlebot'}
        response = requests.get(self.base_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        link = soup.select_one('a[href*="/article/"][href*="mini-crossword-"]')
        puzzle_page_url = link["href"] if link else None
        response = requests.get(puzzle_page_url, headers=headers)
        return re.search(r'https://crosshare.org/embed/(.*?)/', response.text).group(1)

    def get_meta(self):
        headers = {'User-Agent': 'Googlebot'}
        webpage = requests.get(self.url, headers=headers)
        if webpage.status_code == 200:
            soup = BeautifulSoup(webpage.text, 'html.parser')
            try:
                date_section = soup.find('p', class_='overflowWrapBreakWord').get_text()
                date_text = re.search(r'\d{4}-\d{2}-\d{2}', date_section).group(0)
                date_text = re.sub(r'[^\d-]', '', date_text)
                date = datetime.strptime(date_text, '%Y-%m-%d').date()
            except (ValueError, AttributeError, TypeError) as e:
                print(f"Could not extract date from {self.url}: {e}")
                date = None 
            try:
                meta_tag = soup.find('meta', property='og:title')
                title = meta_tag.get('content') if meta_tag else None
            except (ValueError, AttributeError, TypeError) as e:
                print(f"Could not extract title from {self.url}: {e}")
                title = None
            return (date, title)
