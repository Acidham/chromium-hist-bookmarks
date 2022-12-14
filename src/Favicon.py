import multiprocessing
import os
import time
import urllib.request
from urllib.parse import urlparse

from Alfred3 import Tools


class Icons(object):
    """
    Heat favicon cache and provide fiepath to cached png file

    Args:

        object (obj): -

    """

    def __init__(self, histories: list) -> None:
        """
        Heat cache of favicon files

        Args:

            histories (list): Hiosty object with URL, NAME, addtional.

        """
        self.wf_cache_dir = Tools.getCacheDir()
        self.histories = histories
        self._cache_controller()

    def get_favion_path(self, url: str) -> str:
        """
        Returns fav ico image (PNG) file path

        Args:
            url (str): The URL

        Returns:
            str: Full path to img (PNG) file
        """
        netloc = urlparse(url).netloc
        img = os.path.join(self.wf_cache_dir, f"{netloc}.png")
        if not (os.path.exists(img)):
            img = None
        if img and os.path.getsize(img) == 0:
            os.remove(img)
            img = None
        return img

    def _cache_favicon(self, netloc: str) -> None:
        """
        Download favicon from domain and save in wf cache directory

        Args:
            netloc (str): Network location e.g. http://www.google.com = www.google.com
        """
        if len(netloc) > 0:
            url = f"https://www.google.com/s2/favicons?domain={netloc}&sz=128"
            img = os.path.join(self.wf_cache_dir, f"{netloc}.png")
            os.path.exists(img) and self._cleanup_img_cache(60, img)
            if not (os.path.exists(img)):
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with open(img, "wb") as f:
                    try:
                        with urllib.request.urlopen(req) as r:
                            f.write(r.read())
                    except urllib.error.HTTPError as e:
                        os.path.exists(img) and os.remove(img)

    def _cache_controller(self) -> None:
        """
        Cache Controller to heat up cache and invalidation

        Args:
            histories (list): List with history entries
        """
        domains = [urlparse(i[0]).netloc for i in self.histories]
        pool = multiprocessing.Pool()
        pool.map(self._cache_favicon, domains)

    def _cleanup_img_cache(self, number_of_days: int, f_path: str) -> None:
        """
        Delete cached image after specific amount of days

        Args:
            number_of_days (int): Numer of days back in history
            f_path (str): path to file
        """
        now = time.time()
        old = now - number_of_days * 24 * 60 * 60
        stats = os.stat(f_path)
        c_time = stats.st_ctime
        if c_time < old and os.path.isfile(f_path):
            os.remove(f_path)
