from selenium import webdriver
from selenium.common import NoSuchElementException
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
        try:
            btn_more = self.driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            while btn_more.is_displayed():
                self.driver.execute_script("arguments[0].click()", btn_more)

        except NoSuchElementException:
            pass

    def close(self) -> None:
        self.driver.close()

    def accept_cookie(self) -> None:
        try:
            self.driver.find_element(By.CLASS_NAME, "acceptCookies").click()
        except NoSuchElementException:
            pass

    def page_source(self) -> str:
        return self.driver.page_source
