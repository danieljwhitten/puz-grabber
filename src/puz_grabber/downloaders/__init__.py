from .crosshare_downloader import CrosshareBaseDownloader
from .tufts_downloader import TuftsDownloader

HANDLERS = {
        "crosshare": CrosshareBaseDownloader,
        "tufts": TuftsDownloader
}

__all__ = ["CrosshareBaseDownloader", "TuftsDownloader"]
