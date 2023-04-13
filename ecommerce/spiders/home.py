import scrapy
from scrapy.http import Response

from app.parse import Product
from helpers import parse_single_product


class HomeSpider(scrapy.Spider):
    name = "home"
    allowed_domains = ["webscraper.io"]
    start_urls = ["https://webscraper.io/test-sites/e-commerce/more"]

    def parse(self, response: Response, **kwargs) -> Product:
        for product in response.css(".thumbnail"):
            yield parse_single_product(product)
