from types import TracebackType
from typing import Optional, Self, Type

from selenium import webdriver


class FirefoxDriver:
    def __enter__(self) -> Self:
        opts = webdriver.FirefoxOptions().add_argument("--headless")
        self.driver = webdriver.Firefox(options=opts)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.driver.close()
