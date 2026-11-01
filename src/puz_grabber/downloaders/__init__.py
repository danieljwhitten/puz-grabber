from .crosshare_downloader import CrosshareBaseDownloader, CrosshareDailyDownloader
from .tufts_downloader import TuftsDownloader

HANDLERS = {
        "crosshare": CrosshareBaseDownloader,
        "crossharedaily": CrosshareDailyDownloader,
        "tufts": TuftsDownloader
}

__all__ = ["CrosshareBaseDownloader", "CrosshareDailyDownloader", "TuftsDownloader"]
