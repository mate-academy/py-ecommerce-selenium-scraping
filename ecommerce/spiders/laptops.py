from typing import Any

import scrapy
from scrapy.http import Response
from selenium import webdriver

from helpers import (parse_single_product,
                     ajax_pagination,
                     parse_single_product_with_selenium)


class LaptopsSpider(scrapy.Spider):
    name = "laptops"
    allowed_domains = ["webscraper.io"]
    start_urls = [
        "https://webscraper.io/test-sites/e-commerce/more/computers/laptops"
    ]

    def __init__(self) -> None:
        super().__init__()
        self.driver = webdriver.Chrome()

    def close(self, reason: Any) -> None:
        self.driver.close()

    def parse(self, response: Response, **kwargs) -> None:
        if not response.css(".ecomerce-items-scroll-more"):
            for product in response.css(".thumbnail"):
                yield parse_single_product(product)
        else:
            products = ajax_pagination(response.url, self.driver)
            for product in products:
                yield parse_single_product_with_selenium(product)
