from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium.common import (
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.ie.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.wait import WebDriverWait

from app.config import get_settings
from app.get_driver import get_driver
from app.models import Product
from app.parsers.product_parser import parse_single_product
from app.services.fetcher import load_full_page
from app.utils.logger import logger

settings = get_settings()


def parse_default_product(driver: WebDriver) -> Product:
    soup = BeautifulSoup(driver.page_source, "html.parser")
    return parse_single_product(soup)


def parse_variants(driver: WebDriver) -> list[Product]:
    variants = []
    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")

        for i, button in enumerate(buttons[1:], start=2):
            if button.get_property("disabled"):
                continue

            clicked = False
            for attempt in range(2):
                try:
                    WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(button)
                    )
                    button.click()
                    clicked = True
                    break
                except (ElementClickInterceptedException, TimeoutException):
                    logger.warning(
                        f"Attempt {attempt + 1} failed "
                        f"for button #{i}, retrying..."
                    )

            if not clicked:
                logger.warning(f"Skipping button #{i} after 2 failed attempts")
                continue

            soup = BeautifulSoup(driver.page_source, "html.parser")
            variants.append(parse_single_product(soup))

    except NoSuchElementException:
        logger.info("No swatches found, skipping variants")

    return variants


def get_product_page(urls: list[str]) -> list[Product]:
    products = []
    driver = get_driver()

    for url in urls:
        driver.get(url)
        logger.debug(driver.current_url)
        products.append(parse_default_product(driver))
        products.extend(parse_variants(driver))

    return products


def get_links(page_soup: Tag) -> list[str]:
    logger.info("Getting links from page")
    references = page_soup.select("a.title")
    urls = [urljoin(settings.HOME_URL, link["href"]) for link in references]
    return urls


def get_products_from(url: str) -> list[Product]:
    page = load_full_page(url)
    return get_product_page(get_links(page))
