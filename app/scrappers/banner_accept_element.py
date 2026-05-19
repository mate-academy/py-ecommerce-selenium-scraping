from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


def banner_accept_element(driver: WebDriver) -> None:
    try:
        banner_button = driver.find_element(
            By.CSS_SELECTOR, "button[data-tid='banner-accept']"
        )
        banner_button.click()
    except NoSuchElementException:
        pass
