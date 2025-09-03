from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.wait import WebDriverWait

from app.get_driver import get_driver
from app.utils.logger import logger


def accept_cookies() -> None:
    driver = get_driver()
    try:
        cookies_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        cookies_btn.click()
        logger.info("Cookies accepted")
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located(
                (
                    By.CLASS_NAME,
                    "acceptCookies",
                )
            )
        )
    except TimeoutException as e:
        logger.error(f"Error: {e}")
