from .crosshare_downloader import CrosshareBaseDownloader, CrosshareDailyDownloader
from .tufts_downloader import TuftsDownloader
from .beq_downloader import BEQDownloader

HANDLERS = {
        "beq": BEQDownloader,
        "crosshare": CrosshareBaseDownloader,
        "crossharedaily": CrosshareDailyDownloader,
        "tufts": TuftsDownloader
}

__all__ = ["BEQDownloader","CrosshareBaseDownloader", "CrosshareDailyDownloader", "TuftsDownloader"]
