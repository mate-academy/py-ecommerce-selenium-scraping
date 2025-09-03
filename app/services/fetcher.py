from bs4 import BeautifulSoup

from app.get_driver import get_driver
from app.services.skroller import click_more_buttons
from app.utils.logger import logger


def load_full_page(url: str) -> BeautifulSoup:
    logger.debug("Start Loading Page...")

    driver = get_driver()
    driver.get(url)
    logger.debug(driver.current_url)

    click_more_buttons()

    page_html = driver.page_source
    return BeautifulSoup(page_html, "html.parser")
