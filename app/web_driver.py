from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)
from selenium.webdriver.common.by import By


_driver: WebDriver | None = None
_cookie_click_checker = 0


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def click_button_many_times(driver: WebDriver) -> None:
    while True:
        try:
            driver_btn = driver.find_element(By.CLASS_NAME, "btn")
            driver_btn.click()

        except NoSuchElementException:
            break

        except ElementClickInterceptedException:
            break

        except ElementNotInteractableException:
            break


def check_cookies(driver: WebDriver) -> None:
    global _cookie_click_checker

    if not _cookie_click_checker:
        cookie_banner = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookie_banner.click()
        _cookie_click_checker += 1
