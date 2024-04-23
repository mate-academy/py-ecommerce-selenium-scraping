import time

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


def accept_cookies(driver: WebElement) -> None:
    try:
        accept_cookies_button = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        accept_cookies_button.click()
    except NoSuchElementException:
        return


def scroll_page(driver: WebElement) -> None:
    while True:
        try:
            scroll_button = driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
            if scroll_button.is_displayed():
                scroll_button.click()
                time.sleep(1)
            else:
                break
        except NoSuchElementException:
            break


def has_scroll_button(driver: WebElement) -> None:
    try:
        scroll_page(driver)
        time.sleep(1)
    except NoSuchElementException:
        return
