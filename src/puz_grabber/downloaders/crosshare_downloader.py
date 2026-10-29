import requests
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
from ..config import SOURCES


class CrosshareDownloader:

    def __init__(self, puzzle_code):
        self.base_url = SOURCES[puzzle_code]["base_url"]
        self.outlet = SOURCES[puzzle_code]["outlet"]
        self.code = puzzle_code
        self.id = self.get_latest_id() 
        print(self.id)
        print(self.base_url)
        print(self.outlet)
        self.url = f"https://crosshare.org/crosswords/{self.id}"
        self.date = self.get_meta()[0]
        self.title = self.get_meta()[1]

        self.download()

    def get_latest_id(self):
        response = requests.get(self.base_url)
        script_block = BeautifulSoup(response.text, "html.parser").find("script", id="__NEXT_DATA__")
        content_data = json.loads(script_block.string)
        
        puzzles = content_data["props"]["pageProps"]["puzzles"]
        if not puzzles:
            return None
    
        # Handle both structures: dict directly OR triple/list
        first = puzzles[0]
        if isinstance(first, dict):
            return first["id"]
        else:
            return first[1]["id"]  # puzzle dict is at index 1

    def get_meta(self):
        webpage = requests.get(self.url)
        if webpage.status_code == 200:
            soup = BeautifulSoup(webpage.text, 'html.parser')
            try:
                date_section = soup.find('p', class_='overflowWrapBreakWord').get_text()
                date_text = re.search(r'\d{4}-\d{2}-\d{2}', date_section).group(0)
                date = datetime.strptime(date_text, '%Y-%m-%d').date()
            except:
                print(f"Could not extract date from {self.url}")
                date = None
            try:
                meta_tag = soup.find('meta', property='og:title')
                title = meta_tag.get('content') if meta_tag else None
            except:
                print(f"Could not extract title from {self.url}")
                date = None
            return (date, title)
        else:
            print(f"Could not reach webpage at: {self.url}")
            return None

    def download(self):
        puzzle_file = requests.get(f"https://crosshare.org/api/puz/{self.id}")
        filename = f"{self.outlet} ({self.date:%a., %b %d, %Y}): {self.title}_{self.code}_{self.date:%Y%m%d}.puz"
        filename = filename.replace("/", "-")
        try:
            with open(filename, "wb") as f:
                f.write(puzzle_file.content)
            print(f"Downloaded puzzle as {filename}")
        except:
            print(f"Failed to download file {filename}")

        
