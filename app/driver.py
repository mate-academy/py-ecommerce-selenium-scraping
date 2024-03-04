from selenium import webdriver


class ChromeDriver:
    driver = None

    def __new__(cls) -> webdriver:
        if not cls.driver:
            cls.driver = webdriver.Chrome()
        return cls.driver

    def __enter__(self) -> webdriver:
        return self.driver

    def __exit__(self) -> None:
        self.driver.close()
