import logging
from typing import Optional

from selenium.webdriver.chrome.webdriver import WebDriver

from app.logging_config import setup_logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions


setup_logging()


class WebDriverConfig:
    def __init__(
            self,
            browser: str = "chrome",
            headless: bool = False,
            driver_path: Optional[str] = None
    ) -> None:
        self.browser = browser.lower()
        self.headless = headless
        self.driver_path = driver_path
        self.driver = None

    def _setup_chrome_driver(self) -> WebDriver:
        options = ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        if self.driver_path:
            service = ChromeService(self.driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)

        self.driver.implicitly_wait(3)
        logging.info("WebDriver for Chrome set and ran.")
        return self.driver

    def set_driver(self) -> WebDriver | None:
        if self.browser == "chrome":
            return self._setup_chrome_driver()
        else:
            logging.error(
                f"Browser {self.browser} needs additional setup. "
                "Call your developer."
            )
            return None

    def quit_driver(self) -> None:
        if self.driver:
            self.driver.quit()
            logging.info(f"WebDriver for {self.browser} closed")
        else:
            logging.warning("WebDriver not initialized!")
