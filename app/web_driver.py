from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


chrome_options = Options()
chrome_options.add_argument("--headless")


class WebDriverSingleton:
    _instance: Optional[webdriver.Chrome] = None

    @classmethod
    def get_instance(cls) -> webdriver.Chrome:
        if cls._instance is None:
            cls()
        return cls._instance

    def __init__(self) -> None:
        if WebDriverSingleton._instance is not None:
            raise Exception(
                "This class with a singleton!"
                "Use the get_instance() method to retrieve an instance."
            )
        else:
            WebDriverSingleton._instance = webdriver.Chrome(
                options=chrome_options
            )

    @classmethod
    def close(cls) -> None:
        if cls._instance is not None:
            cls._instance.quit()
            cls._instance = None
