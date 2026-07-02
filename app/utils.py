from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import TimeoutException


def close_cookies_banner(driver: WebDriver) -> None:
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-tid='banner-accept']")
            )
        )
        accept_button.click()
    except TimeoutException:
        pass


def click_show_more_until_gone(driver: WebDriver) -> None:
    while True:
        try:
            products_before = len(
                driver.find_elements(By.CSS_SELECTOR, ".card-body")
            )

            more_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )

            driver.execute_script("arguments[0].click();", more_button)

            WebDriverWait(driver, 5).until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, ".card-body")
                ) > products_before
            )

        except TimeoutException:
            break
