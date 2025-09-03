from selenium.common import (
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By

from app.get_driver import get_driver
from app.utils.logger import logger


def click_more_buttons() -> None:
    driver = get_driver()
    while True:
        try:
            button = driver.find_element(
                By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"
            )
            button.click()
        except ElementNotInteractableException:
            logger.info("Full Page Loaded")
            break
        except NoSuchElementException:
            logger.info("Button not found - loading completed")
            break
        except TimeoutException as e:
            logger.error(f"Error: {e}")
            break
