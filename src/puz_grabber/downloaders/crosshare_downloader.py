import requests
from requests.exceptions import ConnectTimeout, ReadTimeout
import re
import json
from json import JSONDecodeError
from bs4 import BeautifulSoup
from datetime import datetime
from ..config import SOURCES


class CrosshareBaseDownloader:

    def __init__(self, puzzle_code):
        self.base_url = SOURCES[puzzle_code]["base_url"]
        self.outlet = SOURCES[puzzle_code]["outlet"]
        self.code = puzzle_code
        self.id = self.get_latest_id() 
        if self.id is None:
            raise RuntimeError(f"Could not determine latest puzzle ID for {self.code}")
        self.url = f"https://crosshare.org/crosswords/{self.id}"
        self.date = self.get_date()
        result = self.download()
        if result is None:
            raise RuntimeError(f"Failed to download puzzle from {self.url}")
        self.filename, self.puzzle_file = result


    def get_latest_id(self):
        try:
            response = requests.get(self.base_url, timeout=(5.05, 15))
        except (ConnectTimeout, ReadTimeout) as e:
            print(f"Failed to get page {self.base_url}: {e}")
            return None
        try:
            script_block = BeautifulSoup(response.text, "html.parser").find("script", id="__NEXT_DATA__")
            content_data = json.loads(script_block.string)
            puzzles = content_data["props"]["pageProps"]["puzzles"]
            if not puzzles:
                return None
            first = puzzles[0]
            if isinstance(first, dict):
                return first["id"]
            else:
                return first[1]["id"]  # puzzle dict is at index 1
        except (AttributeError, JSONDecodeError, KeyError, TypeError, IndexError) as e:
            print(f"Failed to get puzzle id from {self.base_url}: {e}")
            return None

    def get_date(self):
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            webpage = requests.get(self.url, headers=headers, timeout=(5.05, 15))
        except (ConnectTimeout, ReadTimeout) as e:
            print(f"Failed to get page {self.url}: {e}")
            return None
        if webpage.status_code != 200:
            print(f"Could not reach webpage at: {self.url}")
            return None
        soup = BeautifulSoup(webpage.text, 'html.parser')
        date_section = soup.find('p', class_='overflowWrapBreakWord')
        if date_section and (match := re.search(r'\d{4}-\d{2}-\d{2}', date_section.get_text())):
            try:
                return datetime.strptime(re.sub(r'[^\d-]', '', match.group(0)), '%Y-%m-%d').date()
            except ValueError as e:
                print(f"Could not determine date from {self.url}: {e}")
        else:
            print(f"No date found in {self.url}")
            return None

    def download(self):
        file_url = f"https://crosshare.org/api/puz/{self.id}"
        try:
            puzzle_file = requests.get(file_url, timeout=(5.05, 30))
        except (ConnectTimeout, ReadTimeout) as e:
            print(f"Failed to download puzzle from {file_url}: {e}")
            return
        if puzzle_file.status_code != 200:
            print(f"Failed to reach {file_url}: Status {puzzle_file.status_code}")
            return
        if self.date:
            filename = f"{self.outlet} ({self.date:%a., %b %d, %Y})_{self.code}_{self.date:%Y%m%d}.puz"
        else:
            filename = f"{self.outlet} (undated)_{self.code}_{self.id}.puz"
        filename = filename.replace("/", "-")
        return (filename, puzzle_file)
        

    def write_file(self):
        try:
            with open(self.filename, "wb") as f:
                f.write(self.puzzle_file.content)
            print(f"Downloaded puzzle as {self.filename}")
        except OSError as e:
            print(f"Failed to download file {self.filename}: {e}")

class CrosshareDailyDownloader(CrosshareBaseDownloader):

    def get_date(self):
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            webpage = requests.get(self.base_url, headers=headers, timeout=(5.05, 15))
        except (ConnectTimeout, ReadTimeout) as e:
            print(f"Failed to get page {self.url}: {e}")
            return None
        if webpage.status_code != 200:
            print(f"Could not reach webpage at: {self.url}")
            return None
        soup = BeautifulSoup(webpage.text, 'html.parser')
        date_section = soup.find('h3', class_='marginBottom0')
        if date_section and (match := re.search(r'\d{1,2}\/\d{1,2}\/\d{4}', date_section.get_text())):
            try:
                return datetime.strptime(re.sub(r'[^\d\/]', '', match.group(0)), '%m/%d/%Y').date()
            except ValueError as e:
                print(f"Could not determine date from {self.url}: {e}")
        else:
            print(f"No date found in {self.url}")
            return None
