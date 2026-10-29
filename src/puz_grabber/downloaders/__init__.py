from .crosshare_downloader import CrosshareDownloader

HANDLERS = {
        "crosshare": CrosshareDownloader
}

__all__ = ["CrosshareDownloader"]
