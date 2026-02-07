from selenium import webdriver
import atexit

from selenium.webdriver.chrome.webdriver import WebDriver


class WebDriverSingleton:
    _instance = None
    _driver = None

    def __new__(cls, browser: str = "chrome") -> "WebDriverSingleton":
        if cls._instance is None:
            cls._instance = super(WebDriverSingleton, cls).__new__(cls)
            cls._instance._initialize_driver(browser)
        return cls._instance

    def _initialize_driver(self, browser: str) -> None:
        if browser == "chrome":
            self._driver = webdriver.Chrome()
        elif browser == "firefox":
            self._driver = webdriver.Firefox()
        atexit.register(self.quit_driver)

    def get_driver(self) -> "WebDriver":
        """Returns the single instance of the WebDriver."""
        return self._driver

    def quit_driver(self) -> None:
        """Quits the driver and resets the instance."""
        if self._driver:
            self._driver.quit()
            self._driver = None
        WebDriverSingleton._instance = None
