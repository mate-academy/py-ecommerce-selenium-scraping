from selenium import webdriver


class ChromeDriver:
    def __new__(cls) -> None:
        if not hasattr(cls, "instance"):
            cls.instance = super(ChromeDriver, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        self.web_driver = webdriver.Chrome()
