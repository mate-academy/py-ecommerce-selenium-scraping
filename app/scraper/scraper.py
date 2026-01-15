from urllib.parse import urljoin
from tqdm import tqdm
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from app.logger.logger import logging


class Scraper:
    def __init__(self, driver: webdriver, home_url: str) -> None:
        self.driver = driver
        self.home_url = home_url

    def get_products_from_root_url(self, url: str) -> list[dict]:
        """
        The main method gets the list of products by the given url,
        using other methods, returns a list of product dictionaries
        """
        logging.info("get_products_from_root_url  starting")
        cards = self.get_cards_from_page(url)
        products_data = []
        if cards:
            for card in tqdm(
                cards,
                total=len(cards),
                desc=f"scraping prices, ratings and reviews {url}",
                colour="green",
            ):
                product_data: dict = self.get_product_data_from_card(card)
                link_to_detail_page: str = self.get_link_to_product_page(card)
                product_data["link_to_detail_page"] = link_to_detail_page
                products_data.append(product_data)

        for product_data in tqdm(
            products_data,
            total=len(products_data),
            desc=f"scraping titles and descriptions {url}",
            colour="blue",
        ):
            rest_of_product_data: dict = self.get_title_and_description(
                product_data.pop("link_to_detail_page")
            )
            product_data.update(rest_of_product_data)
        return products_data

    @staticmethod
    def get_product_data_from_card(card: WebElement) -> dict:
        """
        :param card: WebElement
        :return: dict of product data - price, rating and num of reviews
        """
        product_data = dict()
        try:
            logging.info("Scraping price")
            product_data["price"] = float(
                card.find_element(By.CLASS_NAME, "price")
                .text.replace("$", "")
            )
        except NoSuchElementException:
            logging.exception(
                "Failed to get price on on page default value '0.0'")
            product_data["price"] = float(0)

        try:
            product_data["rating"] = len(
                card.find_elements(By.CLASS_NAME, "ws-icon-star"))
            logging.info(f"rating {product_data["rating"]}")
        except NoSuchElementException:
            logging.exception(
                "Failed to get rating default value '0'")
            product_data["rating"] = 0
        try:
            product_data["num_of_reviews"] = int(
                card.find_element(
                    By.CSS_SELECTOR, "span[itemprop='reviewCount']"
                ).text
            )
            logging.info(
                f"Number of reviews: {product_data["num_of_reviews"]}")
        except NoSuchElementException:
            logging.exception(
                "Failed to get reviews,, default value '0'")
            product_data["num_of_reviews"] = 0
        return product_data

    def get_cards_from_page(self, url: str) -> list[WebElement] | None:
        """
        getting product cards from a web page
        :param url: string url
        :return: list of WebElement
        """
        logging.info("get_cards_from_page   starting")
        logging.info(f"Getting cards from {url}")
        self.driver.get(url)
        self.accept_cookies()
        wait = WebDriverWait(self.driver, 5)

        while True:
            cards = self.driver.find_elements(By.CLASS_NAME, "product-wrapper")
            prev_count = len(cards)

            try:
                more_button = wait.until(
                    expected_conditions.element_to_be_clickable(
                        (By.CLASS_NAME, "ecomerce-items-scroll-more")
                    )
                )
                more_button.click()

                wait.until(
                    lambda d: any((
                        len(d.find_elements(By.CLASS_NAME,
                                            "product-wrapper")) > prev_count,
                        not more_button.is_displayed(),
                    ))
                )
            except (NoSuchElementException, TimeoutException):
                logging.info("No more products to load")
                break
        return cards

    def get_link_to_product_page(self, card: list[WebElement]) -> str | None:
        logging.info("Getting links to products links")
        try:
            link = card.find_element(By.TAG_NAME, "a")
            url = link.get_attribute("href")
            return urljoin(self.home_url, url)
        except NoSuchElementException as e:
            logging.warning(
                f"Failed to get links to products links, excepted {e}")
            return None

    def get_title_and_description(self, url: str) -> dict:
        self.driver.get(url)
        product_data = dict()

        try:
            product_data["title"] = self.driver.find_element(
                By.CLASS_NAME, "title"
            ).text
        except NoSuchElementException:
            logging.exception(
                f"Failed to get title on page {url}, default value ''")
            product_data["title"] = ""
        try:
            product_data["description"] = self.driver.find_element(
                By.CLASS_NAME, "description").text
        except NoSuchElementException:
            logging.exception(
                f"Failed to get description on page {url}, default value ''")
            product_data["description"] = ""
        return product_data

    def accept_cookies(self) -> None:
        try:
            button = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Accept')]"
            )
            if button.is_displayed():
                button.click()
        except NoSuchElementException:
            pass
