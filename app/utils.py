from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


class CustomDriver:
    class __CustomDriver:
        def __init__(self) -> None:
            self.options = Options()
            self.options.add_argument("--headless")
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.options,
            )

    driver = None

    def __init__(self) -> None:
        if not self.driver:
            CustomDriver.driver = CustomDriver.__CustomDriver().driver

    def get(self, url: str) -> None:
        self.driver.get(url)
        self.accept_cookie()

    def click_more(self) -> None:
        btns_more = self.driver.find_elements(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        if btns_more:
            while btns_more[0].is_displayed():
                self.driver.execute_script(
                    "arguments[0].click()", btns_more[0]
                )

    def close(self) -> None:
        self.driver.close()

    def accept_cookie(self) -> None:
        buttons = self.driver.find_elements(By.CLASS_NAME, "acceptCookies")
        if buttons:
            buttons[0].click()

    def page_source(self) -> str:
        return self.driver.page_source
