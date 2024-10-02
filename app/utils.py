from typing import List, Coroutine

from bs4 import BeautifulSoup
from httpx import AsyncClient
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


async def get_soup(
    client: AsyncClient,
    page: str
) -> BeautifulSoup:
    response = await client.get(url=page)
    page = response.text
    soup = BeautifulSoup(markup=page, features="html.parser")
    return soup


def get_tasks(
        client: AsyncClient,
        product_url_list: List[str]
) -> List[Coroutine]:
    tasks = [
        get_soup(client=client, page=url)
        for url in product_url_list
    ]
    return tasks


def get_more(driver: WebDriver) -> WebElement | None:
    try:
        return driver.find_element(
            By.CSS_SELECTOR,
            "a.ecomerce-items-scroll-more"
        )
    except NoSuchElementException:
        return None


def scroll_more(driver: WebDriver) -> None:
    more = get_more(driver)

    while more:
        try:
            more.click()
            more = get_more(driver)
        except (
            ElementNotInteractableException,
            ElementClickInterceptedException
        ):
            more = None


def accept_cookies(driver: WebDriver) -> None:
    cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
    try:
        cookies.click()
    except ElementNotInteractableException:
        pass
