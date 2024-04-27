from abc import ABC

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class DriverConfiguration(ABC):

    @staticmethod
    def create_driver(options: Options):
        pass


class ChromeDriverConfiguration(DriverConfiguration):

    @staticmethod
    def create_driver(options: Options):
        return webdriver.Chrome(options=options)


class WebDriverContextManager:
    def __init__(self, driver_creator, argument):
        self.options = Options()
        self.argument = argument
        self.driver_creator = driver_creator
        self.driver = None

    def __enter__(self):
        self.options.add_argument(self.argument)
        self.driver = self.driver_creator.create_driver(self.options)
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()
