from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from decouple import config


class ChromeDriver:
    _instance = None
    chrome_driver_path = config("CHROME_DRIVER_PATH")
    service = Service(chrome_driver_path)

    def __new__(cls) -> webdriver:
        if cls._instance is None:
            cls._instance = super(ChromeDriver, cls).__new__(cls)
            cls._instance.driver = webdriver.Chrome(service=cls.service)
        return cls._instance.driver

    def __enter__(self) -> webdriver:
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.driver.quit()
