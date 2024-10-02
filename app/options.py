from typing import AnyStr, Tuple, List
from urllib.parse import urljoin

from selenium.webdriver.chrome.options import Options


CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument("--headless")
CHROME_OPTIONS.add_argument("--disable-gpu")


class Urls:
    def __init__(self) -> None:
        self.BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
        self.HOME = self.BASE_URL
        self.COMPUTERS = self.get_url("computers")
        self.LAPTOPS = self.get_url("computers/laptops")
        self.TABLETS = self.get_url("computers/tablets")
        self.PHONES = self.get_url("phones")
        self.TOUCH = self.get_url("phones/touch")

    def get_url(self, url) -> AnyStr:
        return urljoin(self.BASE_URL, url)

    def attrs_for_map(self) -> List[str]:
        return [
            attr for attr in dir(self)
            if not callable(getattr(self, attr))
            and not attr.startswith("__")
            and attr != "BASE_URL"
        ]

    def all_urls(self) -> list[str]:
        return [
            getattr(self, attr) for attr in self.attrs_for_map()
        ]

    def get_mapped_urls_filenames(self) -> List[Tuple[str, str]]:
        return [
            (getattr(self, attr), attr.lower())
            for attr in self.attrs_for_map()
        ]


URLS = Urls()
