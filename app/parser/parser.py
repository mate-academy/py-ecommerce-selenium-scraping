import time

from bs4 import BeautifulSoup, Tag
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

from app.schemas import Product


class Parser:
    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver

    def _accept_cookies(self) -> None:
        try:
            cookies = self.driver.find_elements(By.ID, "cookieBanner")
            if cookies:
                try:
                    accept = self.driver.find_element(By.CLASS_NAME, "acceptCookies")
                    accept.click()
                except WebDriverException:
                    pass
        except WebDriverException:
            pass

    def _click_more_until_end(self) -> None:
        try:
            while True:
                time.sleep(1)
                more_button = self.driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
                try:
                    more_button.click()
                except WebDriverException:
                    break
        except WebDriverException:
            return

    def get_full_page(self, page_url: str) -> str:
        self.driver.get(page_url)
        self._accept_cookies()
        self._click_more_until_end()
        time.sleep(1)
        return self.driver.page_source

    def _parse_product(self, product: Tag) -> Product:
        price_el = product.select_one(".price")
        if not price_el:
            price_el = product.select_one("span[itemprop='price']")

        stars = product.select(".ws-icon-star")
        if stars:
            rating = len(stars)
        else:
            rating_el = product.select_one("p[data-rating]")
            rating = int(rating_el.get("data-rating")) if rating_el and rating_el.has_attr("data-rating") else 0

        num_of_reviews_el = product.select_one("span[itemprop='reviewCount']")

        title_el = product.select_one(".title")
        desc_el = product.select_one(".description")

        title = title_el.get("title") if title_el and title_el.has_attr("title") else ""
        description = desc_el.get_text(" ", strip=True).replace("\xa0", " ") if desc_el else ""
        price = float(price_el.get_text(strip=True).lstrip("$")) if price_el else 0.0
        num_of_reviews = int(num_of_reviews_el.get_text()) if num_of_reviews_el else 0

        return Product(
            title=title,
            description=description,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews,
        )

    def parse_page(self, page_url: str) -> list[Product]:
        html = self.get_full_page(page_url)
        soup = BeautifulSoup(html, "html.parser")
        products: list[Product] = []
        for product_soup in soup.select("div.product-wrapper"):
            try:
                products.append(self._parse_product(product_soup))
            except Exception:
                continue

        return products

