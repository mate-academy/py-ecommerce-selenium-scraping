import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC # noqa 812
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.remote.webelement import WebElement


def accept_cookies(driver: WebElement) -> None:
    try:
        wait = WebDriverWait(driver, 10)
        accept_cookies_button = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        accept_cookies_button.click()
    except NoSuchElementException:
        return
    except TimeoutException:
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
