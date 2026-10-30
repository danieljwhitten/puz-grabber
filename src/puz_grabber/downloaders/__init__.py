from .crosshare_downloader import CrosshareDownloader
from .tufts_downloader import TuftsDownloader

HANDLERS = {
        "crosshare": CrosshareDownloader,
        "tufts": TuftsDownloader
}

__all__ = ["CrosshareDownloader", "TuftsDownloader"]
