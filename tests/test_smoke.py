"""Smoke tests for puz_grabber error handling (exception-based init).

No network access. Every requests.get is replaced with a fake that routes by
URL, and each test runs inside a throwaway directory so we can assert whether a
.puz file was written.

__init__ raises RuntimeError on failure, so failure tests assert on that.

Run:
    python -m pytest tests/ -q
    python -m unittest discover -s tests -v
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from requests.exceptions import ConnectTimeout

from puz_grabber.downloaders import CrosshareBaseDownloader, TuftsDownloader


NEXT_DATA_OK = (
    '<html><script id="__NEXT_DATA__" type="application/json">'
    '{"props":{"pageProps":{"puzzles":[{"id":"ABC123"}]}}}'
    "</script></html>"
)

PUZZLE_PAGE_OK = (
    '<html><head><meta property="og:title" content="Mini 261"/></head>'
    '<body><p class="overflowWrapBreakWord">Published 2026-10-28T09:00:49Z</p>'
    "</body></html>"
)

PUZZLE_PAGE_NO_DATE = "<html><body>no date here</body></html>"


class FakeResponse:
    def __init__(self, text="", status_code=200, content=b""):
        self.text = text
        self.status_code = status_code
        self.content = content


def router(base_text=NEXT_DATA_OK, puzzle_text=PUZZLE_PAGE_OK, api=None):
    """Build a fake requests.get that routes by URL.

    api: a FakeResponse, an Exception instance to raise, or None (=> 404).
    """
    def _get(url, **kwargs):
        if "/api/puz/" in url:
            if isinstance(api, Exception):
                raise api
            return api if api is not None else FakeResponse(status_code=404)
        if "/crosswords/" in url:
            return FakeResponse(puzzle_text)
        return FakeResponse(base_text)
    return _get


def raiser(exc):
    def _get(url, **kwargs):
        raise exc
    return _get


class TempDirTestCase(unittest.TestCase):
    """Run each test in a scratch directory so we can inspect written files."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._cwd = os.getcwd()
        os.chdir(self._tmp.name)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def written(self):
        return sorted(os.listdir(self._tmp.name))


class LatestIdFailures(TempDirTestCase):
    """get_latest_id() failures should raise RuntimeError during init."""

    def _init(self, get):
        with patch("requests.get", side_effect=get), patch("builtins.print"):
            return CrosshareBaseDownloader("dc")

    def test_timeout_raises_runtime_error(self):
        with self.assertRaises(RuntimeError) as cm:
            self._init(raiser(ConnectTimeout("boom")))
        self.assertIn("Could not determine latest puzzle ID", str(cm.exception))

    def test_no_next_data_script_raises(self):
        with self.assertRaises(RuntimeError) as cm:
            self._init(router(base_text="<html></html>"))
        self.assertIn("Could not determine latest puzzle ID", str(cm.exception))

    def test_malformed_json_raises(self):
        bad = '<script id="__NEXT_DATA__">{oops}</script>'
        with self.assertRaises(RuntimeError):
            self._init(router(base_text=bad))

    def test_empty_puzzles_raises(self):
        empty = '<script id="__NEXT_DATA__">{"props":{"pageProps":{"puzzles":[]}}}</script>'
        with self.assertRaises(RuntimeError):
            self._init(router(base_text=empty))

    def test_missing_puzzles_key_raises(self):
        partial = '<script id="__NEXT_DATA__">{"props":{"pageProps":{}}}</script>'
        with self.assertRaises(RuntimeError):
            self._init(router(base_text=partial))

    def test_empty_script_tag_raises(self):
        # json.loads(None) -> TypeError
        empty_tag = '<script id="__NEXT_DATA__"></script>'
        with self.assertRaises(RuntimeError):
            self._init(router(base_text=empty_tag))

    def test_nothing_written_when_init_fails(self):
        cases = [
            "<html></html>",
            '<script id="__NEXT_DATA__">{oops}</script>',
            '<script id="__NEXT_DATA__">{"props":{"pageProps":{}}}</script>',
        ]
        for base_text in cases:
            with self.subTest(base_text=base_text):
                with self.assertRaises(RuntimeError):
                    self._init(router(base_text=base_text))
                self.assertEqual(self.written(), [])


class DownloadFailures(TempDirTestCase):
    """download() failures should raise RuntimeError during init."""

    def _init(self, api):
        with patch("requests.get", side_effect=router(api=api)), patch("builtins.print"):
            return CrosshareBaseDownloader("dc")

    def test_api_timeout_raises(self):
        with self.assertRaises(RuntimeError) as cm:
            self._init(ConnectTimeout("slow"))
        self.assertIn("Failed to download puzzle", str(cm.exception))
        self.assertEqual(self.written(), [])

    def test_api_404_raises(self):
        with self.assertRaises(RuntimeError) as cm:
            self._init(FakeResponse(status_code=404))
        self.assertIn("Failed to download puzzle", str(cm.exception))
        self.assertEqual(self.written(), [])

    def test_api_500_raises(self):
        with self.assertRaises(RuntimeError):
            self._init(FakeResponse(status_code=500))
        self.assertEqual(self.written(), [])

    def test_success_writes_one_puz(self):
        """Full success path: init completes, write_file() creates the .puz."""
        with patch("requests.get", side_effect=router(api=FakeResponse(content=b"PUZDATA"))), \
             patch("builtins.print"):
            puzzle = CrosshareBaseDownloader("dc")
            puzzle.write_file()

        self.assertIsNotNone(puzzle.date)
        files = self.written()
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].endswith(".puz"))
        self.assertIn("2026", files[0])

    def test_unwritable_target_catches_oserror(self):
        """OSError during file write should be caught, not propagated."""
        with patch("requests.get", side_effect=router(api=FakeResponse(content=b"PUZDATA"))), \
             patch("builtins.print"):
            puzzle = CrosshareBaseDownloader("dc")
            with patch("builtins.open", side_effect=OSError("permission denied")):
                puzzle.write_file()  # must not raise

        self.assertEqual(self.written(), [])


class MissingMetadata(TempDirTestCase):
    """Missing metadata should not prevent the download."""

    def test_missing_date_still_downloads_undated(self):
        with patch("requests.get", side_effect=router(
                puzzle_text=PUZZLE_PAGE_NO_DATE,
                api=FakeResponse(content=b"PUZDATA"))), \
             patch("builtins.print"):
            puzzle = CrosshareBaseDownloader("dc")
            self.assertIsNone(puzzle.date)
            puzzle.write_file()

        files = self.written()
        self.assertEqual(len(files), 1)
        self.assertIn("undated", files[0])


class TuftsFailures(TempDirTestCase):
    def test_no_mini_crossword_link_raises(self):
        page = FakeResponse("<html><body>nothing here</body></html>")
        with patch("requests.get", return_value=page) as get, patch("builtins.print"):
            with self.assertRaises(RuntimeError):
                TuftsDownloader("td")

        # Should stop after the first request, not chase a None URL.
        self.assertEqual(get.call_count, 1)
        self.assertEqual(self.written(), [])


class CliBehaviour(unittest.TestCase):
    def test_unknown_code_exits_2(self):
        from puz_grabber.__main__ import main
        with patch("sys.argv", ["puz-grabber", "nope"]):
            with self.assertRaises(SystemExit) as ctx:
                main()
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

