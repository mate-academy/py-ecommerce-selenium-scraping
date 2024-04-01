from selenium import webdriver


class WebDriverSingleton:
    _instance = None

    def __init__(self, driver: webdriver.Chrome):
        if WebDriverSingleton._instance is not None:
            raise Exception("This class is singleton")
        WebDriverSingleton._instance = driver

    @staticmethod
    def get_driver() -> webdriver.Chrome:
        if WebDriverSingleton._instance is None:
            raise Exception("Create first webdriver")
        return WebDriverSingleton._instance
