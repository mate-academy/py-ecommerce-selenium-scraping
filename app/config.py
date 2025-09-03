from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class Settings:
    BASE_URL: str = "https://webscraper.io/"
    HOME_URL: str = urljoin(BASE_URL, "test-sites/e-commerce/more/")

    COMPUTERS_URL: str = urljoin(HOME_URL, "computers/")
    PHONES_URL: str = urljoin(HOME_URL, "phones/")

    LAPTOPS_URL: str = urljoin(COMPUTERS_URL, "laptops")
    TABLETS_URL: str = urljoin(COMPUTERS_URL, "tablets")

    TOUCH_URL: str = urljoin(PHONES_URL, "touch")


settings = Settings()


def get_settings() -> Settings:
    return settings
