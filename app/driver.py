from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver


class ChromeWebDriver:
    def __init__(self) -> None:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self._driver = webdriver.Chrome(options=chrome_options)

    def __enter__(self) -> WebDriver:
        return self._driver

    def __exit__(self,
                 exc_type: type,
                 exc_val: Exception,
                 exc_tb: type) -> None:
        self._driver.close()
