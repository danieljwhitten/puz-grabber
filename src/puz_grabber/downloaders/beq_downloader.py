import requests
from requests.exceptions import ConnectTimeout, ReadTimeout
import re
import json
from json import JSONDecodeError
from bs4 import BeautifulSoup
from datetime import datetime

from ..config import SOURCES


class BEQDownloader:

    def __init__(self, puzzle_code):
        self.base_url = SOURCES[puzzle_code]["base_url"]
        self.outlet = SOURCES[puzzle_code]["outlet"]
        self.code = puzzle_code
        self.url = self.get_latest_url() 
        if self.url is None:
            raise RuntimeError(f"Could not determine latest puzzle URL for {self.code}")
        self.date = self.get_date()
        result = self.download()
        if result is None:
            raise RuntimeError(f"Failed to download puzzle from {self.url}")
        self.filename, self.puzzle_file = result


    def get_latest_url(self):
        try:
            response = requests.get(self.base_url, timeout=(5.05, 15))
            if response.status_code != 200:
                print(f"Could not reach webpage at: {self.base_url}")
                return None
            self.page_text = response.text
        except (ConnectTimeout, ReadTimeout) as e:
            print(f"Failed to get page {self.base_url}: {e}")
            return None
        try:
            script_block = BeautifulSoup(response.text, "html.parser").find("a", href=re.compile(r"^/files/.*?\.puz$"))
            return f"{self.base_url}{script_block['href']}"
        except (AttributeError, JSONDecodeError, KeyError, TypeError, IndexError) as e:
            print(f"Failed to get puzzle url from {self.base_url}: {e}")
            return None

    def get_date(self):
        soup = BeautifulSoup(self.page_text, 'html.parser')
        date_section = soup.find('time', class_='entry-date published updated')
        if date_section: 
            try:
                return datetime.fromisoformat(date_section.attrs["datetime"])
            except ValueError as e:
                print(f"Could not determine date from {self.base_url}: {e}")
        else:
            print(f"No date found in {self.base_url}")
            return None

    def download(self):
        try:
            puzzle_file = requests.get(self.url, timeout=(5.05, 30))
        except (ConnectTimeout, ReadTimeout) as e:
            print(f"Failed to download puzzle from {self.url}: {e}")
            return
        if puzzle_file.status_code != 200:
            print(f"Failed to reach {self.url}: Status {puzzle_file.status_code}")
            return
        if self.date:
            if SOURCES[self.code]["date_in_filename"]:
                filename = f"{self.outlet} ({self.date:%a., %b %-d, %Y})_{self.code}_{self.date:%Y%m%d}.puz"
            else:
                filename = f"{self.outlet}_{self.code}_{self.date:%Y%m%d}.puz"
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
